# Session Provisioning & GPU Management

## Overview

Session Provisioning manages GPU resource allocation, lifecycle, and monitoring. Key features:

- **Multi-provider support** - Local Docker, RunPod, Vast.ai
- **GPU allocation** - Specify GPU type, memory, timeouts
- **Real-time monitoring** - Live metrics via WebSocket
- **Session lifecycle** - Create, monitor, stop sessions
- **Cost tracking** - Monitor estimated costs
- **Automatic cleanup** - Timeout-based session termination

## Architecture

### Session Lifecycle

```
[Start Request]
      ↓
[Pending] → Wait for provider allocation
      ↓
[Running] → GPU allocated, environment ready
      ↓
[Monitoring] → Stream metrics, handle events
      ↓
[Stop Request or Timeout]
      ↓
[Stopped] → Cleanup, finalize costs
```

### Provider Integration

Each provider implements same interface:

```python
class ProviderInterface(ABC):
    async def allocate_gpu(config: Dict) -> str  # Returns session_id
    async def get_metrics(session_id: str) -> Dict
    async def terminate(session_id: str) -> bool
```

## API Endpoints

### Start GPU Session

```bash
POST /api/v1/workspaces/{workspace_id}/sessions
```

**Request:**
```json
{
  "provider": "local_docker",
  "gpu_type": "RTX 4090",
  "memory_gb": 16,
  "timeout_hours": 1
}
```

**Response:**
```json
{
  "id": "session-123abc",
  "workspace_id": "workspace-456",
  "provider": "local_docker",
  "status": "pending",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "config": {
    "gpu_type": "RTX 4090",
    "memory_gb": 16,
    "timeout_hours": 1
  }
}
```

### List Sessions

```bash
GET /api/v1/workspaces/{workspace_id}/sessions
```

**Response:**
```json
[
  {
    "id": "session-123abc",
    "workspace_id": "workspace-456",
    "provider": "local_docker",
    "status": "running",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:32:45Z",
    "config": { ... }
  }
]
```

### Get Session Details

```bash
GET /api/v1/workspaces/{workspace_id}/sessions/{session_id}
```

### Stop Session

```bash
POST /api/v1/workspaces/{workspace_id}/sessions/{session_id}/stop
```

**Response:**
```json
{
  "message": "Session stopped",
  "session": {
    "id": "session-123abc",
    "status": "stopped",
    "cost": 12.50,
    "duration_seconds": 3600
  }
}
```

### Get Session Logs

```bash
GET /api/v1/workspaces/{workspace_id}/sessions/{session_id}/logs?lines=100
```

**Response:**
```json
{
  "session_id": "session-123abc",
  "logs": [
    "[2024-01-15 10:30:00] Session initialized",
    "[2024-01-15 10:30:05] GPU allocated: RTX 4090",
    "[2024-01-15 10:30:10] Environment ready"
  ]
}
```

## WebSocket Events

### Session Events

```typescript
// Session started
{
  type: 'session.started',
  data: {
    session_id: 'session-123',
    provider: 'local_docker',
    gpu_type: 'RTX 4090',
  },
  session_id: 'session-123',
  workspace_id: 'workspace-456',
}

// Session stopped
{
  type: 'session.stopped',
  data: {
    session_id: 'session-123',
    duration_seconds: 3600,
    cost: 12.50,
  },
  session_id: 'session-123',
}

// Session error
{
  type: 'session.error',
  data: {
    session_id: 'session-123',
    error: 'GPU out of memory',
    error_code: 'OOM',
  },
  session_id: 'session-123',
}

// Session status update
{
  type: 'session.status_update',
  data: {
    session_id: 'session-123',
    status: 'running',
    uptime_seconds: 300,
  },
  session_id: 'session-123',
}
```

### Metrics Events

```typescript
// Metrics update (every second)
{
  type: 'metrics.update',
  data: {
    gpu_usage: 45.2,
    gpu_memory_used: 24576,
    gpu_temperature: 72,
    cpu_usage: 28.5,
    system_memory: 8192,
    disk_usage: 50.0,
  },
  session_id: 'session-123',
  workspace_id: 'workspace-456',
}
```

## Frontend Usage

### React Hook - Start Session

```typescript
import { useSessions } from '@/hooks/useSessions';

function MyComponent({ workspaceId }) {
  const { sessions, currentSession, startSession, stopSession } = useSessions(workspaceId);

  const handleStart = async () => {
    const session = await startSession({
      provider: 'local_docker',
      gpu_type: 'RTX 4090',
      memory_gb: 16,
      timeout_hours: 1,
    });
    console.log('Session started:', session);
  };

  const handleStop = async () => {
    if (currentSession) {
      await stopSession(currentSession.id);
    }
  };

  return (
    <div>
      <button onClick={handleStart}>Start GPU Session</button>
      {currentSession && (
        <div>
          <p>Status: {currentSession.status}</p>
          <button onClick={handleStop}>Stop Session</button>
        </div>
      )}
    </div>
  );
}
```

### React Hook - Monitor Metrics

```typescript
import { useSessionMetrics } from '@/hooks/useSessions';

function MetricsMonitor({ sessionId }) {
  const { metrics, isLive } = useSessionMetrics(sessionId);

  if (!isLive) return <div>Waiting for metrics...</div>;

  return (
    <div>
      <p>GPU Usage: {metrics.gpu_usage}%</p>
      <p>Memory: {metrics.gpu_memory_used} MB / {metrics.gpu_memory_total} MB</p>
      <p>Temperature: {metrics.gpu_temperature}°C</p>
    </div>
  );
}
```

### React Hook - Terminal I/O

```typescript
import { useTerminal } from '@/hooks/useSessions';

function Terminal({ sessionId }) {
  const { output, sendCommand, clearOutput } = useTerminal(sessionId);

  return (
    <div>
      <div className="terminal-output">{output}</div>
      <input
        type="text"
        placeholder="Enter command..."
        onKeyPress={(e) => {
          if (e.key === 'Enter') {
            sendCommand(e.target.value);
            e.target.value = '';
          }
        }}
      />
      <button onClick={clearOutput}>Clear</button>
    </div>
  );
}
```

### Component - SessionsPanel

The SessionsPanel component provides a UI for:
- Starting new sessions
- Listing active sessions
- Displaying live metrics
- Stopping sessions

```typescript
import { SessionsPanel } from '@/components/sessions/SessionsPanel';

function Dashboard() {
  return (
    <div>
      <SessionsPanel workspaceId="workspace-123" />
    </div>
  );
}
```

## Backend Implementation

### Session Service

```python
from routes.sessions import SessionService

# Create session
session = SessionService.create_session(
    db=db,
    workspace_id='workspace-123',
    user_id='user-456',
    provider='local_docker',
    provider_session_id='docker-abc123',
    config={
        'gpu_type': 'RTX 4090',
        'memory_gb': 16,
    }
)

# Update status
SessionService.update_session_status(
    db=db,
    session=session,
    status='running',
    started_at=datetime.utcnow()
)

# Terminate
SessionService.terminate_session(db, session)
```

### Broadcasting Status Updates

```python
from websocket.manager import manager, EventType, WebSocketEvent
import asyncio

async def emit_session_status():
    event = WebSocketEvent(
        event_type=EventType.SESSION_STATUS_UPDATE,
        data={
            'session_id': 'session-123',
            'status': 'running',
            'uptime_seconds': 300,
        },
        workspace_id='workspace-456',
        session_id='session-123',
    )
    
    await manager.broadcast_to_workspace('workspace-456', event)
```

## Providers

### Local Docker (Default)

Uses host Docker daemon for GPU allocation.

**Config:**
```python
{
    'provider': 'local_docker',
    'gpu_type': 'RTX 4090',  # Optional
    'memory_gb': 16,
    'timeout_hours': 1,
}
```

**Status:** ✅ Ready for integration

### RunPod

Cloud GPU provider with hundreds of GPUs available.

**Config:**
```python
{
    'provider': 'runpod',
    'gpu_type': 'RTX 4090',
    'memory_gb': 16,
    'timeout_hours': 1,
}
```

**Requires:**
- RUNPOD_API_KEY in environment
- RunPod account with API key

**Status:** 📋 Ready for implementation

### Vast.ai

Decentralized GPU marketplace.

**Config:**
```python
{
    'provider': 'vast_ai',
    'gpu_type': 'A100',
    'memory_gb': 40,
    'timeout_hours': 2,
}
```

**Requires:**
- VASTAI_API_KEY in environment
- Vast.ai account

**Status:** 📋 Ready for implementation

## Database Schema

### WorkspaceSession Model

```python
class WorkspaceSession(Base):
    id: str = Column(String(36), primary_key=True)
    workspace_id: str = Column(String(36), ForeignKey('workspaces.id'))
    provider: str = Column(String(50))  # local_docker, runpod, vast.ai
    provider_session_id: str = Column(String(255))  # Provider's internal ID
    status: str = Column(String(50))  # pending, running, stopped, error
    config: dict = Column(JSON)  # GPU type, memory, timeout, etc.
    cost_estimate: float = Column(Float, default=0.0)
    metrics_json: dict = Column(JSON)  # Latest metrics snapshot
    created_by: str = Column(String(36), ForeignKey('users.id'))
    created_at: datetime = Column(DateTime, server_default=utcnow())
    updated_at: datetime = Column(DateTime, onupdate=utcnow())
    started_at: datetime = Column(DateTime, nullable=True)
    terminated_at: datetime = Column(DateTime, nullable=True)
```

## Cost Tracking

Each session tracks estimated costs:

```python
session.cost_estimate = calculate_cost(
    provider=session.provider,
    gpu_type=session.config['gpu_type'],
    duration_seconds=(session.terminated_at - session.created_at).total_seconds(),
    memory_gb=session.config['memory_gb'],
)
```

## Error Handling

### Common Errors

| Error | Cause | Recovery |
|-------|-------|----------|
| GPU Out of Memory | Requested GPU can't fit workload | Reduce memory_gb or increase timeout |
| Provider Unavailable | Cloud provider down | Retry with different provider |
| Timeout Exceeded | Session ran too long | Set higher timeout_hours |
| Authentication Failed | Invalid API keys | Check provider credentials |

### Error Flow

```
[Session Start Failure]
      ↓
[Emit session.error event via WebSocket]
      ↓
[Set session status to 'error']
      ↓
[Log error details in audit]
      ↓
[User sees error in UI]
      ↓
[Can retry or select different provider]
```

## Monitoring

### Session Health Checks

- Every 30 seconds: Check if session is responsive
- Every 60 seconds: Collect and emit metrics
- On timeout: Automatically terminate session
- On error: Emit error event and cleanup

### Metrics Collection

Metrics are collected and broadcast:

```python
metrics = {
    'gpu_usage': 45.2,           # Percent
    'gpu_memory_used': 24576,    # MB
    'gpu_memory_total': 49152,   # MB
    'gpu_temperature': 72,       # Celsius
    'cpu_usage': 28.5,           # Percent
    'system_memory': 8192,       # MB
    'disk_usage': 50.0,          # Percent
}
```

## Next Steps

1. **Provider Integration** - Implement RunPod and Vast.ai adapters
2. **GPU Scheduling** - Multi-objective optimization (cost, availability, performance)
3. **Checkpointing** - Save session state to restore later
4. **Auto-scaling** - Provision/deprovision based on demand
5. **Cost Optimization** - Spot instance support, smart scheduling

---

**Session Provisioning is now ready for GPU workloads!** 🚀
