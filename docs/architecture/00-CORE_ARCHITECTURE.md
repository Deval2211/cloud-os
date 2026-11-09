# Core Architecture - Universal AI Cloud OS

**Document**: Core System Architecture
**Version**: 1.0
**Date**: May 2026
**Status**: Design Phase

## Executive Summary

Universal AI Cloud OS is architected as a **distributed, cloud-native operating system** that unifies disparate GPU cloud providers, local GPU clusters, and edge nodes under a single browser-based interface.

The architecture is:
- **Modular**: Independent services communicate via async events
- **Scalable**: Stateless backends, horizontal scaling ready
- **Resilient**: Automatic failover, session recovery, checkpoint management
- **AI-native**: Optimized for GPU workloads, distributed training, inference
- **Future-proof**: Kubernetes-compatible from day one, marketplace-ready

## System Decomposition

### Layer 1: User Interface (Browser)

The frontend is a **React-based desktop environment** running in the browser.

**Key Components:**
- **Desktop Environment**: Custom window manager, taskbar, workspace switcher
- **GPU Monitor**: Real-time VRAM, CPU, storage metrics (WebSocket updates)
- **IDE Integration**: code-server embedding with extensions
- **Workflow Builder**: Drag-and-drop visual programming
- **Terminal**: xterm.js-based terminal emulator
- **Notification System**: Real-time alerts and job status

**Tech Stack:**
- Next.js 14+ (SSR + SSG)
- React 18+
- TailwindCSS
- Zustand (state management)
- Framer Motion (animations)
- Socket.io client (realtime)
- Ace/Monaco Editor

**Architecture Pattern:**
```
Pages (layout)
├── Desktop Container (main app shell)
│   ├── Taskbar (real-time metrics)
│   ├── Window Manager (floating windows)
│   ├── Workspace Manager
│   └── Notification Center
└── Sidebar/Navigation
    ├── File Explorer
    ├── Workflow Builder
    ├── Storage Manager
    └── Provider Management
```

### Layer 2: Backend Services (FastAPI)

The backend is a **microservice architecture** built on FastAPI with clear separation of concerns.

**Core Services:**

#### 2.1 Authentication & Authorization Service
```
- OAuth2 providers (Google, GitHub)
- JWT token generation/validation
- Refresh token management (server-side storage)
- RBAC (Role-Based Access Control)
- Multi-tenant isolation
```

#### 2.2 Workspace Manager
```
Responsibilities:
- Create/destroy/list workspaces
- Manage workspace lifecycle
- Persist workspace state
- Handle workspace switching
- Manage IDE/terminal sessions

Database:
- Workspaces table
- WorkspacePermissions
- WorkspaceState (snapshots)
```

#### 2.3 Provider Orchestrator
```
Responsibilities:
- Load provider plugins dynamically
- Route compute requests to appropriate providers
- Manage provider authentication
- Handle provider failures/fallback
- Cost optimization & estimation

Components:
- ProviderRegistry (in-memory + Redis cache)
- ProviderRouter (intelligent routing)
- ProviderHealthChecker
- ProviderAuthManager
```

#### 2.4 GPU Scheduler & Resource Manager
```
Responsibilities:
- Analyze available GPU resources
- Schedule workloads intelligently
- Allocate GPUs to jobs
- Monitor resource utilization
- Handle preemption & failover

Algorithm:
1. Collect GPU inventory from all providers
2. Filter by workload requirements (VRAM, GPU type)
3. Score candidates (cost, latency, availability)
4. Select optimal provider
5. Allocate resources
6. Monitor health, trigger failover if needed
```

#### 2.5 Session Manager
```
Responsibilities:
- Create/restore sessions
- Manage session state
- Handle session persistence
- Implement checkpoint system
- Auto-recovery on provider failure

Session State:
- Active workspaces
- Terminal states
- Notebook kernel state
- File system state
- Environment variables
- GPU allocations

Persistence Strategy:
- Auto-snapshot every 5 minutes
- Stream important changes to storage
- On disconnect: attempt recovery for 24 hours
- On provider failure: automatic failover
```

#### 2.6 Workflow Engine
```
Responsibilities:
- Parse/execute visual workflows
- Manage workflow state
- Handle async execution
- Fan-out parallel tasks
- Manage workflow versioning

Implementation:
- GraphQL schema for workflow definition
- Event-driven execution
- Celery for distributed task execution
- Redis for job state
```

#### 2.7 AI Assistant Service
```
Responsibilities:
- Generate environments from prompts
- Suggest optimizations
- Auto-fix errors
- Deploy inference servers
- Orchestrate complex setups

Capabilities:
- LLM integration (OpenAI, Claude, Ollama)
- Container recipe generation (Dockerfile)
- Workflow generation
- Environment variable management
- Dependency resolution
```

#### 2.8 Storage Integration Service
```
Responsibilities:
- Mount S3/MinIO storage
- Manage storage credentials
- Sync datasets
- Checkpoint management
- Cloud storage integration

Supported Backends:
- S3/MinIO (primary)
- Google Drive
- HuggingFace Hub
- Local mounts
```

#### 2.9 Monitoring & Metrics Service
```
Responsibilities:
- Collect GPU metrics (NVIDIA DCGM)
- Track job runtime metrics
- Collect system metrics
- Generate alerts
- Feed metrics to Prometheus

Metrics Collected:
- GPU utilization, temperature, power
- VRAM usage, memory bandwidth
- CPU/memory usage
- Network I/O
- Disk I/O
- Container metrics
```

### Layer 3: Provider Plugin System

**Provider Plugin Architecture**

Each provider implements a standardized TypeScript/Python SDK interface:

```python
class ProviderBase(ABC):
    """Base provider interface"""
    
    @abstractmethod
    async def authenticate(self, credentials: dict) -> bool:
        """Authenticate with provider"""
        pass
    
    @abstractmethod
    async def get_available_gpus(self) -> List[GPU]:
        """List available GPUs"""
        pass
    
    @abstractmethod
    async def provision_session(
        self, 
        session_config: SessionConfig
    ) -> ComputeSession:
        """Provision GPU session"""
        pass
    
    @abstractmethod
    async def get_session_metrics(self, session_id: str) -> Metrics:
        """Get real-time metrics"""
        pass
    
    @abstractmethod
    async def execute_command(
        self, 
        session_id: str, 
        command: str
    ) -> str:
        """Execute command in session"""
        pass
    
    @abstractmethod
    async def checkpoint_session(self, session_id: str) -> str:
        """Save session checkpoint"""
        pass
    
    @abstractmethod
    async def restore_session(self, checkpoint_id: str) -> ComputeSession:
        """Restore from checkpoint"""
        pass
    
    @abstractmethod
    async def terminate_session(self, session_id: str) -> bool:
        """Clean up session"""
        pass
```

**Supported Providers (MVP):**
1. **RunPod** - RunPod API integration
2. **Vast.ai** - Vast.ai API integration
3. **Local Docker** - Docker Compose for local development
4. **Lambda Labs** - Lambda GPU Cloud
5. **Paperspace** - Paperspace Gradient

**Future Providers:**
- Google Colab (API-based)
- Kaggle Notebooks
- AWS SageMaker
- Azure ML
- OVHcloud GPU

### Layer 4: Edge Agent Network

**Edge Agent Deployment**

Lightweight agents deployable on any machine (local PC, homelab, university GPU node).

```
Edge Agent (Go/Python Binary)
├── Agent Manager
│   ├── Self-registration with control plane
│   ├── Health checking & heartbeats
│   └── Secure authentication (mTLS + API keys)
├── Job Executor
│   ├── Docker runtime management
│   ├── Container orchestration
│   └── GPU allocation
├── Metrics Collector
│   ├── GPU metrics (nvidia-smi)
│   ├── System metrics
│   └── Metrics reporting
└── Storage Sync
    ├── Checkpoint syncing
    ├── Dataset management
    └── Output collection
```

**Agent Registration Flow:**
```
1. User installs agent binary (single executable)
2. User runs: `cloud-agent --register --token=<API_TOKEN>`
3. Agent connects to control plane
4. Agent reports capabilities (GPU model, VRAM, CPU cores, disk)
5. Agent appears in provider list as "local-node-<id>"
6. Control plane can schedule workloads to this agent
```

### Layer 5: Kubernetes & Container Orchestration

**Initial Deployment**: Docker Compose
**Target Architecture**: Kubernetes

**K8s Design Principles:**
- Each workspace = isolated namespace
- GPU allocation via device plugin
- Persistent volumes for storage
- Network policies for isolation
- Resource quotas per workspace

```yaml
# Example: Workspace pod in Kubernetes
apiVersion: v1
kind: Pod
metadata:
  name: workspace-user123-python
  namespace: workspace-user123
  labels:
    workspace: user123
    app: ide
spec:
  containers:
  - name: code-server
    image: codercom/code-server:latest
    resources:
      requests:
        nvidia.com/gpu: 1
        memory: "16Gi"
        cpu: "4"
      limits:
        nvidia.com/gpu: 1
        memory: "24Gi"
    volumeMounts:
    - name: workspace-storage
      mountPath: /home/coder/project
  - name: jupyter
    image: jupyter/pytorch-notebook:latest
    resources:
      requests:
        nvidia.com/gpu: 1
  volumes:
  - name: workspace-storage
    persistentVolumeClaim:
      claimName: workspace-pvc
```

## Data Flow Architecture

### Workflow: User Creates GPU Environment from Prompt

```
1. User: "Create Flux fine-tuning environment"
         ↓
2. Frontend sends to /api/assist/generate-env
         ↓
3. AI Assistant Service
   - Call Claude/GPT with system prompt
   - Generate Dockerfile recipe
   - Generate install script
   - Suggest resource requirements
         ↓
4. Backend generates workspace with:
   - Custom Dockerfile
   - Environment variables
   - Storage mounts
   - GPU allocation request
         ↓
5. GPU Scheduler analyzes requirements
   - Needs: RTX 4090 or A100, 20GB VRAM
   - Searches provider inventory
   - Selects best-cost provider (e.g., RunPod)
         ↓
6. Provider Plugin provisions session
   - Creates GPU instance
   - Builds container (Dockerfile)
   - Mounts storage
   - Exposes ports for IDE/Jupyter
         ↓
7. Session Manager creates session record
   - Stores session metadata
   - Sets up checkpoint snapshots
   - Registers with monitoring
         ↓
8. Frontend receives session URL
   - User accesses VSCode IDE
   - User accesses Jupyter
   - Real-time GPU metrics visible in taskbar
         ↓
9. Continuous:
   - Auto-snapshot every 5 minutes
   - Stream metrics via WebSocket
   - Monitor provider health
```

### Workflow: Provider Failure Recovery

```
1. GPU session running, periodic health check fails
         ↓
2. Session Manager detects unhealthy session
   - Mark session as "degraded"
   - Trigger recovery protocol
         ↓
3. Recovery options (in priority order):
   a) Reconnect to same provider (transient error)
   b) Migrate to backup provider
   c) Restore from latest checkpoint
         ↓
4. If migration needed:
   - Load latest checkpoint
   - Select alternative provider
   - Provision new session
   - Restore checkpoint
   - Reroute traffic
         ↓
5. Session restored (user sees brief "reconnecting..." message)
   - Workspace state restored
   - Terminal history preserved
   - Training can resume
```

## Database Schema (PostgreSQL)

### Core Tables

```sql
-- Users
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email VARCHAR UNIQUE NOT NULL,
  oauth_provider VARCHAR NOT NULL,
  oauth_id VARCHAR NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  settings JSONB DEFAULT '{}'
);

-- Workspaces
CREATE TABLE workspaces (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  name VARCHAR NOT NULL,
  description TEXT,
  base_image VARCHAR,  -- Docker image
  environment JSONB,   -- ENV vars
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  deleted_at TIMESTAMP,  -- soft delete
  UNIQUE(user_id, name)
);

-- Workspace Sessions
CREATE TABLE workspace_sessions (
  id UUID PRIMARY KEY,
  workspace_id UUID REFERENCES workspaces(id),
  provider VARCHAR NOT NULL,  -- "runpod", "vastai", etc.
  provider_session_id VARCHAR NOT NULL,
  gpu_model VARCHAR,
  vram_gb INT,
  status VARCHAR,  -- "active", "paused", "recovering", "failed"
  created_at TIMESTAMP DEFAULT NOW(),
  terminated_at TIMESTAMP,
  metadata JSONB  -- provider-specific metadata
);

-- Checkpoints
CREATE TABLE checkpoints (
  id UUID PRIMARY KEY,
  session_id UUID REFERENCES workspace_sessions(id),
  checkpoint_type VARCHAR,  -- "auto", "manual", "error_recovery"
  storage_path VARCHAR NOT NULL,  -- S3/MinIO path
  file_size_bytes BIGINT,
  created_at TIMESTAMP DEFAULT NOW(),
  metadata JSONB
);

-- Workflows
CREATE TABLE workflows (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  name VARCHAR NOT NULL,
  definition JSONB NOT NULL,  -- DAG representation
  version INT DEFAULT 1,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Workflow Runs
CREATE TABLE workflow_runs (
  id UUID PRIMARY KEY,
  workflow_id UUID REFERENCES workflows(id),
  session_id UUID REFERENCES workspace_sessions(id),
  status VARCHAR,  -- "pending", "running", "completed", "failed"
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  result JSONB,
  error_message TEXT
);

-- Provider Credentials
CREATE TABLE provider_credentials (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  provider VARCHAR NOT NULL,
  credentials JSONB NOT NULL,  -- encrypted with key derivation
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Metrics (time-series, typically sharded)
CREATE TABLE metrics (
  timestamp TIMESTAMP NOT NULL,
  session_id UUID NOT NULL,
  metric_type VARCHAR NOT NULL,  -- "gpu_util", "vram", "temp", "power"
  value FLOAT NOT NULL,
  tags JSONB,
  PRIMARY KEY (timestamp, session_id, metric_type)
) PARTITION BY RANGE (timestamp);

-- Audit Log
CREATE TABLE audit_log (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  action VARCHAR NOT NULL,
  resource_type VARCHAR,
  resource_id VARCHAR,
  details JSONB,
  timestamp TIMESTAMP DEFAULT NOW()
);
```

## API Architecture

### RESTful Endpoints (Core)

```
Authentication
POST   /api/v1/auth/login          - OAuth redirect
POST   /api/v1/auth/logout         - Logout & cleanup
GET    /api/v1/auth/me             - Current user info

Workspaces
GET    /api/v1/workspaces          - List workspaces
POST   /api/v1/workspaces          - Create workspace
GET    /api/v1/workspaces/{id}     - Get workspace
PUT    /api/v1/workspaces/{id}     - Update workspace
DELETE /api/v1/workspaces/{id}     - Delete workspace

Sessions
GET    /api/v1/workspaces/{id}/sessions           - List sessions
POST   /api/v1/workspaces/{id}/sessions           - Create session
GET    /api/v1/sessions/{id}                      - Session details
POST   /api/v1/sessions/{id}/checkpoint           - Manual checkpoint
GET    /api/v1/sessions/{id}/metrics              - Historical metrics
POST   /api/v1/sessions/{id}/recover              - Force recovery

Providers
GET    /api/v1/providers            - List provider plugins
POST   /api/v1/providers/auth       - Authenticate provider
GET    /api/v1/providers/{name}/gpus - Available GPUs
DELETE /api/v1/providers/{name}/auth - Revoke provider

Workflows
GET    /api/v1/workflows            - List workflows
POST   /api/v1/workflows            - Create workflow
PUT    /api/v1/workflows/{id}       - Update workflow
POST   /api/v1/workflows/{id}/run   - Execute workflow
GET    /api/v1/workflows/{id}/runs  - List runs
GET    /api/v1/workflow-runs/{id}   - Run status

Storage
GET    /api/v1/storage              - List mounts
POST   /api/v1/storage              - Add S3/storage mount
GET    /api/v1/storage/{id}/list    - List files in mount

AI Assistant
POST   /api/v1/assist/generate-env  - Generate env from prompt
POST   /api/v1/assist/fix-error     - AI error resolution
POST   /api/v1/assist/optimize      - Suggest optimizations
```

### WebSocket Events

```
Client → Server:
- workspace.select              - Switch active workspace
- terminal.input                - Send terminal input
- workflow.step_trigger         - Manually trigger workflow step
- metrics.subscribe             - Subscribe to real-time metrics
- session.checkpoint_request    - Manual checkpoint

Server → Client:
- session.metrics_update        - GPU/CPU metrics (1Hz)
- session.status                - Session status change
- session.checkpoint_complete   - Checkpoint finished
- workflow.step_completed       - Workflow step result
- notification.alert            - System alert
- terminal.output               - Terminal output streaming
```

## Security Architecture

### Authentication Flow

```
1. User clicks "Login with GitHub"
2. Frontend redirects to /api/v1/auth/github
3. Backend exchanges code for access token
4. Backend creates JWT (short-lived: 15 minutes)
5. Backend creates Refresh Token (long-lived: 30 days)
6. Refresh Token stored in HttpOnly cookie
7. JWT returned in response body
8. Frontend stores JWT in memory (not localStorage)
9. Frontend includes JWT in Authorization header

Refresh Token Rotation:
- On each JWT refresh, issue new Refresh Token
- Invalidate old Refresh Token
- Revoke compromised tokens immediately
```

### Secret Management

```
Provider Credentials:
1. User enters API key for RunPod
2. Backend encrypts with user-specific key derivation
3. Store encrypted blob in database
4. On use: decrypt in-process
5. Never log credentials

Encryption:
- Algorithm: AES-256-GCM
- Key derivation: PBKDF2 with user salt
- IV: randomly generated per encryption
```

### Network Security

```
- All communication: TLS 1.3
- CORS: Restricted to frontend domain
- CSRF: Token-based protection
- Rate limiting: Per-user, per-endpoint
- Request signing: Optional for provider APIs
```

## Performance Optimization

### Caching Strategy

```
Redis Cache:
- Provider GPU inventory (5 min TTL)
- Workspace state (real-time update)
- User settings (24 hour TTL)
- Authentication tokens (varies by type)

Frontend Caching:
- API responses (React Query with intelligent invalidation)
- DOM state (Zustand stores)
- Large datasets (IndexedDB for local storage)
```

### Scalability Design

```
Horizontal Scaling:
- Stateless FastAPI instances (behind load balancer)
- Database read replicas for queries
- Redis cluster for distributed caching
- Separate worker pool for Celery tasks

Bottleneck Analysis:
1. Database queries → connection pooling, indexing, read replicas
2. Provider API latency → parallel requests, circuit breakers
3. GPU availability → intelligent scheduling, cost optimization
4. Network bandwidth → compression, chunked transfers
```

## Deployment Architecture

### Development Environment

```
Docker Compose Stack:
- PostgreSQL container
- Redis container
- MinIO container (S3 mock)
- FastAPI backend
- Next.js frontend
- code-server container
```

### Production Environment

```
Kubernetes Cluster:
- Frontend (Next.js): 2-3 replicas
- Backend API: 3-5 replicas
- Worker pool: 2-10 replicas (Celery)
- PostgreSQL (managed DB)
- Redis cluster (managed)
- MinIO cluster (or S3)
- Monitoring: Prometheus + Grafana
- Ingress: nginx-ingress with cert-manager
```

## Monitoring & Observability

### Metrics Stack

```
Collection:
- Prometheus agents on each component
- NVIDIA DCGM for GPU metrics
- cAdvisor for container metrics

Storage:
- Prometheus time-series DB (2-week retention)
- Long-term: S3/InfluxDB

Visualization:
- Grafana dashboards
- Frontend real-time metrics display
```

### Logging Stack

```
Collection:
- Structured JSON logging (FastAPI middleware)
- Centralized logging (ELK or Loki)

Retention:
- Application logs: 30 days
- Audit logs: 1 year
- Debug logs: 7 days
```

## Technical Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Provider API unavailability | Session loss | Multi-provider failover, checkpoint recovery |
| Network partition | Workspace isolation | Local-first caching, graceful degradation |
| GPU shortage | Failed scheduling | Cost prediction, queue management, fallback providers |
| User data loss | Privacy/compliance | Encrypted storage, backup redundancy, audit logs |
| Kubernetes complexity | Operations overhead | Start with Docker Compose, gradual migration |
| Cold start latency | Poor UX | Caching, preallocation, background startup |

## Next Steps

1. Proceed to [Frontend Architecture](01-FRONTEND_ARCHITECTURE.md)
2. Proceed to [Backend Architecture](02-BACKEND_ARCHITECTURE.md)
3. Review [Database Schema Design](../design/DATABASE_SCHEMA.md)
4. Review [Security Architecture](../design/SECURITY_ARCHITECTURE.md)
5. See [MVP Roadmap](../operations/MVP_ROADMAP.md)
