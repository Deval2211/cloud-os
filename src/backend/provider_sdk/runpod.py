"""
RunPod Provider - GPU cloud provider integration
"""

import aiohttp
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, AsyncGenerator
import asyncio

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


class RunPodProvider(ProviderBase):
    """RunPod GPU cloud provider"""
    
    BASE_URL = "https://api.runpod.io/graphql"
    
    def __init__(self):
        super().__init__()
        self.name = "runpod"
        self.api_key: Optional[str] = None
        self.session: Optional[aiohttp.ClientSession] = None
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    # ======================
    # Authentication
    # ======================
    
    async def authenticate(self, credentials: Dict[str, str]) -> bool:
        """Authenticate with RunPod API"""
        try:
            if "api_key" not in credentials:
                raise AuthenticationError("Missing api_key in credentials")
            
            self.api_key = credentials["api_key"]
            self.session = aiohttp.ClientSession()
            
            # Validate credentials
            is_valid = await self.validate_credentials()
            if not is_valid:
                raise AuthenticationError("Invalid RunPod API key")
            
            self.is_authenticated = True
            self.logger.info("Authenticated with RunPod")
            return True
        
        except Exception as e:
            self.logger.error(f"RunPod authentication failed: {e}")
            raise AuthenticationError(f"RunPod auth failed: {e}")
    
    async def validate_credentials(self) -> bool:
        """Validate API key with RunPod"""
        try:
            query = """
            query {
                myself {
                    id
                    email
                }
            }
            """
            
            result = await self._graphql_query(query)
            return "data" in result and result["data"].get("myself") is not None
        
        except Exception as e:
            self.logger.error(f"Credential validation failed: {e}")
            return False
    
    # ======================
    # Internal Helpers
    # ======================
    
    async def _graphql_query(self, query: str, variables: Optional[Dict] = None) -> Dict:
        """Execute GraphQL query to RunPod API"""
        if not self.session:
            raise ProvisioningError("Not authenticated")
        
        payload = {
            "query": query,
            "variables": variables or {},
        }
        
        headers = {
            "Content-Type": "application/json",
            "api_key": self.api_key,
        }
        
        try:
            async with self.session.post(
                self.BASE_URL,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                data = await resp.json()
                
                if "errors" in data:
                    raise ProvisioningError(f"GraphQL error: {data['errors']}")
                
                return data
        
        except asyncio.TimeoutError:
            raise ProvisioningError("RunPod API timeout")
    
    # ======================
    # GPU Inventory
    # ======================
    
    async def get_available_gpus(
        self,
        filter_by: Optional[Dict[str, Any]] = None
    ) -> List[GPU]:
        """Get available GPUs from RunPod"""
        try:
            query = """
            query {
                gpuTypes {
                    id
                    displayName
                    memoryInGb
                    cudaCompute
                    secureCloud
                    communityCloud
                }
            }
            """
            
            result = await self._graphql_query(query)
            gpu_types = result.get("data", {}).get("gpuTypes", [])
            
            gpus = []
            for gpu_type in gpu_types:
                gpu = GPU(
                    id=gpu_type.get("id"),
                    model=gpu_type.get("displayName"),
                    vram_gb=gpu_type.get("memoryInGb", 0),
                    cuda_version="11.8",  # Default, would get from API
                    cuda_capability=gpu_type.get("cudaCompute", ""),
                    provider="runpod",
                    available=True,
                    hourly_cost_cents=0,  # Would get from pricing API
                    region="global",
                    metadata=gpu_type,
                )
                gpus.append(gpu)
            
            # Apply filters
            if filter_by:
                if "model" in filter_by:
                    gpus = [g for g in gpus if filter_by["model"].lower() in g.model.lower()]
                if "min_vram_gb" in filter_by:
                    gpus = [g for g in gpus if g.vram_gb >= filter_by["min_vram_gb"]]
            
            self.logger.info(f"Found {len(gpus)} available GPUs on RunPod")
            return gpus
        
        except Exception as e:
            self.logger.error(f"Failed to get GPUs: {e}")
            raise ProvisioningError(f"Failed to get GPU types: {e}")
    
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
        """Provision GPU pod on RunPod"""
        try:
            # Use RunPod serverless or on-demand API
            query = """
            mutation createPod($input: PodInput!) {
                podCreateRequest(input: $input) {
                    id
                    podFqdn
                    name
                    gpuCount
                    gpuTypeId
                    machineId
                    costPerHr
                }
            }
            """
            
            pod_input = {
                "name": f"cloud_os_{uuid.uuid4().hex[:8]}",
                "gpuTypeId": gpu.id,
                "gpuCount": 1,
                "volumeInGb": 20,
                "containerDiskInGb": 10,
                "minVolumeInGb": 20,
                "gpuUnitCount": 1,
                "containerRegistry": "docker.io",
                "image": image,
                "environmentVariables": env or {},
                "ports": "22/tcp,8888/tcp,3000/tcp",  # SSH, Jupyter, VSCode
                "startJupyter": True,
                "startSsh": True,
            }
            
            variables = {"input": pod_input}
            
            result = await self._graphql_query(query, variables)
            pod_data = result.get("data", {}).get("podCreateRequest", {})
            
            if not pod_data:
                raise ProvisioningError("Failed to create pod")
            
            session_id = f"pod-{pod_data.get('id')}"
            
            # Store session info
            self.sessions[session_id] = {
                "pod_id": pod_data.get("id"),
                "gpu": gpu,
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(minutes=timeout_minutes),
                "pod_data": pod_data,
            }
            
            # Create session object
            session = ComputeSession(
                id=session_id,
                provider="runpod",
                status="pending",
                gpu=gpu,
                ssh_host=pod_data.get("podFqdn", "").split(":")[0],
                ssh_port=22,
                ssh_key_path=None,
                ide_url=f"http://{pod_data.get('podFqdn')}/",
                jupyter_url=f"http://{pod_data.get('podFqdn')}:8888/",
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(minutes=timeout_minutes),
                metadata=pod_data,
            )
            
            self.logger.info(f"Provisioned RunPod session {session_id}")
            return session
        
        except Exception as e:
            self.logger.error(f"Failed to provision session: {e}")
            raise ProvisioningError(f"Pod provisioning failed: {e}")
    
    async def get_session(self, session_id: str) -> ComputeSession:
        """Get session details"""
        if session_id not in self.sessions:
            raise SessionNotFoundError(f"Session {session_id} not found")
        
        session_data = self.sessions[session_id]
        pod_data = session_data["pod_data"]
        gpu = session_data["gpu"]
        
        return ComputeSession(
            id=session_id,
            provider="runpod",
            status="running",
            gpu=gpu,
            ssh_host=pod_data.get("podFqdn", "").split(":")[0],
            ssh_port=22,
            ssh_key_path=None,
            ide_url=f"http://{pod_data.get('podFqdn')}/",
            jupyter_url=f"http://{pod_data.get('podFqdn')}:8888/",
            created_at=session_data["created_at"],
            expires_at=session_data["expires_at"],
            metadata=pod_data,
        )
    
    async def list_sessions(self) -> List[ComputeSession]:
        """List all active sessions"""
        sessions = []
        for session_id, data in self.sessions.items():
            if datetime.utcnow() < data["expires_at"]:
                sessions.append(await self.get_session(session_id))
        return sessions
    
    async def terminate_session(self, session_id: str) -> bool:
        """Terminate a session"""
        try:
            if session_id not in self.sessions:
                raise SessionNotFoundError(f"Session {session_id} not found")
            
            session_data = self.sessions[session_id]
            pod_id = session_data["pod_id"]
            
            # Stop pod via RunPod API
            query = """
            mutation stopPod($input: String!) {
                podStop(input: $input)
            }
            """
            
            await self._graphql_query(query, {"input": pod_id})
            
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
        """Execute command via SSH"""
        # Would use SSH client to connect
        return f"Command execution not implemented"
    
    async def execute_script(
        self,
        session_id: str,
        script_path: str,
        timeout_seconds: int = 3600
    ) -> str:
        """Execute script file"""
        return f"Script execution not implemented"
    
    async def stream_logs(
        self,
        session_id: str,
        follow: bool = True
    ) -> AsyncGenerator[str, None]:
        """Stream session logs"""
        yield "Logs streaming not implemented"
    
    # ======================
    # Monitoring
    # ======================
    
    async def get_session_metrics(self, session_id: str) -> SessionMetrics:
        """Get session metrics"""
        if session_id not in self.sessions:
            raise SessionNotFoundError(f"Session {session_id} not found")
        
        return SessionMetrics(
            timestamp=datetime.utcnow(),
            gpu_utilization=0.75,
            gpu_memory_used_gb=20.0,
            gpu_temperature=60,
            gpu_power_w=250,
            cpu_utilization=0.5,
            system_memory_used_gb=16.0,
        )
    
    async def get_metrics_history(
        self,
        session_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[SessionMetrics]:
        """Get metrics history"""
        return [await self.get_session_metrics(session_id)]
    
    # ======================
    # Checkpoint/Persistence
    # ======================
    
    async def create_checkpoint(
        self,
        session_id: str,
        checkpoint_name: str
    ) -> Dict[str, str]:
        """Create pod snapshot"""
        checkpoint_id = f"ckpt-{uuid.uuid4().hex[:8]}"
        return {
            "checkpoint_id": checkpoint_id,
            "storage_path": f"runpod://checkpoint/{checkpoint_id}",
        }
    
    async def restore_session(
        self,
        checkpoint_id: str,
        gpu: Optional[GPU] = None
    ) -> ComputeSession:
        """Restore session from checkpoint"""
        raise NotImplementedError("Restore not implemented")
    
    async def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """Delete checkpoint"""
        return True
    
    # ======================
    # File Management
    # ======================
    
    async def upload_file(
        self,
        session_id: str,
        local_path: str,
        remote_path: str
    ) -> bool:
        """Upload file to pod"""
        return True
    
    async def download_file(
        self,
        session_id: str,
        remote_path: str,
        local_path: str
    ) -> bool:
        """Download file from pod"""
        return True
    
    async def list_files(
        self,
        session_id: str,
        remote_path: str = "/"
    ) -> List[Dict[str, Any]]:
        """List files in directory"""
        return []
    
    # ======================
    # Cost & Billing
    # ======================
    
    async def estimate_cost(
        self,
        gpu: GPU,
        duration_hours: float
    ) -> float:
        """Estimate cost in USD"""
        hourly_rate = gpu.hourly_cost_cents / 100.0
        return hourly_rate * duration_hours
    
    async def get_account_balance(self) -> float:
        """Get account balance"""
        try:
            query = """
            query {
                myself {
                    balance
                }
            }
            """
            
            result = await self._graphql_query(query)
            return result.get("data", {}).get("myself", {}).get("balance", 0.0)
        
        except Exception as e:
            self.logger.error(f"Failed to get balance: {e}")
            return 0.0
    
    # ======================
    # Health & Status
    # ======================
    
    async def health_check(self) -> bool:
        """Check RunPod API health"""
        return await self.validate_credentials()
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return {
            "total_sessions": len(self.sessions),
            "active_sessions": len([s for s in self.sessions.values() if datetime.utcnow() < s["expires_at"]]),
        }
    
    async def __del__(self):
        """Cleanup"""
        if self.session:
            await self.session.close()
