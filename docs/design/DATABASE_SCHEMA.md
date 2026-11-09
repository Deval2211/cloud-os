# Database Schema Design

**Document**: PostgreSQL Schema & Data Model
**Version**: 1.0
**Status**: Design Phase

## Overview

The database uses PostgreSQL as the primary data store. All tables are designed for:
- Multi-tenant safety (row-level security potential)
- Efficient querying (proper indexing)
- Time-series support (partitioned metrics table)
- Soft deletes (audit trail)

## Core Tables

### Users Table

```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  oauth_provider VARCHAR(50) NOT NULL,  -- 'github', 'google'
  oauth_id VARCHAR(255) NOT NULL,
  oauth_email VARCHAR(255),
  name VARCHAR(255),
  avatar_url TEXT,
  
  -- User settings
  settings JSONB DEFAULT '{}',  -- theme, notifications, etc.
  
  -- Account status
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_login_at TIMESTAMP,
  
  CONSTRAINT unique_oauth UNIQUE(oauth_provider, oauth_id)
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created_at ON users(created_at);
```

### Workspaces Table

```sql
CREATE TABLE workspaces (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  
  -- Metadata
  name VARCHAR(255) NOT NULL,
  description TEXT,
  
  -- Docker configuration
  base_image VARCHAR(255) DEFAULT 'python:3.11',
  dockerfile TEXT,  -- Optional custom Dockerfile
  
  -- Environment
  environment JSONB DEFAULT '{}',  -- {'KEY': 'value', ...}
  
  -- Settings
  auto_checkpoint_enabled BOOLEAN DEFAULT true,
  checkpoint_interval_minutes INT DEFAULT 5,
  
  -- Timestamps
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  deleted_at TIMESTAMP,  -- Soft delete
  
  CONSTRAINT unique_workspace_name UNIQUE(user_id, name),
  CONSTRAINT name_not_empty CHECK(length(name) > 0)
);

CREATE INDEX idx_workspaces_user_id ON workspaces(user_id);
CREATE INDEX idx_workspaces_deleted_at ON workspaces(deleted_at);
CREATE INDEX idx_workspaces_created_at ON workspaces(created_at);
```

### Workspace Sessions Table

```sql
CREATE TABLE workspace_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  
  -- Provider information
  provider VARCHAR(50) NOT NULL,  -- 'runpod', 'vastai', 'lambda_labs', etc.
  provider_session_id VARCHAR(255) NOT NULL,  -- External provider's session ID
  
  -- GPU Information
  gpu_model VARCHAR(50),  -- 'RTX 4090', 'A100', etc.
  vram_gb INT,
  cuda_version VARCHAR(20),  -- '12.4', '11.8', etc.
  
  -- Session state
  status VARCHAR(50) DEFAULT 'active',  -- 'active', 'paused', 'recovering', 'failed', 'terminated'
  
  -- Endpoints
  ide_url TEXT,  -- VSCode Server URL
  jupyter_url TEXT,  -- Jupyter URL
  ssh_host VARCHAR(255),
  ssh_port INT,
  
  -- Performance
  hourly_cost_cents INT,  -- Cost in cents per hour
  
  -- Timestamps
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  started_at TIMESTAMP,
  last_heartbeat_at TIMESTAMP,
  terminated_at TIMESTAMP,
  
  -- Metadata
  metadata JSONB DEFAULT '{}',  -- Provider-specific data
  
  CONSTRAINT provider_session_unique UNIQUE(provider, provider_session_id)
);

CREATE INDEX idx_sessions_workspace_id ON workspace_sessions(workspace_id);
CREATE INDEX idx_sessions_status ON workspace_sessions(status);
CREATE INDEX idx_sessions_provider ON workspace_sessions(provider);
CREATE INDEX idx_sessions_created_at ON workspace_sessions(created_at);
CREATE INDEX idx_sessions_last_heartbeat ON workspace_sessions(last_heartbeat_at);
```

### Checkpoints Table

```sql
CREATE TABLE checkpoints (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES workspace_sessions(id) ON DELETE CASCADE,
  
  -- Checkpoint metadata
  checkpoint_type VARCHAR(50) NOT NULL,  -- 'auto', 'manual', 'error_recovery'
  name VARCHAR(255),  -- Optional user-given name
  description TEXT,
  
  -- Storage
  storage_path VARCHAR(255) NOT NULL,  -- S3/MinIO path
  file_size_bytes BIGINT,
  
  -- Status
  status VARCHAR(50) DEFAULT 'completed',  -- 'pending', 'completed', 'failed'
  error_message TEXT,
  
  -- Versioning
  version INT,
  
  -- Timestamps
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  expires_at TIMESTAMP,  -- Auto-cleanup after expiry
  
  metadata JSONB DEFAULT '{}'  -- Additional metadata
);

CREATE INDEX idx_checkpoints_session_id ON checkpoints(session_id);
CREATE INDEX idx_checkpoints_created_at ON checkpoints(created_at);
CREATE INDEX idx_checkpoints_status ON checkpoints(status);
CREATE INDEX idx_checkpoints_expires_at ON checkpoints(expires_at);
```

### Workflows Table

```sql
CREATE TABLE workflows (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  
  -- Metadata
  name VARCHAR(255) NOT NULL,
  description TEXT,
  category VARCHAR(100),  -- 'training', 'inference', 'preprocessing', etc.
  
  -- Workflow definition
  definition JSONB NOT NULL,  -- DAG representation
  
  -- Versioning
  version INT DEFAULT 1,
  is_published BOOLEAN DEFAULT false,
  
  -- Execution settings
  default_session_config JSONB,  -- GPU requirements, etc.
  
  -- Timestamps
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  published_at TIMESTAMP,
  deleted_at TIMESTAMP
);

CREATE INDEX idx_workflows_user_id ON workflows(user_id);
CREATE INDEX idx_workflows_category ON workflows(category);
CREATE INDEX idx_workflows_is_published ON workflows(is_published);
```

### Workflow Runs Table

```sql
CREATE TABLE workflow_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  workflow_id UUID NOT NULL REFERENCES workflows(id),
  session_id UUID REFERENCES workspace_sessions(id),
  
  -- Execution state
  status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'running', 'completed', 'failed', 'cancelled'
  
  -- Results
  result JSONB,  -- Output from final node
  error_message TEXT,
  error_traceback TEXT,
  
  -- Execution timeline
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  runtime_seconds INT,
  
  -- Metadata
  triggered_by VARCHAR(50),  -- 'user', 'schedule', 'api'
  
  -- Timestamps
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_workflow_runs_workflow_id ON workflow_runs(workflow_id);
CREATE INDEX idx_workflow_runs_session_id ON workflow_runs(session_id);
CREATE INDEX idx_workflow_runs_status ON workflow_runs(status);
CREATE INDEX idx_workflow_runs_created_at ON workflow_runs(created_at);
```

### Provider Credentials Table

```sql
CREATE TABLE provider_credentials (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  
  -- Provider info
  provider VARCHAR(50) NOT NULL,  -- 'runpod', 'vastai', etc.
  provider_user_id VARCHAR(255),  -- Account ID at provider
  
  -- Encrypted credentials
  credentials_encrypted BYTEA NOT NULL,  -- AES-256-GCM encrypted
  encryption_iv BYTEA NOT NULL,  -- IV for encryption
  
  -- Metadata
  is_active BOOLEAN DEFAULT true,
  last_verified_at TIMESTAMP,
  
  -- Timestamps
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  CONSTRAINT unique_provider_per_user UNIQUE(user_id, provider)
);

CREATE INDEX idx_credentials_user_id ON provider_credentials(user_id);
CREATE INDEX idx_credentials_provider ON provider_credentials(provider);
```

### Metrics Table (Time-Series - Partitioned)

```sql
CREATE TABLE metrics (
  timestamp TIMESTAMP NOT NULL,
  session_id UUID NOT NULL,
  
  -- Metric type
  metric_type VARCHAR(50) NOT NULL,  -- 'gpu_util', 'vram', 'temp', 'power', 'cpu', 'memory', 'disk_io'
  
  -- Value
  value FLOAT NOT NULL,
  
  -- Metadata
  tags JSONB,  -- {'device': 'gpu:0', 'worker': 'node-1', ...}
  
  PRIMARY KEY (timestamp, session_id, metric_type)
) PARTITION BY RANGE (timestamp);

-- Create partitions (monthly)
CREATE TABLE metrics_2026_05 PARTITION OF metrics
  FOR VALUES FROM ('2026-05-01') TO ('2026-06-01');

CREATE TABLE metrics_2026_06 PARTITION OF metrics
  FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');

-- ... more partitions

CREATE INDEX idx_metrics_session_timestamp ON metrics (session_id, timestamp DESC);
```

### Audit Log Table

```sql
CREATE TABLE audit_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  
  -- Action information
  action VARCHAR(100) NOT NULL,  -- 'workspace.created', 'session.started', etc.
  resource_type VARCHAR(50),  -- 'workspace', 'session', 'workflow'
  resource_id UUID,
  
  -- Details
  details JSONB,
  ip_address INET,
  user_agent TEXT,
  
  -- Timestamp
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_resource ON audit_log(resource_type, resource_id);
CREATE INDEX idx_audit_action ON audit_log(action);
CREATE INDEX idx_audit_timestamp ON audit_log(created_at);
```

### Refresh Tokens Table

```sql
CREATE TABLE refresh_tokens (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  
  -- Token
  token_hash VARCHAR(255) NOT NULL UNIQUE,  -- SHA256 hash
  
  -- Validity
  expires_at TIMESTAMP NOT NULL,
  revoked_at TIMESTAMP,  -- NULL if not revoked
  
  -- Metadata
  ip_address INET,
  user_agent TEXT,
  
  -- Timestamps
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_expires_at ON refresh_tokens(expires_at);
```

### Storage Mounts Table

```sql
CREATE TABLE storage_mounts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  
  -- Mount information
  name VARCHAR(255) NOT NULL,
  storage_type VARCHAR(50) NOT NULL,  -- 's3', 'gcs', 'azure_blob', 'huggingface'
  
  -- Credentials (encrypted)
  credentials_encrypted BYTEA,
  encryption_iv BYTEA,
  
  -- Configuration
  config JSONB,  -- {'bucket': 'my-bucket', 'region': 'us-east-1', ...}
  
  -- Status
  is_active BOOLEAN DEFAULT true,
  
  -- Timestamps
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  CONSTRAINT unique_storage_name UNIQUE(user_id, name)
);

CREATE INDEX idx_storage_mounts_user_id ON storage_mounts(user_id);
```

## SQLAlchemy ORM Models

```python
# models/user.py
from sqlalchemy import Column, String, Boolean, DateTime, func
from db.base import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    oauth_provider = Column(String(50), nullable=False)
    oauth_id = Column(String(255), nullable=False)
    name = Column(String(255))
    avatar_url = Column(String)
    settings = Column(JSON, default={})
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime)
    
    # Relationships
    workspaces = relationship("Workspace", back_populates="user")
    workflows = relationship("Workflow", back_populates="user")
    credentials = relationship("ProviderCredentials", back_populates="user")

# models/workspace.py
class Workspace(Base):
    __tablename__ = "workspaces"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String)
    base_image = Column(String(255), default="python:3.11")
    dockerfile = Column(String)
    environment = Column(JSON, default={})
    auto_checkpoint_enabled = Column(Boolean, default=True)
    checkpoint_interval_minutes = Column(Integer, default=5)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    deleted_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="workspaces")
    sessions = relationship("WorkspaceSession", back_populates="workspace")

# models/session.py
class WorkspaceSession(Base):
    __tablename__ = "workspace_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True)
    provider = Column(String(50), nullable=False, index=True)
    provider_session_id = Column(String(255), nullable=False)
    gpu_model = Column(String(50))
    vram_gb = Column(Integer)
    cuda_version = Column(String(20))
    status = Column(String(50), default="active", index=True)
    ide_url = Column(String)
    jupyter_url = Column(String)
    ssh_host = Column(String(255))
    ssh_port = Column(Integer)
    hourly_cost_cents = Column(Integer)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    last_heartbeat_at = Column(DateTime, index=True)
    terminated_at = Column(DateTime)
    metadata = Column(JSON, default={})
    
    # Relationships
    workspace = relationship("Workspace", back_populates="sessions")
    checkpoints = relationship("Checkpoint", back_populates="session")
```

## Migration Strategy (Alembic)

```bash
# Generate migration
alembic revision --autogenerate -m "Add users and workspaces tables"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Performance Considerations

### Query Optimization

```sql
-- Get active sessions with latest metrics
SELECT s.*, 
       (SELECT value FROM metrics 
        WHERE session_id = s.id AND metric_type = 'gpu_util'
        ORDER BY timestamp DESC LIMIT 1) as gpu_util
FROM workspace_sessions s
WHERE s.status = 'active'
LIMIT 10;

-- Use connection pooling in backend
# config.py
DATABASE_POOL_SIZE = 20
DATABASE_MAX_OVERFLOW = 0
```

### Partitioning Strategy

- Metrics table: Monthly partitions (auto-create)
- Archive old metrics to S3 after 90 days
- Keep only 2-week retention in hot storage

### Backup & Recovery

```bash
# Daily backup to S3
pg_dump cloud_os_db | gzip | aws s3 cp - s3://backups/cloud-os/$(date +%Y%m%d).sql.gz

# Recovery
aws s3 cp s3://backups/cloud-os/YYYYMMDD.sql.gz - | gunzip | psql cloud_os_db
```

## Next Steps

- See [API Specifications](../api/API_SPECIFICATIONS.md)
- Review [Backend Architecture](../architecture/02-BACKEND_ARCHITECTURE.md)
