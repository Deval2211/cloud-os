# Cloud OS - Bugs & Code Issues Reference

**Document**: Specific bugs, issues, and incomplete code locations  
**Last Updated**: 2026-05-30

---

## CRITICAL BUGS 🔴

### Bug #1: Session Creation Field Mismatch

**Location**: [src/backend/routes/sessions.py](src/backend/routes/sessions.py#L39)  
**Severity**: CRITICAL - Causes runtime error  
**Status**: ❌ NOT FIXED

**Issue**:
```python
# Line 39 in sessions.py - WRONG FIELD NAME
session = SessionService.create_session(
    db=db,
    workspace_id=workspace_id,
    user_id=current_user.id,
    provider=session_create.provider,
    provider_session_id=f"{session_create.provider}-{uuid.uuid4().hex[:8]}",
    config={...},
    created_by=user_id,  # ❌ FIELD DOESN'T EXIST!
)
```

**Problem**: The `WorkspaceSession` model doesn't have a `created_by` field. It uses `user_id`.

**Model Definition** [src/backend/models.py](src/backend/models.py#L81):
```python
class WorkspaceSession(Base):
    __tablename__ = "workspace_sessions"
    ...
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)  # ✅ Correct field
    # NO created_by field
```

**Fix**:
```python
# Should be:
session = SessionService.create_session(
    db=db,
    workspace_id=workspace_id,
    user_id=current_user.id,  # ✅ Use this
    provider=session_create.provider,
    provider_session_id=f"{session_create.provider}-{uuid.uuid4().hex[:8]}",
    config={...},
    # Remove created_by parameter
)
```

**Impact**: Every attempt to create a session will fail with `TypeError: unexpected keyword argument 'created_by'`

---

### Bug #2: Incomplete Stop Session Endpoint

**Location**: [src/backend/routes/sessions.py](src/backend/routes/sessions.py#L299)  
**Severity**: CRITICAL - Endpoint not functional  
**Status**: ❌ NOT IMPLEMENTED

**Issue**: The endpoint definition starts but the body is missing:

```python
# Line 299 - INCOMPLETE
@router.post("/workspaces/{workspace_id}/sessions/{session_id}/stop")
# ❌ NO FUNCTION BODY! File ends here or continues with incomplete code
```

**Expected Implementation**:
```python
@router.post("/workspaces/{workspace_id}/sessions/{session_id}/stop")
async def stop_session(
    workspace_id: str,
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """Stop a GPU session"""
    # Verify workspace
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.owner_id == current_user.id,
    ).first()
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Get session
    session = SessionService.get_session(db, session_id)
    if not session or session.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Terminate session
    terminated_session = SessionService.terminate_session(db, session)
    
    # Broadcast event
    event = WebSocketEvent(
        event_type=EventType.SESSION_STOPPED,
        data={"session_id": session.id},
        user_id=current_user.id,
        workspace_id=workspace_id,
    )
    
    await manager.broadcast_to_workspace(workspace_id, event)
    
    return SessionResponse.from_orm(terminated_session)
```

**Impact**: Users cannot stop their GPU sessions - they'll run indefinitely and incur costs

---

### Bug #3: Missing useTerminal Hook

**Location**: [src/frontend/src/components/windows/TerminalWindow.tsx](src/frontend/src/components/windows/TerminalWindow.tsx#L8)  
**Severity**: HIGH - Component won't render  
**Status**: ❌ NOT IMPLEMENTED

**Issue**:
```typescript
// Line 8 in TerminalWindow.tsx - HOOK DOESN'T EXIST
import { useTerminal } from '@/hooks/useSessions';

const { output, history, sendCommand, clearOutput } = useTerminal(sessionId);
```

**Problem**: The hook `useTerminal` is imported but doesn't exist in [src/frontend/src/hooks/useSessions.ts](src/frontend/src/hooks/useSessions.ts)

**What exists in useSessions.ts**:
```typescript
export function useSessions(workspaceId: string) { ... }
export function useSessionMetrics(sessionId: string | null) { ... }
// ❌ useTerminal does NOT exist
```

**Fix - Add to useSessions.ts**:
```typescript
export function useTerminal(sessionId: string | null) {
  const [output, setOutput] = useState<string>('');
  const [history, setHistory] = useState<string[]>([]);
  
  const sendCommand = (command: string) => {
    if (!sessionId) return;
    // TODO: Send command via WebSocket or API
  };
  
  const clearOutput = () => {
    setOutput('');
  };
  
  return {
    output,
    history,
    sendCommand,
    clearOutput,
  };
}
```

**Impact**: TerminalWindow component will fail to render with `ReferenceError: useTerminal is not defined`

---

## HIGH PRIORITY ISSUES 🟠

### Issue #4: Celery Tasks Are All Stubs

**Location**: [src/backend/tasks.py](src/backend/tasks.py)  
**Severity**: HIGH - No background tasks work  
**Status**: ❌ ALL INCOMPLETE

**List of Stub Tasks** (Lines shown):

```python
# Lines 35-41
@shared_task
def provision_gpu_session(workspace_id: str, provider: str, config: dict):
    logger.info(...)
    # Implementation will go here  # ❌
    pass

# Lines 43-49
@shared_task
def monitor_session_metrics(session_id: str):
    logger.info(...)
    # Implementation will go here  # ❌
    pass

# Lines 51-57
@shared_task
def create_checkpoint(session_id: str):
    logger.info(...)
    # Implementation will go here  # ❌
    pass

# Lines 59-65
@shared_task
def restore_checkpoint(session_id: str, checkpoint_id: str):
    logger.info(...)
    # Implementation will go here  # ❌
    pass

# Lines 67-73
@shared_task
def terminate_session(session_id: str):
    logger.info(...)
    # Implementation will go here  # ❌
    pass

# Lines 75-81
@shared_task
def execute_workflow(workflow_id: str, run_id: str):
    logger.info(...)
    # Implementation will go here  # ❌
    pass

# Lines 83-93 (etc...)
```

**Total Stubs**: 13 tasks, all empty

**Impact**: No background jobs execute. Sessions don't provision, metrics don't collect, checkpoints don't save, workflows don't run.

---

### Issue #5: Provider System Completely Missing

**Location**: [src/backend/provider-sdk/](src/backend/provider-sdk/) - **EMPTY FOLDER**  
**Severity**: CRITICAL - Core feature missing  
**Status**: ❌ NOT STARTED

**Files that should exist but don't**:

1. **base.py** (200+ lines) - ProviderBase abstract class
   ```python
   class ProviderBase(ABC):
       @abstractmethod
       async def authenticate(self, credentials: Dict) -> bool
       @abstractmethod
       async def get_available_gpus(self) -> List[GPU]
       @abstractmethod
       async def allocate_gpu(self, config: Dict) -> str
       @abstractmethod
       async def get_metrics(self, session_id: str) -> Metrics
       @abstractmethod
       async def terminate_session(self, session_id: str) -> bool
   ```

2. **registry.py** (100+ lines) - Plugin registration system
   ```python
   class ProviderRegistry:
       def register(self, name: str, provider_class: Type[ProviderBase])
       def get_provider(self, name: str) -> ProviderBase
       def list_providers(self) -> List[str]
   ```

3. **local_docker.py** (100+ lines) - Local provider implementation
   ```python
   class LocalDockerProvider(ProviderBase):
       async def authenticate(self, credentials) -> bool
       async def get_available_gpus(self) -> List[GPU]
       # ... implement all abstract methods
   ```

4. **runpod.py, vastai.py, lambda_labs.py** - Other provider implementations (future)

**Impact**: Cannot allocate any GPUs. System is non-functional for its core purpose.

---

### Issue #6: No Checkpoint Service

**Location**: [src/backend/services/](src/backend/services/) - **DOESN'T EXIST**  
**Severity**: HIGH - Session persistence missing  
**Status**: ❌ NOT IMPLEMENTED

**Missing File**: `src/backend/services/checkpoint_service.py` (300+ lines)

**Should implement**:
```python
class CheckpointService:
    async def create_checkpoint(self, session_id: str) -> Checkpoint
    async def restore_checkpoint(self, session_id: str, checkpoint_id: str) -> bool
    async def list_checkpoints(self, session_id: str) -> List[Checkpoint]
    async def delete_checkpoint(self, checkpoint_id: str) -> bool
    async def start_auto_checkpoint_loop(self, session_id: str)
    # ... backup to S3, lifecycle management, etc.
```

**Impact**: User sessions lost on disconnection. Cannot resume work. No persistence.

---

### Issue #7: No GPU Scheduler

**Location**: [src/backend/services/](src/backend/services/) - **DOESN'T EXIST**  
**Severity**: HIGH - GPU allocation missing  
**Status**: ❌ DESIGNED BUT NOT IMPLEMENTED

**Missing File**: `src/backend/services/scheduler_service.py` (200+ lines)

**Should implement multi-objective optimization**:
```python
class GPUScheduler:
    WEIGHTS = {
        'cost': 0.3,
        'performance': 0.25,
        'availability': 0.25,
        'latency': 0.2
    }
    
    async def allocate_gpu(
        self,
        workspace: Workspace,
        requirements: GPURequirements,
        constraints: Optional[GPUConstraints] = None
    ) -> GPUAllocation
```

**Impact**: Cannot intelligently select GPUs. No cost optimization. No performance optimization.

---

### Issue #8: Database Models Unused

**Location**: [src/backend/models.py](src/backend/models.py#L100-380)  
**Severity**: MEDIUM - Database tables created but inaccessible  
**Status**: ⚠️ PARTIAL - Models exist, no CRUD routes

**Unused Models**:

1. **Workflow** (Line ~120)
   - ✅ Model exists
   - ❌ No GET/POST/PATCH/DELETE routes
   - ❌ No service class

2. **WorkflowRun** (Line ~150)
   - ✅ Model exists
   - ❌ No execution routes
   - ❌ No executor service

3. **Checkpoint** (Line ~100)
   - ✅ Model exists
   - ❌ No CRUD routes
   - ❌ No checkpoint service

4. **ProviderCredentials** (Line ~170)
   - ✅ Model exists
   - ❌ No credential management routes
   - ❌ No encryption/decryption

5. **Metrics** (Line ~190)
   - ✅ Model exists
   - ❌ No data collection
   - ❌ No query endpoints

6. **AuditLog** (Line ~200)
   - ✅ Model exists
   - ❌ No query routes
   - ❌ No audit logging

**Impact**: Database overhead, schema complexity without functionality.

---

## MEDIUM PRIORITY ISSUES 🟡

### Issue #9: Missing Route Handlers

**Location**: Multiple route files  
**Severity**: MEDIUM - Features designed but not exposed  
**Status**: ❌ NOT IMPLEMENTED

**Missing Routes**:

#### Workflow Management (0/7)
```
❌ POST   /api/v1/workspaces/{id}/workflows
❌ GET    /api/v1/workspaces/{id}/workflows
❌ GET    /api/v1/workflows/{id}
❌ PATCH  /api/v1/workflows/{id}
❌ DELETE /api/v1/workflows/{id}
❌ POST   /api/v1/workflows/{id}/run
❌ GET    /api/v1/workflows/{id}/runs
```

#### Checkpoint Management (0/5)
```
❌ POST   /api/v1/sessions/{id}/checkpoints
❌ GET    /api/v1/sessions/{id}/checkpoints
❌ GET    /api/v1/checkpoints/{id}
❌ POST   /api/v1/checkpoints/{id}/restore
❌ DELETE /api/v1/checkpoints/{id}
```

#### Provider Management (0/5)
```
❌ GET    /api/v1/providers
❌ POST   /api/v1/users/provider-credentials
❌ GET    /api/v1/users/provider-credentials
❌ DELETE /api/v1/users/provider-credentials/{provider}
❌ GET    /api/v1/providers/{name}/gpus
```

**Impact**: No way to use designed features through API.

---

### Issue #10: Missing Frontend Components

**Location**: [src/frontend/src/components/](src/frontend/src/components/)  
**Severity**: MEDIUM - Frontend stubs exist  
**Status**: ⚠️ PARTIAL IMPLEMENTATION

**Component Status**:

1. **EditorWindow.tsx** (50 lines) - ⚠️ Partial
   - ✅ UI framework exists
   - ❌ No file I/O
   - ❌ No language detection
   - ❌ No syntax highlighting

2. **TerminalWindow.tsx** (100 lines) - ⚠️ Partial
   - ✅ Terminal UI exists
   - ❌ No WebSocket connection
   - ❌ No command execution
   - ❌ No terminal proxy

3. **FileBrowser.tsx** - ❌ Missing
   - File tree UI needed
   - Need API integration
   - Need file operations (create, delete, rename)

4. **WorkflowBuilder.tsx** - ❌ Missing
   - Canvas needed
   - Node palette needed
   - Connection editor needed
   - DAG validation needed

5. **MetricsDashboard.tsx** - ❌ Missing
   - GPU usage chart
   - Memory chart
   - Temperature chart
   - Cost tracker

**Impact**: Users can't see/interact with advanced features.

---

### Issue #11: Missing Frontend Hooks

**Location**: [src/frontend/src/hooks/useSessions.ts](src/frontend/src/hooks/useSessions.ts)  
**Severity**: MEDIUM - Partial hook implementation  
**Status**: ⚠️ INCOMPLETE

**Existing Hooks** (2):
```typescript
✅ useSessions(workspaceId) - Session CRUD
✅ useSessionMetrics(sessionId) - Metrics streaming
```

**Missing Hooks** (7+):
```typescript
❌ useTerminal(sessionId)
❌ useWorkflows(workspaceId)
❌ useCheckpoints(sessionId)
❌ useProviders()
❌ useAIAssistant(workspaceId)
❌ useMetricsHistory(sessionId)
❌ useWorkflowExecution(workflowId)
```

**Impact**: No way to call new backend features from frontend components.

---

### Issue #12: Missing Zustand Stores

**Location**: [src/frontend/src/stores/](src/frontend/src/stores/)  
**Severity**: MEDIUM - State management incomplete  
**Status**: ⚠️ PARTIAL

**Existing Stores** (5):
```typescript
✅ authStore.ts
✅ desktopStore.ts
✅ sessionStore.ts
✅ websocketStore.ts
✅ workspaceStore.ts
```

**Missing Stores** (4+):
```typescript
❌ workflowStore.ts - Workflow state
❌ checkpointStore.ts - Checkpoint browser state
❌ providerStore.ts - Provider selection state
❌ metricsStore.ts - Historical metrics state
```

**Impact**: No client-side state management for new features.

---

## CONFIGURATION ISSUES 🔧

### Issue #13: Missing Environment Variables

**Location**: `.env` file  
**Severity**: MEDIUM - Required config not set  
**Status**: ⚠️ PARTIALLY CONFIGURED

**Missing/Not Set**:

```bash
# Provider Credentials Encryption
PROVIDER_CREDENTIALS_ENCRYPTION_KEY=          # ❌ CRITICAL - Not set
# Used by: ProviderCredentials model encryption

# S3/MinIO Configuration
S3_BUCKET_NAME=                               # ❌ NOT SET
S3_REGION=                                    # ❌ NOT SET
S3_ENDPOINT=http://minio:9000                # ⚠️ Not verified
# Used by: Checkpoint storage, file persistence

# AI Integration
OPENAI_API_KEY=                               # ❌ NOT SET
OPENAI_MODEL=gpt-4                            # ⚠️ Not used yet

# Monitoring
SENTRY_DSN=                                   # ❌ NOT SET
PROMETHEUS_ENDPOINT=http://prometheus:9090   # ⚠️ Not used yet

# Provider API Keys
RUNPOD_API_KEY=                               # ❌ NOT SET (needed for provider)
VASTAI_API_KEY=                               # ❌ NOT SET (needed for provider)
```

**Impact**: Features requiring these configs won't work (checkpoints, AI, providers).

---

## TESTING & VALIDATION

### Issue #14: No End-to-End Tests for GPU Provisioning

**Location**: [src/backend/tests/](src/backend/tests/)  
**Severity**: MEDIUM - No way to verify GPU features  
**Status**: ❌ NOT WRITTEN

**Missing Test Coverage**:
- No provider mock tests
- No scheduler tests
- No checkpoint tests
- No workflow tests
- No full e2e session provisioning test

**Impact**: Can't verify if implementations work without manual testing.

---

## DOCUMENTATION ISSUES 📚

### Issue #15: Implementation Gaps in Docs

Some design documents reference code that doesn't exist:

1. **PROVIDER_SDK.md** - References imports that don't exist:
   ```python
   from providers.base import ProviderBase
   from providers.registry import provider_registry
   # These modules don't exist!
   ```

2. **GPU_SCHEDULER.md** - References scheduler that doesn't exist:
   ```python
   from services.scheduler_service import GPUScheduler
   # This file doesn't exist!
   ```

3. **SESSION_PERSISTENCE.md** - References checkpoint service that doesn't exist:
   ```python
   from services.checkpoint_service import CheckpointService
   # This file doesn't exist!
   ```

**Impact**: Docs suggest implementation exists when it doesn't.

---

## Quick Reference: What Needs to Be Done

### To Fix Critical Bugs (1-2 hours)
1. Fix session model field name in routes/sessions.py
2. Complete stop session endpoint
3. Add useTerminal hook to frontend

### To Implement Core Features (40-60 hours)
1. Create Provider system (base.py, registry.py, local_docker.py)
2. Implement GPU Scheduler
3. Create Checkpoint Service
4. Implement all 13 Celery tasks

### To Add Major Features (100+ hours)
1. Workflow Executor
2. AI Assistant integration
3. IDE/code-server integration
4. Terminal backend proxy
5. Frontend components for all features

---

**Last Updated**: 2026-05-30  
**Issues Found**: 15 major issues, 40+ specific code gaps
