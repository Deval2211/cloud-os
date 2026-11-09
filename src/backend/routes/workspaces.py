"""
Workspace routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid
import logging

from models import Workspace, User
from auth.routes import get_current_user
from auth.db import get_db_session
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/workspaces", tags=["workspaces"])


class WorkspaceService:
    """Service for workspace operations"""

    @staticmethod
    def create_workspace(
        db: Session, owner: User, name: str, description: str | None = None
    ) -> Workspace:
        """Create a new workspace"""
        workspace = Workspace(
            id=str(uuid.uuid4()),
            owner_id=owner.id,
            name=name,
            description=description,
            config={},
            is_active=True,
        )
        db.add(workspace)
        db.commit()
        db.refresh(workspace)
        logger.info(f"Created workspace {workspace.id} for user {owner.id}")
        return workspace

    @staticmethod
    def get_workspace(db: Session, workspace_id: str) -> Workspace | None:
        """Get workspace by ID"""
        return db.query(Workspace).filter(Workspace.id == workspace_id).first()

    @staticmethod
    def get_user_workspaces(db: Session, owner_id: str) -> List[Workspace]:
        """Get all workspaces for a user"""
        return db.query(Workspace).filter(
            Workspace.owner_id == owner_id,
            Workspace.is_active == True
        ).all()

    @staticmethod
    def update_workspace(
        db: Session, workspace: Workspace, **kwargs
    ) -> Workspace:
        """Update workspace fields"""
        for key, value in kwargs.items():
            if hasattr(workspace, key):
                setattr(workspace, key, value)

        workspace.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(workspace)
        return workspace

    @staticmethod
    def delete_workspace(db: Session, workspace: Workspace) -> None:
        """Delete workspace (soft delete)"""
        workspace.is_active = False
        workspace.updated_at = datetime.utcnow()
        db.commit()
        logger.info(f"Deleted workspace {workspace.id}")


# Pydantic schemas
from pydantic import BaseModel, Field
from typing import Optional


class WorkspaceCreate(BaseModel):
    """Create workspace request"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class WorkspaceUpdate(BaseModel):
    """Update workspace request"""
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[dict] = None


class WorkspaceResponse(BaseModel):
    """Workspace response"""
    id: str
    owner_id: str
    name: str
    description: Optional[str]
    config: dict
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Routes


@router.post("", response_model=WorkspaceResponse)
async def create_workspace(
    request: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> WorkspaceResponse:
    """Create a new workspace"""
    try:
        workspace = WorkspaceService.create_workspace(
            db,
            current_user,
            request.name,
            request.description,
        )
        return WorkspaceResponse.from_orm(workspace)
    except Exception as e:
        logger.error(f"Error creating workspace: {e}")
        raise HTTPException(status_code=500, detail="Failed to create workspace")


@router.get("", response_model=List[WorkspaceResponse])
async def get_workspaces(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> List[WorkspaceResponse]:
    """Get all workspaces for current user"""
    try:
        workspaces = WorkspaceService.get_user_workspaces(db, current_user.id)
        return [WorkspaceResponse.from_orm(w) for w in workspaces]
    except Exception as e:
        logger.error(f"Error fetching workspaces: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch workspaces")


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> WorkspaceResponse:
    """Get specific workspace"""
    try:
        workspace = WorkspaceService.get_workspace(db, workspace_id)

        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")

        # Check ownership
        if workspace.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        return WorkspaceResponse.from_orm(workspace)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching workspace: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch workspace")


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: str,
    request: WorkspaceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> WorkspaceResponse:
    """Update workspace"""
    try:
        workspace = WorkspaceService.get_workspace(db, workspace_id)

        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")

        # Check ownership
        if workspace.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        update_data = request.dict(exclude_unset=True)
        workspace = WorkspaceService.update_workspace(db, workspace, **update_data)

        return WorkspaceResponse.from_orm(workspace)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating workspace: {e}")
        raise HTTPException(status_code=500, detail="Failed to update workspace")


@router.delete("/{workspace_id}")
async def delete_workspace(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> dict:
    """Delete workspace"""
    try:
        workspace = WorkspaceService.get_workspace(db, workspace_id)

        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")

        # Check ownership
        if workspace.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        WorkspaceService.delete_workspace(db, workspace)

        return {"message": "Workspace deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting workspace: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete workspace")
