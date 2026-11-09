# Session Persistence & Checkpoint Recovery

**Document**: Session Persistence Architecture
**Version**: 1.0
**Status**: Design Phase

## Overview

Session persistence ensures users can recover their workspace even if:
- Provider connection drops
- Provider crashes or goes down
- User internet disconnects
- Browser crashes
- GPU session times out
- User manually pauses/resumes

This is a **critical differentiator** separating Cloud OS from ephemeral services like Colab.

## Session State Model

### What Gets Persisted

```python
@dataclass
class SessionState:
    """Complete session state"""
    
    # Environment
    workspace_id: str
    session_id: str
    environment_variables: Dict[str, str]
    installed_packages: List[str]
    
    # File System
    working_directory: str
    file_tree: Dict[str, Any]  # Complete directory structure
    important_files: Dict[str, bytes]  # Key files by path
    
    # IDE State
    open_files: List[str]
    cursor_positions: Dict[str, Tuple[int, int]]  # Line, col
    breakpoints: List[str]
    
    # Terminal State
    terminal_history: List[str]
    current_working_dir: str
    
    # Notebook State
    notebook_kernels: Dict[str, KernelState]
    executed_cells: Dict[str, Any]
    cell_outputs: Dict[str, Any]
    
    # Workflow State
    active_workflows: List[str]
    workflow_results: Dict[str, Any]
    
    # Training State
    model_checkpoints: List[str]
    training_logs: List[str]
    loss_history: List[float]
```

## Auto-Checkpoint Strategy

### Checkpoint Levels

**Level 1: Continuous Sync** (Real-time)
- IDE file edits → immediately synced to S3
- Terminal history → streamed to storage
- Kernel state → streamed periodically

**Level 2: Periodic Snapshots** (Every 5 minutes)
- Complete filesystem snapshot
- Environment state
- Open file states
- Memory snapshots

**Level 3: Critical Points** (Manual)
- User clicks "Save Checkpoint"
- Training reaches milestone
- Before high-risk operation
- Before provider switch

### Implementation

```python
# services/checkpoint_service.py
class CheckpointService:
    """Manages session checkpoints"""
    
    async def start_auto_checkpoint_loop(self, session_id: str):
        """Continuous checkpointing"""
        
        while True:
            try:
                # Create checkpoint every 5 minutes
                await self.create_checkpoint(
                    session_id,
                    checkpoint_type='auto',
                    name=f'auto-{datetime.utcnow().isoformat()}'
                )
                
                # Clean old checkpoints (keep last 20)
                await self.cleanup_old_checkpoints(session_id, keep=20)
                
                await asyncio.sleep(300)  # 5 minutes
                
            except Exception as e:
                logger.error(f"Checkpoint failed for {session_id}: {e}")
                await asyncio.sleep(60)  # Retry after 1 min
    
    async def create_checkpoint(
        self,
        session_id: str,
        checkpoint_type: str = 'auto',
        name: Optional[str] = None
    ) -> Checkpoint:
        """Create session checkpoint"""
        
        session = await db.get_session(session_id)
        provider = provider_manager.get_provider(session.provider)
        
        logger.info(f"Creating {checkpoint_type} checkpoint for session {session_id}")
        
        # 1. Collect session state
        state = await self._collect_session_state(session)
        
        # 2. Compress state
        state_json = json.dumps(state, default=str)
        state_compressed = gzip.compress(state_json.encode())
        
        # 3. Upload to S3
        checkpoint_path = f"checkpoints/{session_id}/{uuid.uuid4()}.tar.gz"
        
        async with self.s3_client.upload_fileobj(
            BytesIO(state_compressed),
            bucket=CHECKPOINT_BUCKET,
            key=checkpoint_path
        ) as resp:
            file_size = len(state_compressed)
        
        # 4. Save checkpoint record
        checkpoint = Checkpoint(
            id=str(uuid.uuid4()),
            session_id=session_id,
            checkpoint_type=checkpoint_type,
            name=name or f"checkpoint-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            storage_path=checkpoint_path,
            file_size_bytes=file_size,
            status='completed',
            created_at=datetime.utcnow()
        )
        
        db.session.add(checkpoint)
        await db.session.commit()
        
        logger.info(f"Checkpoint {checkpoint.id} created, size: {file_size} bytes")
        
        return checkpoint
    
    async def _collect_session_state(self, session: WorkspaceSession) -> SessionState:
        """Collect complete session state"""
        
        provider = provider_manager.get_provider(session.provider)
        
        # Get filesystem snapshot
        files = await provider.execute_command(
            session.provider_session_id,
            "find /home/user -type f -mmin -5"  # Files modified in last 5 min
        )
        
        # Get environment
        env_vars = await provider.execute_command(
            session.provider_session_id,
            "env"
        )
        
        # Get pip packages
        packages = await provider.execute_command(
            session.provider_session_id,
            "pip list --format json"
        )
        
        # Get IDE state from code-server
        ide_state = await self._get_ide_state(session)
        
        # Get terminal history
        terminal_history = await provider.execute_command(
            session.provider_session_id,
            "cat ~/.bash_history | tail -100"
        )
        
        return SessionState(
            workspace_id=session.workspace_id,
            session_id=session.id,
            environment_variables=parse_env(env_vars),
            installed_packages=json.loads(packages),
            file_tree=await self._build_file_tree(session),
            important_files=await self._collect_important_files(session),
            terminal_history=terminal_history.split('\n'),
            # ... other fields
        )
    
    async def restore_session(
        self,
        checkpoint_id: str,
        new_session: WorkspaceSession
    ):
        """Restore session from checkpoint"""
        
        checkpoint = await db.get_checkpoint(checkpoint_id)
        provider = provider_manager.get_provider(new_session.provider)
        
        logger.info(f"Restoring session from checkpoint {checkpoint_id}")
        
        # 1. Download checkpoint from S3
        checkpoint_data = await self.s3_client.get_object(
            Bucket=CHECKPOINT_BUCKET,
            Key=checkpoint.storage_path
        )
        
        state_compressed = checkpoint_data['Body'].read()
        state_json = gzip.decompress(state_compressed).decode()
        state = json.loads(state_json)
        
        # 2. Restore environment variables
        env_commands = [
            f"export {k}={v}" for k, v in state['environment_variables'].items()
        ]
        await provider.execute_script(
            new_session.provider_session_id,
            "\n".join(env_commands)
        )
        
        # 3. Restore pip packages
        await provider.execute_command(
            new_session.provider_session_id,
            f"pip install {' '.join(state['installed_packages'])}"
        )
        
        # 4. Restore files
        for file_path, content in state['important_files'].items():
            await provider.upload_file(
                new_session.provider_session_id,
                BytesIO(content),
                file_path
            )
        
        # 5. Restore IDE state
        await self._restore_ide_state(new_session, state['ide_state'])
        
        # 6. Restore terminal history
        await provider.execute_command(
            new_session.provider_session_id,
            f"cat > ~/.bash_history << 'EOF'\n{chr(10).join(state['terminal_history'])}\nEOF"
        )
        
        logger.info(f"Session restored successfully")
```

## Recovery Flow

### Automatic Recovery (Transparent to User)

```
User in IDE
    ↓
Provider connection drops
    ↓
Health check detects failure (5-30 second delay)
    ↓
Session Manager triggers recovery
    ↓
Loads latest checkpoint
    ↓
Selects alternate provider
    ↓
Provisions new session
    ↓
Restores checkpoint
    ↓
Reroutes user session
    ↓
Frontend shows "Reconnecting..." briefly
    ↓
User continues working (IDE opens new tab)
```

### Code Flow

```python
# Backend
async def health_check_loop(session_id: str):
    """Periodic health check"""
    while True:
        try:
            session = await db.get_session(session_id)
            provider = provider_manager.get_provider(session.provider)
            
            # Ping session
            metrics = await provider.get_session_metrics(
                session.provider_session_id,
                timeout=10
            )
            
            session.last_heartbeat_at = datetime.utcnow()
            session.status = 'healthy'
            await db.save(session)
            
        except asyncio.TimeoutError:
            # Provider not responding
            logger.warning(f"Session {session_id} health check timeout")
            
            # Mark as unhealthy
            session.status = 'unhealthy'
            await db.save(session)
            
            # Trigger recovery if unhealthy for >60 seconds
            if (datetime.utcnow() - session.last_heartbeat_at).seconds > 60:
                await handle_session_failure(session_id)
        
        except Exception as e:
            logger.error(f"Health check error: {e}")
        
        finally:
            await asyncio.sleep(30)  # Check every 30 seconds

# Frontend
useEffect(() => {
    const checkHealth = setInterval(async () => {
        try {
            await api.get(`/api/v1/sessions/${sessionId}/health`);
            setIsConnected(true);
        } catch (err) {
            setIsConnected(false);
            showNotification("Connection lost, attempting recovery...");
            
            // Implement exponential backoff
            let retries = 0;
            while (!isConnected && retries < 10) {
                await new Promise(r => setTimeout(r, 1000 * Math.pow(2, retries)));
                try {
                    await api.get(`/api/v1/sessions/${sessionId}/health`);
                    setIsConnected(true);
                    showNotification("Connection restored!");
                } catch {}
                retries++;
            }
        }
    }, 30000);  // Check every 30 seconds
    
    return () => clearInterval(checkHealth);
}, [sessionId]);
```

## Storage Architecture

### Checkpoint Storage Layout

```
s3://cloud-os-checkpoints/
├── user123/
│   ├── workspace-abc/
│   │   ├── session-1/
│   │   │   ├── checkpoint-001.tar.gz
│   │   │   ├── checkpoint-002.tar.gz
│   │   │   └── checkpoint-003.tar.gz
│   │   └── session-2/
│   │       ├── checkpoint-001.tar.gz
│   │       └── checkpoint-002.tar.gz
│   └── workspace-def/
│       └── session-1/
│           ├── checkpoint-001.tar.gz
│           └── checkpoint-002.tar.gz
```

### Lifecycle & Cleanup

```python
async def cleanup_old_checkpoints(
    session_id: str,
    keep: int = 20,
    retention_days: int = 30
):
    """Clean old/expired checkpoints"""
    
    checkpoints = await db.query(Checkpoint).filter(
        Checkpoint.session_id == session_id
    ).order_by(Checkpoint.created_at.desc()).all()
    
    # Keep recent checkpoints
    for checkpoint in checkpoints[keep:]:
        # Also clean those older than 30 days
        age_days = (datetime.utcnow() - checkpoint.created_at).days
        
        if age_days > retention_days:
            # Delete from S3
            await s3_client.delete_object(
                Bucket=CHECKPOINT_BUCKET,
                Key=checkpoint.storage_path
            )
            
            # Delete from DB
            await db.delete(checkpoint)
            
            logger.info(f"Cleaned checkpoint {checkpoint.id}")
```

## Metrics & Monitoring

```python
@app.get("/api/v1/sessions/{session_id}/checkpoint-status")
async def get_checkpoint_status(session_id: str):
    """Get checkpoint status"""
    
    session = await db.get_session(session_id)
    latest_checkpoint = await db.query(Checkpoint).filter(
        Checkpoint.session_id == session_id
    ).order_by(Checkpoint.created_at.desc()).first()
    
    return {
        'session_id': session_id,
        'checkpoint_enabled': session.workspace.auto_checkpoint_enabled,
        'latest_checkpoint': {
            'id': latest_checkpoint.id,
            'created_at': latest_checkpoint.created_at,
            'size_mb': latest_checkpoint.file_size_bytes / 1024 / 1024,
            'age_minutes': (datetime.utcnow() - latest_checkpoint.created_at).total_seconds() / 60
        },
        'checkpoint_count': await db.count(
            Checkpoint.query.filter(Checkpoint.session_id == session_id)
        ),
        'total_checkpoint_size_gb': sum(
            c.file_size_bytes for c in checkpoints
        ) / 1024 / 1024 / 1024,
        'recovery_capability': 'full' if latest_checkpoint else 'none'
    }
```

## Best Practices

1. **Checkpoint Frequently**: Every 5 minutes for critical work
2. **Test Recovery**: Regularly test recovery workflows
3. **Monitor Checkpoint Size**: Alert if >5GB
4. **Backup Checkpoints**: Replicate to secondary S3 bucket
5. **Document Restore Process**: Clear instructions for users

## Next Steps

- Review [Security Architecture](SECURITY_ARCHITECTURE.md)
- See [Backend Architecture](../architecture/02-BACKEND_ARCHITECTURE.md)
