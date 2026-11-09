# WebSocket Real-Time Events

## Overview

The Cloud OS platform uses WebSockets for real-time communication between clients and server. This enables:

- **Real-time metrics** - GPU usage, memory, CPU updates
- **Session management** - Session start/stop notifications
- **Terminal output** - Live terminal streaming
- **Workflow execution** - Step-by-step workflow progress
- **Collaboration** - User presence, cursor updates
- **System events** - Heartbeats, error notifications

## Connection

### Connect from Backend

```python
from websocket.manager import manager, EventType, WebSocketEvent

# Broadcast event to workspace
event = WebSocketEvent(
    event_type=EventType.METRICS_UPDATE,
    data={
        "gpu_usage": 45.2,
        "memory_usage": 2048,
        "temperature": 72,
    },
    workspace_id="workspace-123",
)
await manager.broadcast_to_workspace("workspace-123", event)

# Send to specific user
await manager.send_to_user("user-123", event)
```

### Connect from Frontend

```typescript
import { WebSocketClient, EventType } from '@/api/websocket';

// Create client
const client = new WebSocketClient(
  'http://localhost:8000',
  'jwt-token-here',
  'workspace-123'
);

// Connect
await client.connect();

// Subscribe to events
client.on(EventType.METRICS_UPDATE, (event) => {
  console.log('GPU usage:', event.data.gpu_usage);
});

// Send event
client.sendEvent({
  type: EventType.TERMINAL_INPUT,
  data: { command: 'ls -la' },
  timestamp: new Date().toISOString(),
});

// Disconnect
client.disconnect();
```

### Using Zustand Store

```typescript
import { useWebSocketStore } from '@/stores/websocketStore';

// In component
const { isConnected, activeUsers, connect, disconnect } = useWebSocketStore();

useEffect(() => {
  // Connect to workspace
  connect('workspace-123', token);

  return () => disconnect();
}, []);
```

## Event Types

### Session Events

```typescript
// Session started
{
  type: 'session.started',
  data: {
    session_id: 'session-123',
    provider: 'runpod',
    gpu_type: 'RTX 4090',
  },
  workspace_id: 'workspace-123',
  user_id: 'user-123',
  timestamp: '2024-01-15T10:30:00Z'
}

// Session stopped
{
  type: 'session.stopped',
  data: {
    session_id: 'session-123',
    duration_seconds: 3600,
    cost: 12.50,
  },
  workspace_id: 'workspace-123',
  timestamp: '2024-01-15T11:30:00Z'
}

// Session error
{
  type: 'session.error',
  data: {
    session_id: 'session-123',
    error: 'GPU out of memory',
    error_code: 'OOM',
  },
  workspace_id: 'workspace-123',
  timestamp: '2024-01-15T10:35:00Z'
}

// Session status update
{
  type: 'session.status_update',
  data: {
    session_id: 'session-123',
    status: 'running',
    uptime_seconds: 300,
  },
  workspace_id: 'workspace-123',
  timestamp: '2024-01-15T10:35:00Z'
}
```

### Metrics Events

```typescript
// Metrics update
{
  type: 'metrics.update',
  data: {
    session_id: 'session-123',
    timestamp: 1705318200,
    metrics: {
      gpu_usage: 45.2,
      gpu_memory_used: 24576,
      gpu_temperature: 72,
      cpu_usage: 28.5,
      system_memory: 8192,
      disk_usage: 50.0,
    },
  },
  session_id: 'session-123',
  workspace_id: 'workspace-123',
  timestamp: '2024-01-15T10:30:45Z'
}

// GPU usage
{
  type: 'gpu.usage',
  data: {
    session_id: 'session-123',
    usage_percent: 45.2,
    memory_used_mb: 24576,
    memory_total_mb: 49152,
  },
  session_id: 'session-123',
  timestamp: '2024-01-15T10:30:45Z'
}

// Memory usage
{
  type: 'memory.usage',
  data: {
    session_id: 'session-123',
    used_mb: 8192,
    total_mb: 16384,
    percent: 50.0,
  },
  session_id: 'session-123',
  timestamp: '2024-01-15T10:30:45Z'
}
```

### Terminal Events

```typescript
// Terminal output
{
  type: 'terminal.output',
  data: {
    session_id: 'session-123',
    output: 'total 24\ndrwxr-xr-x  5 user staff  160 Jan 15 10:30 .\n',
    stream: 'stdout',
  },
  session_id: 'session-123',
  user_id: 'user-123',
  workspace_id: 'workspace-123',
  timestamp: '2024-01-15T10:30:45Z'
}

// Terminal input
{
  type: 'terminal.input',
  data: {
    session_id: 'session-123',
    command: 'ls -la',
  },
  session_id: 'session-123',
  user_id: 'user-123',
  workspace_id: 'workspace-123',
  timestamp: '2024-01-15T10:30:44Z'
}

// Terminal resize
{
  type: 'terminal.resize',
  data: {
    session_id: 'session-123',
    cols: 120,
    rows: 30,
  },
  session_id: 'session-123',
  user_id: 'user-123',
  workspace_id: 'workspace-123',
  timestamp: '2024-01-15T10:30:44Z'
}
```

### Workflow Events

```typescript
// Workflow started
{
  type: 'workflow.started',
  data: {
    workflow_id: 'workflow-123',
    workflow_run_id: 'run-456',
    total_steps: 5,
  },
  workspace_id: 'workspace-123',
  user_id: 'user-123',
  timestamp: '2024-01-15T10:30:00Z'
}

// Workflow step completed
{
  type: 'workflow.step_completed',
  data: {
    workflow_run_id: 'run-456',
    step_id: 'step-1',
    step_name: 'Data Preprocessing',
    duration_seconds: 45,
    output: { records_processed: 10000 },
  },
  workspace_id: 'workspace-123',
  timestamp: '2024-01-15T10:30:45Z'
}

// Workflow step failed
{
  type: 'workflow.step_failed',
  data: {
    workflow_run_id: 'run-456',
    step_id: 'step-2',
    step_name: 'Model Training',
    error: 'Out of memory',
    error_code: 'OOM',
  },
  workspace_id: 'workspace-123',
  timestamp: '2024-01-15T10:31:30Z'
}

// Workflow completed
{
  type: 'workflow.completed',
  data: {
    workflow_run_id: 'run-456',
    status: 'success',
    total_duration_seconds: 300,
    results: { accuracy: 0.95 },
  },
  workspace_id: 'workspace-123',
  timestamp: '2024-01-15T10:35:00Z'
}
```

### Collaboration Events

```typescript
// User joined
{
  type: 'user.joined',
  data: {
    user_id: 'user-123',
    username: 'john_doe',
    active_users: ['user-123', 'user-456'],
  },
  workspace_id: 'workspace-123',
  timestamp: '2024-01-15T10:30:00Z'
}

// User left
{
  type: 'user.left',
  data: {
    user_id: 'user-123',
    active_users: ['user-456'],
  },
  workspace_id: 'workspace-123',
  timestamp: '2024-01-15T10:31:00Z'
}

// Cursor update
{
  type: 'cursor.update',
  data: {
    user_id: 'user-123',
    line: 45,
    column: 12,
    filename: 'main.py',
  },
  workspace_id: 'workspace-123',
  user_id: 'user-123',
  timestamp: '2024-01-15T10:30:45Z'
}
```

### System Events

```typescript
// Connection established
{
  type: 'connection.established',
  data: {
    message: 'Connected to workspace',
    workspace_id: 'workspace-123',
    active_users: ['user-123', 'user-456'],
  },
  user_id: 'user-123',
  workspace_id: 'workspace-123',
  timestamp: '2024-01-15T10:30:00Z'
}

// Heartbeat
{
  type: 'heartbeat',
  data: {},
  timestamp: '2024-01-15T10:30:30Z'
}

// Error
{
  type: 'error',
  data: {
    error: 'Invalid event format',
    code: 'INVALID_EVENT',
  },
  timestamp: '2024-01-15T10:30:45Z'
}
```

## Usage Examples

### React Component with Real-Time Metrics

```typescript
import { useEffect, useState } from 'react';
import { useWebSocketStore } from '@/stores/websocketStore';
import { EventType } from '@/api/websocket';

export function MetricsDisplay() {
  const { client, isConnected } = useWebSocketStore();
  const [metrics, setMetrics] = useState<any>(null);

  useEffect(() => {
    if (!client || !isConnected) return;

    // Subscribe to metrics updates
    const unsubscribe = client.on(EventType.METRICS_UPDATE, (event) => {
      setMetrics(event.data.metrics);
    });

    return unsubscribe;
  }, [client, isConnected]);

  if (!metrics) return <div>Waiting for metrics...</div>;

  return (
    <div>
      <p>GPU Usage: {metrics.gpu_usage}%</p>
      <p>Memory: {metrics.gpu_memory_used} MB</p>
      <p>Temperature: {metrics.gpu_temperature}°C</p>
    </div>
  );
}
```

### Terminal Component

```typescript
import { useEffect, useRef } from 'react';
import { useWebSocketStore } from '@/stores/websocketStore';
import { EventType } from '@/api/websocket';

export function Terminal() {
  const { client, isConnected } = useWebSocketStore();
  const outputRef = useRef<HTMLDivElement>(null);
  const sessionId = 'session-123'; // Get from context

  useEffect(() => {
    if (!client || !isConnected) return;

    // Subscribe to terminal output
    const unsubscribe = client.on(EventType.TERMINAL_OUTPUT, (event) => {
      if (event.session_id !== sessionId) return;

      if (outputRef.current) {
        outputRef.current.textContent += event.data.output;
        outputRef.current.scrollTop = outputRef.current.scrollHeight;
      }
    });

    return unsubscribe;
  }, [client, isConnected, sessionId]);

  const sendCommand = (command: string) => {
    if (!client || !isConnected) return;

    client.sendEvent({
      type: EventType.TERMINAL_INPUT,
      data: { command, session_id: sessionId },
      timestamp: new Date().toISOString(),
    });
  };

  return (
    <div>
      <div ref={outputRef} className="terminal-output" />
      <input
        type="text"
        placeholder="Enter command..."
        onKeyPress={(e) => {
          if (e.key === 'Enter') {
            sendCommand(e.currentTarget.value);
            e.currentTarget.value = '';
          }
        }}
      />
    </div>
  );
}
```

## Best Practices

### 1. Always Cleanup Subscriptions

```typescript
useEffect(() => {
  const unsubscribe = client.on(EventType.METRICS_UPDATE, handler);
  return unsubscribe; // Cleanup on unmount
}, []);
```

### 2. Handle Connection Errors

```typescript
try {
  await connect(workspaceId, token);
} catch (error) {
  console.error('Failed to connect:', error);
  // Show error to user
}
```

### 3. Use Proper Session IDs

```typescript
// Always include session_id for session-specific events
client.sendEvent({
  type: EventType.TERMINAL_INPUT,
  data: {
    command: 'ls',
    session_id: sessionId, // Important!
  },
  timestamp: new Date().toISOString(),
});
```

### 4. Implement Backpressure

```typescript
// Don't send events faster than they can be processed
const throttledSend = useMemo(
  () => throttle((cmd: string) => sendCommand(cmd), 100),
  []
);
```

### 5. Monitor Connection Health

```typescript
const { isConnected, error } = useWebSocketStore();

if (error) {
  return <div className="error">Connection error: {error}</div>;
}

if (!isConnected) {
  return <div className="loading">Connecting...</div>;
}
```

## Debugging

### Enable Debug Logging

```typescript
// In browser DevTools console
localStorage.setItem('debug', 'websocket:*');
```

### Check Connection Status

```typescript
const { isConnected, workspaceId } = useWebSocketStore();
console.log('Connected:', isConnected);
console.log('Workspace:', workspaceId);
```

### Monitor Events

```typescript
client.on(EventType.HEARTBEAT, (event) => {
  console.log('Heartbeat received', event.timestamp);
});
```

## Architecture

### Backend Flow

```
WebSocket Connection
       ↓
routes/websocket.py → verify JWT token
       ↓
manager.connect() → add to active connections
       ↓
Receive event → validate → emit to handlers
       ↓
Other service sends event → manager.broadcast_to_workspace()
       ↓
All clients receive event
```

### Frontend Flow

```
User action
       ↓
sendEvent() → JSON serialize → send to WebSocket
       ↓
Server processes
       ↓
Server broadcasts event
       ↓
handleMessage() → parse JSON → emit to subscribers
       ↓
Component handlers execute → update state → re-render
```

---

**WebSocket is now ready for real-time applications!** 🚀
