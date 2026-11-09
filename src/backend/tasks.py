"""
Celery task definitions for Cloud OS Backend
"""
from celery import Celery, shared_task
from config import settings
from auth.db import get_db_session
from models import WorkspaceSession, Workspace, Checkpoint, Metrics
from websocket.manager import manager, EventType, WebSocketEvent
from provider_sdk import provider_manager, provider_registry
from datetime import datetime, timedelta
import logging
import asyncio
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Initialize Celery app
celery_app = Celery(
    'cloud_os',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=['tasks']
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)


# ==============================================================================
# Session Management Tasks
# ==============================================================================

@shared_task(bind=True, max_retries=3)
def provision_gpu_session(self, workspace_id: str, session_id: str, provider: str, config: dict):
    """Provision a GPU session"""
    try:
        db = next(get_db_session())
        
        # Get session from database
        session = db.query(WorkspaceSession).filter(
            WorkspaceSession.id == session_id
        ).first()
        
        if not session:
            logger.error(f"Session {session_id} not found")
            return {"error": "Session not found", "session_id": session_id}
        
        logger.info(f"Provisioning GPU session {session_id} on {provider}")
        
        # Get provider
        prov = provider_registry.get_provider(provider)
        if not prov:
            raise Exception(f"Provider {provider} not available")
        
        # Get GPU
        gpu_model = config.get("gpu_type", "RTX 4090")
        gpus = asyncio.run(prov.get_available_gpus({"model": gpu_model}))
        
        if not gpus:
            raise Exception(f"No {gpu_model} GPUs available")
        
        # Provision session
        gpu = gpus[0]
        compute_session = asyncio.run(prov.provision_session(
            gpu=gpu,
            image=config.get("image", "ubuntu:22.04"),
            env=config.get("env", {}),
            timeout_minutes=config.get("timeout_hours", 1) * 60,
        ))
        
        # Update database
        session.status = "running"
        session.provider_session_id = compute_session.id
        session.started_at = datetime.utcnow()
        session.gpu_type = gpu.model
        session.memory_gb = gpu.vram_gb
        session.session_config = {
            **config,
            "ssh_host": compute_session.ssh_host,
            "ssh_port": compute_session.ssh_port,
            "ide_url": compute_session.ide_url,
        }
        db.commit()
        
        # Broadcast event
        event = WebSocketEvent(
            event_type=EventType.SESSION_STARTED,
            data={
                "session_id": session_id,
                "provider": provider,
                "gpu_type": gpu.model,
                "ssh_host": compute_session.ssh_host,
            },
            workspace_id=workspace_id,
        )
        
        asyncio.run(manager.broadcast_to_workspace(workspace_id, event))
        
        logger.info(f"Session {session_id} provisioned successfully")
        return {"status": "success", "session_id": session_id}
    
    except Exception as e:
        logger.error(f"Session provisioning failed: {e}")
        
        # Retry after 10 seconds
        retry_count = self.request.retries
        if retry_count < 3:
            raise self.retry(exc=e, countdown=10)
        
        # Update session to error state
        try:
            db = next(get_db_session())
            session = db.query(WorkspaceSession).filter(
                WorkspaceSession.id == session_id
            ).first()
            if session:
                session.status = "error"
                db.commit()
        except:
            pass
        
        return {"error": str(e), "session_id": session_id}


@shared_task
def monitor_session_metrics(session_id: str):
    """Monitor session metrics every 30 seconds"""
    try:
        db = next(get_db_session())
        
        session = db.query(WorkspaceSession).filter(
            WorkspaceSession.id == session_id
        ).first()
        
        if not session or session.status != "running":
            return
        
        # Get provider
        prov = provider_registry.get_provider(session.provider)
        if not prov:
            logger.error(f"Provider {session.provider} not available")
            return
        
        # Get metrics
        metrics = asyncio.run(prov.get_session_metrics(session.provider_session_id))
        
        # Store metrics
        metric_record = Metrics(
            session_id=session_id,
            gpu_utilization=metrics.gpu_utilization,
            gpu_memory_used_gb=metrics.gpu_memory_used_gb,
            gpu_temperature=metrics.gpu_temperature,
            gpu_power_w=metrics.gpu_power_w,
            cpu_utilization=metrics.cpu_utilization,
            system_memory_used_gb=metrics.system_memory_used_gb,
            created_at=datetime.utcnow(),
        )
        
        db.add(metric_record)
        db.commit()
        
        # Broadcast metrics
        event = WebSocketEvent(
            event_type=EventType.SESSION_METRICS,
            data={
                "session_id": session_id,
                "gpu_utilization": metrics.gpu_utilization,
                "gpu_memory_used_gb": metrics.gpu_memory_used_gb,
                "gpu_temperature": metrics.gpu_temperature,
                "gpu_power_w": metrics.gpu_power_w,
                "cpu_utilization": metrics.cpu_utilization,
            },
            workspace_id=session.workspace_id,
        )
        
        asyncio.run(manager.broadcast_to_workspace(session.workspace_id, event))
        
    except Exception as e:
        logger.error(f"Failed to monitor metrics for {session_id}: {e}")


@shared_task
def create_checkpoint(session_id: str, checkpoint_name: str = None):
    """Create a checkpoint for a session"""
    try:
        db = next(get_db_session())
        
        session = db.query(WorkspaceSession).filter(
            WorkspaceSession.id == session_id
        ).first()
        
        if not session:
            logger.error(f"Session {session_id} not found")
            return
        
        # Get provider
        prov = provider_registry.get_provider(session.provider)
        if not prov:
            raise Exception(f"Provider {session.provider} not available")
        
        # Create checkpoint
        checkpoint_name = checkpoint_name or f"checkpoint-{datetime.utcnow().isoformat()}"
        checkpoint_data = asyncio.run(prov.create_checkpoint(
            session.provider_session_id,
            checkpoint_name
        ))
        
        # Store checkpoint in database
        checkpoint = Checkpoint(
            session_id=session_id,
            name=checkpoint_name,
            storage_path=checkpoint_data.get("storage_path"),
            checkpoint_id=checkpoint_data.get("checkpoint_id"),
            created_at=datetime.utcnow(),
        )
        
        db.add(checkpoint)
        db.commit()
        
        logger.info(f"Checkpoint {checkpoint_name} created for session {session_id}")
        return {"status": "success", "checkpoint_id": checkpoint_data.get("checkpoint_id")}
    
    except Exception as e:
        logger.error(f"Failed to create checkpoint for {session_id}: {e}")
        return {"error": str(e)}


@shared_task
def restore_checkpoint(session_id: str, checkpoint_id: str):
    """Restore a session from checkpoint"""
    try:
        db = next(get_db_session())
        
        checkpoint = db.query(Checkpoint).filter(
            Checkpoint.checkpoint_id == checkpoint_id
        ).first()
        
        if not checkpoint:
            logger.error(f"Checkpoint {checkpoint_id} not found")
            return
        
        session = db.query(WorkspaceSession).filter(
            WorkspaceSession.id == session_id
        ).first()
        
        if not session:
            logger.error(f"Session {session_id} not found")
            return
        
        # Get provider
        prov = provider_registry.get_provider(session.provider)
        if not prov:
            raise Exception(f"Provider {session.provider} not available")
        
        # Restore from checkpoint
        restored_session = asyncio.run(prov.restore_session(checkpoint_id))
        
        # Update session
        session.status = "running"
        session.provider_session_id = restored_session.id
        session.started_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Session {session_id} restored from checkpoint")
        return {"status": "success", "session_id": session_id}
    
    except Exception as e:
        logger.error(f"Failed to restore checkpoint: {e}")
        return {"error": str(e)}


@shared_task
def terminate_session(session_id: str):
    """Terminate a GPU session"""
    try:
        db = next(get_db_session())
        
        session = db.query(WorkspaceSession).filter(
            WorkspaceSession.id == session_id
        ).first()
        
        if not session:
            logger.error(f"Session {session_id} not found")
            return
        
        # Get provider
        prov = provider_registry.get_provider(session.provider)
        if not prov:
            logger.error(f"Provider {session.provider} not available")
            return
        
        # Terminate session
        asyncio.run(prov.terminate_session(session.provider_session_id))
        
        # Update database
        session.status = "stopped"
        session.terminated_at = datetime.utcnow()
        db.commit()
        
        # Broadcast event
        event = WebSocketEvent(
            event_type=EventType.SESSION_STOPPED,
            data={"session_id": session_id},
            workspace_id=session.workspace_id,
        )
        
        asyncio.run(manager.broadcast_to_workspace(session.workspace_id, event))
        
        logger.info(f"Session {session_id} terminated")
        return {"status": "success"}
    
    except Exception as e:
        logger.error(f"Failed to terminate session {session_id}: {e}")
        return {"error": str(e)}


# ==============================================================================
# Workflow Execution Tasks
# ==============================================================================

@shared_task
def execute_workflow(workflow_id: str, run_id: str):
    """Execute a workflow DAG"""
    try:
        logger.info(f"Executing workflow {workflow_id} (run: {run_id})")
        
        # This would be implemented with the workflow engine
        # For now, mark as started
        
        return {"status": "started", "run_id": run_id}
    
    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        return {"error": str(e)}


@shared_task
def execute_workflow_node(run_id: str, node_id: str, inputs: dict):
    """Execute a single workflow node"""
    try:
        logger.info(f"Executing workflow node {node_id} in run {run_id}")
        
        # This would execute the node logic
        # For now, return mock result
        
        return {"status": "completed", "node_id": node_id, "output": {}}
    
    except Exception as e:
        logger.error(f"Node execution failed: {e}")
        return {"error": str(e)}


@shared_task
def collect_workflow_results(run_id: str):
    """Collect results from completed workflow"""
    try:
        logger.info(f"Collecting results for workflow run {run_id}")
        
        # Aggregate results from all nodes
        
        return {"status": "completed", "run_id": run_id}
    
    except Exception as e:
        logger.error(f"Failed to collect results: {e}")
        return {"error": str(e)}


# ==============================================================================
# AI Assistant Tasks
# ==============================================================================

@shared_task
def process_ai_request(session_id: str, prompt: str, context: dict):
    """Process AI assistant request"""
    try:
        logger.info(f"Processing AI request for session {session_id}")
        
        # This would integrate with an LLM API
        # For now, return mock response
        
        response = f"AI response to: {prompt}"
        
        return {"status": "completed", "response": response}
    
    except Exception as e:
        logger.error(f"AI processing failed: {e}")
        return {"error": str(e)}


# ==============================================================================
# Maintenance Tasks
# ==============================================================================

@shared_task
def cleanup_expired_checkpoints():
    """Clean up expired checkpoints"""
    try:
        logger.info("Cleaning up expired checkpoints")
        
        db = next(get_db_session())
        
        # Find checkpoints older than 30 days
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        expired = db.query(Checkpoint).filter(
            Checkpoint.created_at < cutoff_date
        ).all()
        
        deleted_count = 0
        for checkpoint in expired:
            try:
                # Delete from provider storage
                session = db.query(WorkspaceSession).filter(
                    WorkspaceSession.id == checkpoint.session_id
                ).first()
                
                if session:
                    prov = provider_registry.get_provider(session.provider)
                    if prov:
                        asyncio.run(prov.delete_checkpoint(checkpoint.checkpoint_id))
                
                # Delete from database
                db.delete(checkpoint)
                deleted_count += 1
            
            except Exception as e:
                logger.error(f"Failed to delete checkpoint {checkpoint.id}: {e}")
        
        db.commit()
        
        logger.info(f"Cleaned up {deleted_count} expired checkpoints")
        return {"status": "completed", "deleted": deleted_count}
    
    except Exception as e:
        logger.error(f"Checkpoint cleanup failed: {e}")
        return {"error": str(e)}


@shared_task
def collect_system_metrics():
    """Collect system-wide metrics"""
    try:
        logger.info("Collecting system metrics")
        
        db = next(get_db_session())
        
        # Get active sessions
        active_sessions = db.query(WorkspaceSession).filter(
            WorkspaceSession.status == "running"
        ).all()
        
        # Collect metrics from each
        for session in active_sessions:
            try:
                # Schedule individual metric collection
                monitor_session_metrics.delay(session.id)
            except Exception as e:
                logger.error(f"Failed to collect metrics for {session.id}: {e}")
        
        return {"status": "completed", "sessions_monitored": len(active_sessions)}
    
    except Exception as e:
        logger.error(f"System metrics collection failed: {e}")
        return {"error": str(e)}


@shared_task
def sync_provider_status():
    """Sync status of GPU providers"""
    try:
        logger.info("Syncing provider status")
        
        # Health check all providers
        health_results = asyncio.run(provider_manager.health_check_all())
        
        # Log results
        for provider_name, is_healthy in health_results.items():
            status = "✓" if is_healthy else "✗"
            logger.info(f"Provider {provider_name}: {status}")
        
        # Get usage stats
        usage_stats = asyncio.run(provider_manager.get_usage_stats_all())
        logger.info(f"Provider usage stats: {usage_stats}")
        
        return {"status": "completed", "health": health_results}
    
    except Exception as e:
        logger.error(f"Provider sync failed: {e}")
        return {"error": str(e)}


# ==============================================================================
# Celery Beat Schedule (periodic tasks)
# ==============================================================================

from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    'cleanup-checkpoints': {
        'task': 'tasks.cleanup_expired_checkpoints',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
        'options': {'queue': 'maintenance'},
    },
    'collect-metrics': {
        'task': 'tasks.collect_system_metrics',
        'schedule': 30,  # Every 30 seconds
        'options': {'queue': 'metrics'},
    },
    'sync-providers': {
        'task': 'tasks.sync_provider_status',
        'schedule': 300,  # Every 5 minutes
        'options': {'queue': 'maintenance'},
    },
}
