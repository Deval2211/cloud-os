"""
Checkpoint Service - Session persistence and recovery
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from models import Checkpoint, WorkspaceSession
from provider_sdk import provider_registry

logger = logging.getLogger(__name__)


class CheckpointService:
    """Manages session checkpoints and recovery"""
    
    @staticmethod
    async def create_checkpoint(
        db: Session,
        session_id: str,
        checkpoint_name: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Create a checkpoint for a session.
        
        Args:
            db: Database session
            session_id: Session ID
            checkpoint_name: Human-readable checkpoint name
        
        Returns:
            Checkpoint data or None if failed
        """
        try:
            session = db.query(WorkspaceSession).filter(
                WorkspaceSession.id == session_id
            ).first()
            
            if not session:
                logger.error(f"Session {session_id} not found")
                return None
            
            if session.status != "running":
                logger.warning(f"Session {session_id} is not running")
                return None
            
            # Get provider
            provider = provider_registry.get_provider(session.provider)
            if not provider:
                logger.error(f"Provider {session.provider} not found")
                return None
            
            # Create checkpoint on provider
            checkpoint_data = await provider.create_checkpoint(
                session.provider_session_id,
                checkpoint_name
            )
            
            # Store in database
            checkpoint = Checkpoint(
                session_id=session_id,
                name=checkpoint_name,
                storage_path=checkpoint_data.get("storage_path"),
                checkpoint_id=checkpoint_data.get("checkpoint_id"),
                size_gb=0,  # Would measure actual size
                created_at=datetime.utcnow(),
            )
            
            db.add(checkpoint)
            db.commit()
            db.refresh(checkpoint)
            
            logger.info(f"Created checkpoint {checkpoint.id}")
            
            return {
                "id": checkpoint.id,
                "name": checkpoint.name,
                "checkpoint_id": checkpoint.checkpoint_id,
                "storage_path": checkpoint.storage_path,
                "created_at": checkpoint.created_at.isoformat(),
            }
        
        except Exception as e:
            logger.error(f"Failed to create checkpoint: {e}")
            return None
    
    @staticmethod
    async def restore_checkpoint(
        db: Session,
        checkpoint_id: str,
    ) -> Optional[WorkspaceSession]:
        """
        Restore a session from checkpoint.
        
        Args:
            db: Database session
            checkpoint_id: Checkpoint ID
        
        Returns:
            Restored session or None
        """
        try:
            checkpoint = db.query(Checkpoint).filter(
                Checkpoint.id == checkpoint_id
            ).first()
            
            if not checkpoint:
                logger.error(f"Checkpoint {checkpoint_id} not found")
                return None
            
            # Get original session
            original_session = db.query(WorkspaceSession).filter(
                WorkspaceSession.id == checkpoint.session_id
            ).first()
            
            if not original_session:
                logger.error(f"Original session not found")
                return None
            
            # Get provider
            provider = provider_registry.get_provider(original_session.provider)
            if not provider:
                logger.error(f"Provider not found")
                return None
            
            # Restore from provider
            restored_compute_session = await provider.restore_session(
                checkpoint.checkpoint_id
            )
            
            # Create new session record
            new_session = WorkspaceSession(
                workspace_id=original_session.workspace_id,
                user_id=original_session.user_id,
                provider=original_session.provider,
                provider_session_id=restored_compute_session.id,
                status="running",
                gpu_type=restored_compute_session.gpu.model,
                memory_gb=restored_compute_session.gpu.vram_gb,
                session_config=original_session.session_config,
                started_at=datetime.utcnow(),
            )
            
            db.add(new_session)
            db.commit()
            db.refresh(new_session)
            
            logger.info(f"Restored session {new_session.id} from checkpoint")
            
            return new_session
        
        except Exception as e:
            logger.error(f"Failed to restore checkpoint: {e}")
            return None
    
    @staticmethod
    def list_checkpoints(
        db: Session,
        session_id: str,
    ) -> List[Dict[str, Any]]:
        """
        List all checkpoints for a session.
        
        Args:
            db: Database session
            session_id: Session ID
        
        Returns:
            List of checkpoint data
        """
        try:
            checkpoints = db.query(Checkpoint).filter(
                Checkpoint.session_id == session_id
            ).order_by(Checkpoint.created_at.desc()).all()
            
            return [
                {
                    "id": cp.id,
                    "name": cp.name,
                    "created_at": cp.created_at.isoformat(),
                    "size_gb": cp.size_gb,
                    "storage_path": cp.storage_path,
                }
                for cp in checkpoints
            ]
        
        except Exception as e:
            logger.error(f"Failed to list checkpoints: {e}")
            return []
    
    @staticmethod
    async def delete_checkpoint(
        db: Session,
        checkpoint_id: str,
    ) -> bool:
        """
        Delete a checkpoint.
        
        Args:
            db: Database session
            checkpoint_id: Checkpoint ID
        
        Returns:
            True if successful
        """
        try:
            checkpoint = db.query(Checkpoint).filter(
                Checkpoint.id == checkpoint_id
            ).first()
            
            if not checkpoint:
                logger.error(f"Checkpoint {checkpoint_id} not found")
                return False
            
            # Get provider and delete from remote storage
            session = db.query(WorkspaceSession).filter(
                WorkspaceSession.id == checkpoint.session_id
            ).first()
            
            if session:
                provider = provider_registry.get_provider(session.provider)
                if provider:
                    await provider.delete_checkpoint(checkpoint.checkpoint_id)
            
            # Delete from database
            db.delete(checkpoint)
            db.commit()
            
            logger.info(f"Deleted checkpoint {checkpoint_id}")
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to delete checkpoint: {e}")
            return False
    
    @staticmethod
    def cleanup_expired_checkpoints(
        db: Session,
        retention_days: int = 30,
    ) -> int:
        """
        Delete checkpoints older than retention period.
        
        Args:
            db: Database session
            retention_days: Keep checkpoints newer than this many days
        
        Returns:
            Number of deleted checkpoints
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            expired = db.query(Checkpoint).filter(
                Checkpoint.created_at < cutoff_date
            ).all()
            
            deleted_count = 0
            
            for checkpoint in expired:
                try:
                    # Delete from provider
                    session = db.query(WorkspaceSession).filter(
                        WorkspaceSession.id == checkpoint.session_id
                    ).first()
                    
                    if session:
                        provider = provider_registry.get_provider(session.provider)
                        if provider:
                            asyncio.run(provider.delete_checkpoint(checkpoint.checkpoint_id))
                    
                    # Delete from database
                    db.delete(checkpoint)
                    deleted_count += 1
                
                except Exception as e:
                    logger.error(f"Failed to delete checkpoint {checkpoint.id}: {e}")
            
            db.commit()
            
            logger.info(f"Cleaned up {deleted_count} expired checkpoints")
            
            return deleted_count
        
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            return 0
    
    @staticmethod
    def get_checkpoint_size_total(
        db: Session,
        session_id: str,
    ) -> float:
        """
        Get total size of all checkpoints for a session (in GB).
        
        Args:
            db: Database session
            session_id: Session ID
        
        Returns:
            Total size in GB
        """
        try:
            checkpoints = db.query(Checkpoint).filter(
                Checkpoint.session_id == session_id
            ).all()
            
            return sum(cp.size_gb for cp in checkpoints)
        
        except Exception as e:
            logger.error(f"Failed to calculate checkpoint size: {e}")
            return 0.0
