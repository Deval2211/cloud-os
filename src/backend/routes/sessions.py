"""
GPU session management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import uuid

from auth.db import get_db_session, get_current_user
from models import User, WorkspaceSession, Workspace
from websocket.manager import manager, EventType, WebSocketEvent
from tasks import provision_gpu_session, monitor_session_metrics

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["sessions"])


class SessionService:
    """Service for managing GPU sessions"""

    @staticmethod
    def create_session(
        db: Session,
        workspace_id: str,
        user_id: str,
        provider: str,
        provider_session_id: str,
        config: dict | None = None,
    ) -> WorkspaceSession:
        """Create a new GPU session"""
        session = WorkspaceSession(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            user_id=user_id,
            provider=provider,
            provider_session_id=provider_session_id,
            status="pending",
            session_config=config or {},
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def get_session(db: Session, session_id: str) -> WorkspaceSession | None:
        """Get session by ID"""
        return db.query(WorkspaceSession).filter(
            WorkspaceSession.id == session_id
        ).first()

    @staticmethod
    def get_workspace_sessions(db: Session, workspace_id: str):
        """Get all sessions for a workspace"""
        return db.query(WorkspaceSession).filter(
            WorkspaceSession.workspace_id == workspace_id,
            WorkspaceSession.status != "deleted",
        ).all()

    @staticmethod
    def update_session_status(
        db: Session,
        session: WorkspaceSession,
        status: str,
        **kwargs
    ) -> WorkspaceSession:
        """Update session status"""
        session.status = status
        for key, value in kwargs.items():
            if hasattr(session, key):
                setattr(session, key, value)

        session.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def terminate_session(db: Session, session: WorkspaceSession) -> WorkspaceSession:
        """Terminate a session"""
        session.status = "stopped"
        session.terminated_at = datetime.utcnow()
        db.commit()
        db.refresh(session)
        return session


# Request/Response Schemas
from pydantic import BaseModel


class SessionCreate(BaseModel):
    """Create session request"""
    workspace_id: str
    provider: str = "local_docker"  # local_docker, runpod, vast.ai
    gpu_type: str | None = None  # RTX 4090, A100, etc.
    memory_gb: int = 16  # GPU memory in GB
    timeout_hours: int = 1


class SessionResponse(BaseModel):
    """Session response"""
    id: str
    workspace_id: str
    provider: str
    status: str
    created_at: str
    updated_at: str
    config: dict

    class Config:
        from_attributes = True


# Endpoints

@router.post("/workspaces/{workspace_id}/sessions", response_model=SessionResponse)
async def start_session(
    workspace_id: str,
    session_create: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """
    Start a new GPU session
    
    Query Parameters:
    - workspace_id: Workspace ID
    
    Request Body:
    - provider: GPU provider (local_docker, runpod, vast.ai)
    - gpu_type: GPU type (optional)
    - memory_gb: GPU memory in GB
    - timeout_hours: Session timeout
    
    Returns: New session details
    """
    # Verify workspace exists and user owns it
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.owner_id == current_user.id,
    ).first()

    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Create session
    session = SessionService.create_session(
        db=db,
        workspace_id=workspace_id,
        user_id=current_user.id,
        provider=session_create.provider,
        provider_session_id=f"{session_create.provider}-{uuid.uuid4().hex[:8]}",
        config={
            "gpu_type": session_create.gpu_type,
            "memory_gb": session_create.memory_gb,
            "timeout_hours": session_create.timeout_hours,
        },
    )

    # Emit session.started event
    event = WebSocketEvent(
        event_type=EventType.SESSION_STARTED,
        data={
            "session_id": session.id,
            "provider": session.provider,
            "status": "pending",
            "gpu_type": session_create.gpu_type,
        },
        user_id=current_user.id,
        workspace_id=workspace_id,
        session_id=session.id,
    )

    # Broadcast event (async, don't wait)
    import asyncio
    try:
        asyncio.create_task(
            manager.broadcast_to_workspace(workspace_id, event)
        )
    except:
        pass  # Event broadcasting is best-effort
    
    # Trigger async provisioning task
    provision_gpu_session.delay(
        workspace_id=workspace_id,
        session_id=session.id,
        provider=session_create.provider,
        config={
            "gpu_type": session_create.gpu_type,
            "memory_gb": session_create.memory_gb,
            "timeout_hours": session_create.timeout_hours,
        },
    )
    
    # Schedule periodic metrics collection
    monitor_session_metrics.apply_async(
        args=[session.id],
        countdown=30,  # Start after 30 seconds
    )

    logger.info(f"Session {session.id} created by user {current_user.id}")

    return SessionResponse.from_orm(session)


@router.get("/workspaces/{workspace_id}/sessions", response_model=list[SessionResponse])
async def list_sessions(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """
    List all sessions in a workspace
    
    Query Parameters:
    - workspace_id: Workspace ID
    
    Returns: List of sessions
    """
    # Verify workspace exists and user owns it
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.owner_id == current_user.id,
    ).first()

    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    sessions = SessionService.get_workspace_sessions(db, workspace_id)
    return [SessionResponse.from_orm(s) for s in sessions]


@router.get("/workspaces/{workspace_id}/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    workspace_id: str,
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """
    Get session details
    
    Query Parameters:
    - workspace_id: Workspace ID
    - session_id: Session ID
    
    Returns: Session details
    """
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

    return SessionResponse.from_orm(session)


@router.post("/workspaces/{workspace_id}/sessions/{session_id}/stop")
async def stop_session(
    workspace_id: str,
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """
    Stop a running GPU session
    
    Query Parameters:
    - workspace_id: Workspace ID
    - session_id: Session ID
    
    Returns: Updated session details
    """
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

    # Stop session
    SessionService.terminate_session(db, session)

    # Emit session.stopped event
    event = WebSocketEvent(
        event_type=EventType.SESSION_STOPPED,
        data={
            "session_id": session.id,
            "duration_seconds": int(
                (session.terminated_at - session.created_at).total_seconds()
            ),
            "cost": session.cost_estimate,
        },
        user_id=current_user.id,
        workspace_id=workspace_id,
        session_id=session.id,
    )

    import asyncio
    try:
        asyncio.create_task(
            manager.broadcast_to_workspace(workspace_id, event)
        )
    except:
        pass

    logger.info(f"Session {session.id} stopped by user {current_user.id}")

    return {"message": "Session stopped", "session": SessionResponse.from_orm(session)}


@router.get("/workspaces/{workspace_id}/sessions/{session_id}/logs")
async def get_session_logs(
    workspace_id: str,
    session_id: str,
    lines: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """
    Get session logs
    
    Query Parameters:
    - workspace_id: Workspace ID
    - session_id: Session ID
    - lines: Number of log lines to return
    
    Returns: Log lines
    """
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

    # Return placeholder logs
    return {
        "session_id": session.id,
        "logs": [
            f"[2024-01-15 10:30:{i:02d}] Session initialized",
            f"[2024-01-15 10:30:05] GPU allocated: {session.config.get('gpu_type', 'Unknown')}",
            "[2024-01-15 10:30:10] Environment ready",
        ],
    }
