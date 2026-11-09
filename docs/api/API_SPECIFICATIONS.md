# API Specifications

**Document**: REST API & WebSocket Event Specifications
**Version**: 1.0
**Status**: Design Phase

## Base URL

```
https://api.cloud-os.example.com/api/v1
```

## Authentication

All requests require Authorization header:

```
Authorization: Bearer {JWT_TOKEN}
```

## Response Format

```json
{
  "data": {},
  "error": null,
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-05-28T10:00:00Z"
  }
}
```

## Error Responses

```json
{
  "data": null,
  "error": {
    "code": "WORKSPACE_NOT_FOUND",
    "message": "Workspace not found",
    "details": {}
  },
  "meta": {}
}
```

## Authentication Endpoints

### POST /auth/github

Initiate GitHub OAuth login.

**Response:**
```json
{
  "data": {
    "authorization_url": "https://github.com/login/oauth/authorize?..."
  }
}
```

### POST /auth/github/callback

Handle GitHub OAuth callback.

**Query Parameters:**
- `code`: OAuth code from GitHub

**Response:**
```json
{
  "data": {
    "access_token": "eyJhbGc...",
    "token_type": "bearer",
    "expires_in": 900
  }
}
```

### POST /auth/refresh

Refresh JWT token.

**Response:**
```json
{
  "data": {
    "access_token": "eyJhbGc...",
    "expires_in": 900
  }
}
```

### POST /auth/logout

Logout and revoke tokens.

**Response:**
```json
{
  "data": {
    "message": "Logged out successfully"
  }
}
```

## Workspace Endpoints

### GET /workspaces

List all workspaces for user.

**Query Parameters:**
- `limit`: 1-100 (default: 20)
- `offset`: 0+ (default: 0)
- `sort`: 'created_at' | 'updated_at' | 'name'
- `order`: 'asc' | 'desc'

**Response:**
```json
{
  "data": [
    {
      "id": "uuid",
      "name": "Python Dev",
      "description": "Python development workspace",
      "base_image": "python:3.11",
      "created_at": "2026-05-28T10:00:00Z",
      "updated_at": "2026-05-28T10:00:00Z"
    }
  ],
  "meta": {
    "total": 5,
    "limit": 20,
    "offset": 0
  }
}
```

### POST /workspaces

Create new workspace.

**Request:**
```json
{
  "name": "Python Dev",
  "description": "Python development workspace",
  "base_image": "python:3.11",
  "environment": {
    "JUPYTER_ENABLE_LAB": "yes"
  }
}
```

**Response:**
```json
{
  "data": {
    "id": "uuid",
    "name": "Python Dev",
    "created_at": "2026-05-28T10:00:00Z"
  }
}
```

### GET /workspaces/{id}

Get workspace details.

**Response:**
```json
{
  "data": {
    "id": "uuid",
    "name": "Python Dev",
    "base_image": "python:3.11",
    "environment": {},
    "sessions": [
      {
        "id": "session-uuid",
        "provider": "runpod",
        "gpu_model": "RTX 4090",
        "status": "active"
      }
    ]
  }
}
```

### PUT /workspaces/{id}

Update workspace.

**Request:**
```json
{
  "name": "Python Development",
  "environment": {
    "CUDA_VERSION": "12.4"
  }
}
```

### DELETE /workspaces/{id}

Delete workspace (soft delete).

## Session Endpoints

### POST /workspaces/{workspace_id}/sessions

Create new session.

**Request:**
```json
{
  "gpu_type": "RTX 4090",
  "provider": null,
  "region": null,
  "timeout_minutes": 240
}
```

**Response:**
```json
{
  "data": {
    "id": "session-uuid",
    "workspace_id": "workspace-uuid",
    "provider": "runpod",
    "gpu_model": "RTX 4090",
    "vram_gb": 24,
    "status": "provisioning",
    "ide_url": "https://code.runpod.io?pod_id=...",
    "jupyter_url": "https://jupyter.runpod.io?pod_id=...",
    "created_at": "2026-05-28T10:00:00Z"
  }
}
```

### GET /sessions/{session_id}

Get session details.

**Response:**
```json
{
  "data": {
    "id": "session-uuid",
    "provider": "runpod",
    "status": "active",
    "gpu_model": "RTX 4090",
    "vram_gb": 24,
    "uptime_seconds": 3600,
    "cost_so_far": 0.50
  }
}
```

### GET /sessions/{session_id}/metrics

Get real-time metrics (historical).

**Query Parameters:**
- `start_time`: ISO 8601
- `end_time`: ISO 8601
- `interval`: 1s | 1m | 5m

**Response:**
```json
{
  "data": [
    {
      "timestamp": "2026-05-28T10:00:00Z",
      "gpu_utilization": 85.5,
      "gpu_memory_used_gb": 20.3,
      "gpu_temperature": 65,
      "gpu_power_w": 380,
      "cpu_utilization": 45.2,
      "system_memory_used_gb": 32.1
    }
  ]
}
```

### POST /sessions/{session_id}/checkpoint

Create manual checkpoint.

**Request:**
```json
{
  "name": "Before training",
  "description": "Checkpoint before starting training"
}
```

**Response:**
```json
{
  "data": {
    "id": "checkpoint-uuid",
    "name": "Before training",
    "storage_path": "s3://bucket/checkpoints/...",
    "file_size_mb": 5120,
    "created_at": "2026-05-28T10:00:00Z"
  }
}
```

### POST /sessions/{session_id}/recover

Manually trigger recovery.

**Response:**
```json
{
  "data": {
    "message": "Recovery initiated",
    "new_provider": "vastai",
    "estimated_recovery_time_seconds": 120
  }
}
```

### DELETE /sessions/{session_id}

Terminate session.

## Provider Endpoints

### GET /providers

List available provider plugins.

**Response:**
```json
{
  "data": [
    {
      "name": "runpod",
      "display_name": "RunPod",
      "version": "1.0",
      "authenticated": true,
      "gpu_models": ["RTX 4090", "A100", "H100"],
      "regions": ["us-east-1", "us-west-1"]
    }
  ]
}
```

### POST /providers/{name}/auth

Authenticate with provider.

**Request:**
```json
{
  "api_key": "secret-key"
}
```

**Response:**
```json
{
  "data": {
    "authenticated": true,
    "provider": "runpod",
    "account_balance": 42.50
  }
}
```

### DELETE /providers/{name}/auth

Revoke provider authentication.

### GET /providers/{name}/gpus

List available GPUs from provider.

**Query Parameters:**
- `region`: Optional region filter

**Response:**
```json
{
  "data": [
    {
      "id": "gpu-123",
      "model": "RTX 4090",
      "vram_gb": 24,
      "cuda_version": "12.4",
      "available": true,
      "hourly_cost_cents": 30,
      "region": "us-east-1"
    }
  ]
}
```

## Workflow Endpoints

### POST /workflows

Create workflow.

**Request:**
```json
{
  "name": "Model Fine-tuning",
  "description": "Fine-tune Llama 3",
  "definition": {
    "nodes": [...],
    "edges": [...]
  }
}
```

**Response:**
```json
{
  "data": {
    "id": "workflow-uuid",
    "name": "Model Fine-tuning",
    "version": 1,
    "created_at": "2026-05-28T10:00:00Z"
  }
}
```

### POST /workflows/{id}/run

Execute workflow.

**Request:**
```json
{
  "session_id": "session-uuid",
  "input_overrides": {}
}
```

**Response:**
```json
{
  "data": {
    "run_id": "run-uuid",
    "workflow_id": "workflow-uuid",
    "status": "pending"
  }
}
```

### GET /workflow-runs/{run_id}

Get workflow run status.

**Response:**
```json
{
  "data": {
    "id": "run-uuid",
    "workflow_id": "workflow-uuid",
    "status": "running",
    "progress": 0.35,
    "started_at": "2026-05-28T10:00:00Z",
    "estimated_completion": "2026-05-28T10:30:00Z"
  }
}
```

## WebSocket Events

### Connection

```
wss://api.cloud-os.example.com/ws
Headers: Authorization: Bearer {JWT}
```

### Client → Server Events

#### `session.subscribe`
Subscribe to session metrics.

```json
{
  "event": "session.subscribe",
  "session_id": "uuid"
}
```

#### `terminal.input`
Send terminal input.

```json
{
  "event": "terminal.input",
  "session_id": "uuid",
  "data": "command\n"
}
```

#### `workflow.step_trigger`
Manually trigger workflow step.

```json
{
  "event": "workflow.step_trigger",
  "run_id": "uuid",
  "node_id": "uuid"
}
```

### Server → Client Events

#### `metrics.update`
Real-time metrics update.

```json
{
  "event": "metrics.update",
  "session_id": "uuid",
  "data": {
    "gpu_utilization": 85.5,
    "vram_used_gb": 20.3,
    "temperature": 65
  }
}
```

#### `session.status`
Session status changed.

```json
{
  "event": "session.status",
  "session_id": "uuid",
  "status": "recovering",
  "message": "GPU failed, attempting recovery..."
}
```

#### `terminal.output`
Terminal output.

```json
{
  "event": "terminal.output",
  "session_id": "uuid",
  "data": "output text"
}
```

#### `workflow.step_completed`
Workflow step completed.

```json
{
  "event": "workflow.step_completed",
  "run_id": "uuid",
  "node_id": "uuid",
  "result": {}
}
```

## Rate Limits

- **Unauthenticated**: 30 requests/minute per IP
- **Authenticated**: 300 requests/minute per user
- **Sensitive endpoints** (auth, providers): 5 requests/minute

## Pagination

All list endpoints support:
- `limit`: 1-100 (default: 20)
- `offset`: 0+ (default: 0)

Response includes:
```json
{
  "meta": {
    "total": 100,
    "limit": 20,
    "offset": 0,
    "has_more": true
  }
}
```

## Status Codes

```
200 OK                  - Success
201 Created            - Resource created
202 Accepted           - Request accepted (async)
204 No Content         - Success, no body
400 Bad Request        - Invalid input
401 Unauthorized       - Authentication required
403 Forbidden          - Permission denied
404 Not Found          - Resource not found
409 Conflict           - Resource conflict
429 Too Many Requests  - Rate limited
500 Server Error       - Internal error
```

## Next Steps

- See [Deployment Guide](../operations/DEPLOYMENT.md)
- Review [MVP Roadmap](../operations/MVP_ROADMAP.md)
