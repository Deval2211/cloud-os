"""
Local Docker Provider - Development/testing provider
"""

import docker
import logging
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, AsyncGenerator
import json

from .base import (
    ProviderBase,
    GPU,
    ComputeSession,
    SessionMetrics,
    AuthenticationError,
    ProvisioningError,
    SessionNotFoundError,
)

logger = logging.getLogger(__name__)


class LocalDockerProvider(ProviderBase):
    """Local Docker provider for development"""
    
    def __init__(self):
        super().__init__()
        self.name = "local_docker"
        self.client: Optional[docker.DockerClient] = None
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    # ======================
    # Authentication
    # ======================
    
    async def authenticate(self, credentials: Dict[str, str]) -> bool:
        """Connect to local Docker daemon"""
        try:
            self.client = docker.from_env()
            # Test connection
            self.client.ping()
            self.is_authenticated = True
            self.logger.info("Connected to local Docker daemon")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to Docker: {e}")
            raise AuthenticationError(f"Docker connection failed: {e}")
    
    async def validate_credentials(self) -> bool:
        """Check Docker daemon is still responsive"""
        try:
            if self.client:
                self.client.ping()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Docker health check failed: {e}")
            return False
    
    # ======================
    # GPU Inventory
    # ======================
    
    async def get_available_gpus(
        self,
        filter_by: Optional[Dict[str, Any]] = None
    ) -> List[GPU]:
        """Return mock GPU inventory"""
        # Mock GPUs for local development
        mock_gpus = [
            GPU(
                id="gpu-0",
                model="RTX 4090",
                vram_gb=24,
                cuda_version="12.1",
                cuda_capability="8.9",
                provider="local_docker",
                available=True,
                region="local",
                hourly_cost_cents=0,  # Free for local
            ),
            GPU(
                id="gpu-1",
                model="A100",
                vram_gb=40,
                cuda_version="12.1",
                cuda_capability="8.0",
                provider="local_docker",
                available=True,
                region="local",
                hourly_cost_cents=0,
            ),
        ]
        
        # Apply filters
        if filter_by:
            filtered = mock_gpus
            if "model" in filter_by:
                filtered = [g for g in filtered if g.model == filter_by["model"]]
            if "min_vram_gb" in filter_by:
                filtered = [g for g in filtered if g.vram_gb >= filter_by["min_vram_gb"]]
            return filtered
        
        return mock_gpus
    
    async def get_gpu_details(self, gpu_id: str) -> GPU:
        """Get GPU details"""
        gpus = await self.get_available_gpus()
        for gpu in gpus:
            if gpu.id == gpu_id:
                return gpu
        raise SessionNotFoundError(f"GPU {gpu_id} not found")
    
    # ======================
    # Session Management
    # ======================
    
    async def provision_session(
        self,
        gpu: GPU,
        image: str = "ubuntu:22.04",
        env: Optional[Dict[str, str]] = None,
        startup_script: Optional[str] = None,
        timeout_minutes: int = 30
    ) -> ComputeSession:
        """Provision a Docker container session"""
        try:
            if not self.client:
                raise ProvisioningError("Not authenticated with Docker")
            
            session_id = f"session-{uuid.uuid4().hex[:8]}"
            
            # Prepare environment
            docker_env = env or {}
            docker_env["SESSION_ID"] = session_id
            
            # Run container
            container = self.client.containers.run(
                image,
                command="/bin/bash",
                stdin_open=True,
                tty=True,
                detach=True,
                name=session_id,
                environment=docker_env,
                labels={"cloud_os_session": session_id},
            )
            
            self.logger.info(f"Created container {session_id}")
            
            # Store session info
            self.sessions[session_id] = {
                "container_id": container.id,
                "gpu": gpu,
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(minutes=timeout_minutes),
            }
            
            # Create session object
            session = ComputeSession(
                id=session_id,
                provider="local_docker",
                status="running",
                gpu=gpu,
                ssh_host="localhost",
                ssh_port=22,
                ssh_key_path=None,
                ide_url=None,  # Would set up VS Code Server in production
                jupyter_url=None,
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(minutes=timeout_minutes),
                metadata={"container_id": container.id},
            )
            
            return session
        
        except Exception as e:
            self.logger.error(f"Failed to provision session: {e}")
            raise ProvisioningError(f"Session provisioning failed: {e}")
    
    async def get_session(self, session_id: str) -> ComputeSession:
        """Get session details"""
        if session_id not in self.sessions:
            raise SessionNotFoundError(f"Session {session_id} not found")
        
        session_data = self.sessions[session_id]
        gpu = session_data["gpu"]
        
        return ComputeSession(
            id=session_id,
            provider="local_docker",
            status="running",
            gpu=gpu,
            ssh_host="localhost",
            ssh_port=22,
            ssh_key_path=None,
            ide_url=None,
            jupyter_url=None,
            created_at=session_data["created_at"],
            expires_at=session_data["expires_at"],
            metadata=session_data,
        )
    
    async def list_sessions(self) -> List[ComputeSession]:
        """List all active sessions"""
        sessions = []
        for session_id, data in self.sessions.items():
            # Check if expired
            if datetime.utcnow() > data["expires_at"]:
                continue
            
            sessions.append(await self.get_session(session_id))
        
        return sessions
    
    async def terminate_session(self, session_id: str) -> bool:
        """Terminate a session"""
        try:
            if session_id not in self.sessions:
                raise SessionNotFoundError(f"Session {session_id} not found")
            
            session_data = self.sessions[session_id]
            container_id = session_data["container_id"]
            
            # Stop and remove container
            container = self.client.containers.get(container_id)
            container.stop()
            container.remove()
            
            del self.sessions[session_id]
            self.logger.info(f"Terminated session {session_id}")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to terminate session: {e}")
            return False
    
    # ======================
    # Execution
    # ======================
    
    async def execute_command(
        self,
        session_id: str,
        command: str,
        timeout_seconds: int = 300
    ) -> str:
        """Execute command in session"""
        if not self.client:
            raise ProvisioningError("Not authenticated")
        
        session_data = self.sessions.get(session_id)
        if not session_data:
            raise SessionNotFoundError(f"Session {session_id} not found")
        
        try:
            container = self.client.containers.get(session_data["container_id"])
            result = await asyncio.to_thread(
                container.exec_run,
                command,
                timeout=timeout_seconds
            )
            return result.output.decode("utf-8", errors="ignore")
        except Exception as e:
            self.logger.error(f"Command execution failed: {e}")
            raise ProvisioningError(f"Command execution failed: {e}")
    
    async def execute_script(
        self,
        session_id: str,
        script_path: str,
        timeout_seconds: int = 3600
    ) -> str:
        """Execute script file"""
        # Simplified - would copy script to container and run
        return await self.execute_command(
            session_id,
            f"bash {script_path}",
            timeout_seconds
        )
    
    async def stream_logs(
        self,
        session_id: str,
        follow: bool = True
    ) -> AsyncGenerator[str, None]:
        """Stream container logs"""
        if not self.client:
            raise ProvisioningError("Not authenticated")
        
        session_data = self.sessions.get(session_id)
        if not session_data:
            raise SessionNotFoundError(f"Session {session_id} not found")
        
        container = self.client.containers.get(session_data["container_id"])
        
        for line in container.logs(stream=follow, follow=follow):
            yield line.decode("utf-8", errors="ignore")
    
    # ======================
    # Monitoring
    # ======================
    
    async def get_session_metrics(self, session_id: str) -> SessionMetrics:
        """Get session metrics"""
        if not self.client:
            raise ProvisioningError("Not authenticated")
        
        session_data = self.sessions.get(session_id)
        if not session_data:
            raise SessionNotFoundError(f"Session {session_id} not found")
        
        container = self.client.containers.get(session_data["container_id"])
        stats = container.stats(stream=False)
        
        # Parse stats
        cpu_percent = (
            stats["cpu_stats"]["cpu_usage"]["total_usage"] /
            stats["cpu_stats"]["system_cpu_usage"] * 100
        )
        memory_usage_gb = stats["memory_stats"]["usage"] / (1024 ** 3)
        
        return SessionMetrics(
            timestamp=datetime.utcnow(),
            gpu_utilization=0.5,  # Mock
            gpu_memory_used_gb=2.5,  # Mock
            gpu_temperature=50,  # Mock
            gpu_power_w=100,  # Mock
            cpu_utilization=cpu_percent,
            system_memory_used_gb=memory_usage_gb,
        )
    
    async def get_metrics_history(
        self,
        session_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[SessionMetrics]:
        """Get metrics history (not implemented for local)"""
        return [await self.get_session_metrics(session_id)]
    
    # ======================
    # Checkpoint/Persistence
    # ======================
    
    async def create_checkpoint(
        self,
        session_id: str,
        checkpoint_name: str
    ) -> Dict[str, str]:
        """Create container checkpoint"""
        if not self.client:
            raise ProvisioningError("Not authenticated")
        
        session_data = self.sessions.get(session_id)
        if not session_data:
            raise SessionNotFoundError(f"Session {session_id} not found")
        
        container = self.client.containers.get(session_data["container_id"])
        checkpoint_id = f"ckpt-{uuid.uuid4().hex[:8]}"
        
        # Commit container to image
        image = container.commit(
            repository="cloud_os_checkpoint",
            tag=checkpoint_id,
        )
        
        self.logger.info(f"Created checkpoint {checkpoint_id}")
        
        return {
            "checkpoint_id": checkpoint_id,
            "storage_path": f"docker://cloud_os_checkpoint:{checkpoint_id}",
        }
    
    async def restore_session(
        self,
        checkpoint_id: str,
        gpu: Optional[GPU] = None
    ) -> ComputeSession:
        """Restore session from checkpoint"""
        # Simplified - would run image from checkpoint
        raise NotImplementedError("Restore not implemented for local docker")
    
    async def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """Delete checkpoint"""
        try:
            self.client.images.remove(f"cloud_os_checkpoint:{checkpoint_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete checkpoint: {e}")
            return False
    
    # ======================
    # File Management
    # ======================
    
    async def upload_file(
        self,
        session_id: str,
        local_path: str,
        remote_path: str
    ) -> bool:
        """Upload file to session"""
        # Would use docker cp
        return True
    
    async def download_file(
        self,
        session_id: str,
        remote_path: str,
        local_path: str
    ) -> bool:
        """Download file from session"""
        # Would use docker cp
        return True
    
    async def list_files(
        self,
        session_id: str,
        remote_path: str = "/"
    ) -> List[Dict[str, Any]]:
        """List files in directory"""
        output = await self.execute_command(session_id, f"ls -la {remote_path}")
        # Parse and return
        return []
    
    # ======================
    # Cost & Billing
    # ======================
    
    async def estimate_cost(
        self,
        gpu: GPU,
        duration_hours: float
    ) -> float:
        """Estimate cost (free for local)"""
        return 0.0
    
    async def get_account_balance(self) -> float:
        """Get account balance (unlimited for local)"""
        return float('inf')
    
    # ======================
    # Health & Status
    # ======================
    
    async def health_check(self) -> bool:
        """Check Docker daemon health"""
        return await self.validate_credentials()
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return {
            "total_sessions": len(self.sessions),
            "active_sessions": len([s for s in self.sessions.values() if datetime.utcnow() < s["expires_at"]]),
            "containers": len(self.client.containers.list()) if self.client else 0,
        }
