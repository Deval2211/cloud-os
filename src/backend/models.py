"""
SQLAlchemy database models for Cloud OS
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON, Enum as SQLEnum, Index, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid

Base = declarative_base()


class User(Base):
    """User model - Authentication and profile"""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    github_id = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(255))
    avatar_url = Column(Text)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    workspaces = relationship("Workspace", back_populates="owner")
    provider_credentials = relationship("ProviderCredentials", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")
    refresh_tokens = relationship("RefreshToken", back_populates="user")

    __table_args__ = (
        Index("idx_github_id", "github_id"),
        Index("idx_email", "email"),
    )


class Workspace(Base):
    """Workspace model - Project container"""
    __tablename__ = "workspaces"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    config = Column(JSON, default={})
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="workspaces")
    sessions = relationship("WorkspaceSession", back_populates="workspace")
    workflows = relationship("Workflow", back_populates="workspace")
    checkpoints = relationship("Checkpoint", back_populates="workspace")

    __table_args__ = (
        Index("idx_owner_id", "owner_id"),
        UniqueConstraint("owner_id", "name", name="uq_workspace_owner_name"),
    )


class WorkspaceSession(Base):
    """GPU Session model - Active compute sessions"""
    __tablename__ = "workspace_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    provider = Column(String(50), nullable=False)  # runpod, vastai, etc.
    provider_session_id = Column(String(255), nullable=False)
    status = Column(String(50), default="pending")  # pending, running, stopped, error
    gpu_type = Column(String(100))
    gpu_count = Column(Integer, default=1)
    memory_gb = Column(Integer)
    hourly_rate = Column(Float)
    current_cost = Column(Float, default=0.0)
    session_config = Column(JSON, default={})
    started_at = Column(DateTime)
    ended_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    workspace = relationship("Workspace", back_populates="sessions")
    user = relationship("User")
    checkpoints = relationship("Checkpoint", back_populates="session")
    metrics = relationship("Metrics", back_populates="session")

    __table_args__ = (
        Index("idx_workspace_id", "workspace_id"),
        Index("idx_provider_session_id", "provider_session_id"),
        Index("idx_status", "status"),
    )


class Checkpoint(Base):
    """Checkpoint model - Session snapshots for recovery"""
    __tablename__ = "checkpoints"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False)
    session_id = Column(String(36), ForeignKey("workspace_sessions.id"), nullable=False)
    checkpoint_type = Column(String(50), default="auto")  # auto, manual, critical
    s3_path = Column(String(500), nullable=False)
    size_bytes = Column(Integer)
    checkpoint_data = Column(JSON)
    is_latest = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)

    # Relationships
    workspace = relationship("Workspace", back_populates="checkpoints")
    session = relationship("WorkspaceSession", back_populates="checkpoints")

    __table_args__ = (
        Index("idx_workspace_id", "workspace_id"),
        Index("idx_session_id", "session_id"),
        Index("idx_is_latest", "is_latest"),
    )


class Workflow(Base):
    """Workflow model - DAG definitions"""
    __tablename__ = "workflows"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    definition = Column(JSON, nullable=False)  # DAG structure
    is_active = Column(Boolean, default=True)
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    workspace = relationship("Workspace", back_populates="workflows")
    user = relationship("User")
    runs = relationship("WorkflowRun", back_populates="workflow")

    __table_args__ = (
        Index("idx_workspace_id", "workspace_id"),
    )


class WorkflowRun(Base):
    """Workflow Run model - Execution history"""
    __tablename__ = "workflow_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id = Column(String(36), ForeignKey("workflows.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    execution_log = Column(JSON, default={})
    result = Column(JSON)
    error_message = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    workflow = relationship("Workflow", back_populates="runs")
    user = relationship("User")

    __table_args__ = (
        Index("idx_workflow_id", "workflow_id"),
        Index("idx_status", "status"),
    )


class ProviderCredentials(Base):
    """Provider Credentials model - Encrypted auth for GPU providers"""
    __tablename__ = "provider_credentials"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    provider = Column(String(50), nullable=False)  # runpod, vastai, etc.
    encrypted_credentials = Column(Text, nullable=False)  # AES-256-GCM encrypted
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="provider_credentials")

    __table_args__ = (
        Index("idx_user_id_provider", "user_id", "provider"),
        UniqueConstraint("user_id", "provider", name="uq_user_provider_cred"),
    )


class Metrics(Base):
    """Metrics model - Time-series metrics for sessions"""
    __tablename__ = "metrics"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("workspace_sessions.id"), nullable=False, index=True)
    metric_type = Column(String(50), nullable=False)  # gpu_usage, memory, temperature, etc.
    value = Column(Float, nullable=False)
    unit = Column(String(50))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    session = relationship("WorkspaceSession", back_populates="metrics")

    __table_args__ = (
        Index("idx_session_metric_timestamp", "session_id", "metric_type", "timestamp"),
    )


class AuditLog(Base):
    """Audit Log model - Compliance and security auditing"""
    __tablename__ = "audit_log"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"))
    action = Column(String(255), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(255))
    changes = Column(JSON, default={})
    ip_address = Column(String(45))
    user_agent = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    __table_args__ = (
        Index("idx_user_id_action", "user_id", "action"),
        Index("idx_created_at", "created_at"),
    )


class RefreshToken(Base):
    """Refresh Token model - Token rotation for security"""
    __tablename__ = "refresh_tokens"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    token_hash = Column(String(255), unique=True, nullable=False)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)

    # Relationships
    user = relationship("User", back_populates="refresh_tokens")

    __table_args__ = (
        Index("idx_user_id", "user_id"),
        Index("idx_expires_at", "expires_at"),
    )


class StorageMount(Base):
    """Storage Mount model - External storage integrations"""
    __tablename__ = "storage_mounts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False)
    storage_type = Column(String(50), nullable=False)  # s3, gcs, huggingface, etc.
    mount_name = Column(String(255), nullable=False)
    mount_path = Column(String(500))
    credentials_encrypted = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_workspace_id", "workspace_id"),
    )
