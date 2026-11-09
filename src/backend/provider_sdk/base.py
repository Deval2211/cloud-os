"""
Provider SDK - Base classes and interfaces
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any, AsyncGenerator
import logging

logger = logging.getLogger(__name__)


# ==================
# Exception Classes
# ==================

class ProviderError(Exception):
    """Base exception for provider errors"""
    pass


class AuthenticationError(ProviderError):
    """Authentication failed"""
    pass


class ProvisioningError(ProviderError):
    """GPU provisioning failed"""
    pass


class SessionNotFoundError(ProviderError):
    """Session not found"""
    pass


# ==================
# Data Classes
# ==================

@dataclass
class GPU:
    """GPU specification"""
    id: str
    model: str  # 'RTX 4090', 'A100', 'H100', etc.
    vram_gb: int
    cuda_version: str
    cuda_capability: str  # '8.9', '9.0', etc.
    provider: str
    available: bool = True
    utilization: float = 0.0  # 0.0-1.0
    temperature: Optional[int] = None
    power_usage_w: Optional[int] = None
    hourly_cost_cents: int = 0
    
    # Additional metadata
    region: Optional[str] = None
    availability_zone: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComputeSession:
    """Compute session specification"""
    id: str
    provider: str
    status: str  # 'pending', 'running', 'stopped', 'error'
    gpu: GPU
    
    # Connection info
    ssh_host: str
    ssh_port: int
    ssh_key_path: Optional[str] = None
    
    # URLs
    ide_url: Optional[str] = None
    jupyter_url: Optional[str] = None
    
    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionMetrics:
    """Session metrics snapshot"""
    timestamp: datetime
    gpu_utilization: float
    gpu_memory_used_gb: float
    gpu_temperature: int
    gpu_power_w: int
    cpu_utilization: float
    system_memory_used_gb: float
    network_in_mbps: float = 0.0
    network_out_mbps: float = 0.0
    disk_read_mbps: float = 0.0
    disk_write_mbps: float = 0.0


# ==================
# Provider Interface
# ==================

class ProviderBase(ABC):
    """Abstract base class for all providers"""
    
    def __init__(self):
        self.name: str = self.__class__.__name__.lower()
        self.credentials: Optional[Dict[str, str]] = None
        self.is_authenticated: bool = False
        self.logger = logging.getLogger(f"provider.{self.name}")
    
    # ======================
    # Authentication
    # ======================
    
    @abstractmethod
    async def authenticate(
        self, 
        credentials: Dict[str, str]
    ) -> bool:
        """
        Authenticate with provider.
        
        Args:
            credentials: Provider-specific credentials
                Example for RunPod: {'api_key': '...'}
                Example for Local Docker: {}
        
        Returns:
            True if authentication successful
        
        Raises:
            AuthenticationError: If credentials invalid
        """
        pass
    
    @abstractmethod
    async def validate_credentials(self) -> bool:
        """Validate stored credentials (used for health checks)"""
        pass
    
    # ======================
    # GPU Inventory
    # ======================
    
    @abstractmethod
    async def get_available_gpus(
        self,
        filter_by: Optional[Dict[str, Any]] = None
    ) -> List[GPU]:
        """
        List available GPUs.
        
        Args:
            filter_by: Optional filters
                Example: {'model': 'RTX 4090', 'min_vram_gb': 20}
        
        Returns:
            List of available GPUs
        """
        pass
    
    @abstractmethod
    async def get_gpu_details(self, gpu_id: str) -> GPU:
        """Get detailed GPU information"""
        pass
    
    # ======================
    # Session Management
    # ======================
    
    @abstractmethod
    async def provision_session(
        self,
        gpu: GPU,
        image: str = "ubuntu:22.04",
        env: Optional[Dict[str, str]] = None,
        startup_script: Optional[str] = None,
        timeout_minutes: int = 30
    ) -> ComputeSession:
        """
        Provision new GPU session.
        
        Args:
            gpu: GPU to allocate
            image: Docker image URI
            env: Environment variables
            startup_script: Optional shell script to run on startup
            timeout_minutes: Session timeout
        
        Returns:
            ComputeSession object with connection info
        
        Raises:
            ProvisioningError: If provisioning fails
        """
        pass
    
    @abstractmethod
    async def get_session(self, session_id: str) -> ComputeSession:
        """Get session details"""
        pass
    
    @abstractmethod
    async def list_sessions(self) -> List[ComputeSession]:
        """List all active sessions"""
        pass
    
    @abstractmethod
    async def terminate_session(self, session_id: str) -> bool:
        """Terminate session and release resources"""
        pass
    
    # ======================
    # Execution
    # ======================
    
    @abstractmethod
    async def execute_command(
        self,
        session_id: str,
        command: str,
        timeout_seconds: int = 300
    ) -> str:
        """
        Execute command in session.
        
        Returns:
            Command output (stdout + stderr)
        """
        pass
    
    @abstractmethod
    async def execute_script(
        self,
        session_id: str,
        script_path: str,
        timeout_seconds: int = 3600
    ) -> str:
        """Execute script file in session"""
        pass
    
    @abstractmethod
    async def stream_logs(
        self,
        session_id: str,
        follow: bool = True
    ) -> AsyncGenerator[str, None]:
        """Stream session logs (async generator)"""
        pass
    
    # ======================
    # Monitoring
    # ======================
    
    @abstractmethod
    async def get_session_metrics(
        self,
        session_id: str
    ) -> SessionMetrics:
        """Get current session metrics"""
        pass
    
    @abstractmethod
    async def get_metrics_history(
        self,
        session_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[SessionMetrics]:
        """Get historical metrics"""
        pass
    
    # ======================
    # Checkpoint/Persistence
    # ======================
    
    @abstractmethod
    async def create_checkpoint(
        self,
        session_id: str,
        checkpoint_name: str
    ) -> Dict[str, str]:
        """
        Create session checkpoint.
        
        Returns:
            {'checkpoint_id': '...', 'storage_path': '...'}
        """
        pass
    
    @abstractmethod
    async def restore_session(
        self,
        checkpoint_id: str,
        gpu: Optional[GPU] = None
    ) -> ComputeSession:
        """Restore session from checkpoint"""
        pass
    
    @abstractmethod
    async def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """Delete checkpoint"""
        pass
    
    # ======================
    # File Management
    # ======================
    
    @abstractmethod
    async def upload_file(
        self,
        session_id: str,
        local_path: str,
        remote_path: str
    ) -> bool:
        """Upload file to session"""
        pass
    
    @abstractmethod
    async def download_file(
        self,
        session_id: str,
        remote_path: str,
        local_path: str
    ) -> bool:
        """Download file from session"""
        pass
    
    @abstractmethod
    async def list_files(
        self,
        session_id: str,
        remote_path: str = "/"
    ) -> List[Dict[str, Any]]:
        """List files in session directory"""
        pass
    
    # ======================
    # Cost & Billing
    # ======================
    
    @abstractmethod
    async def estimate_cost(
        self,
        gpu: GPU,
        duration_hours: float
    ) -> float:
        """Estimate cost in USD"""
        pass
    
    @abstractmethod
    async def get_account_balance(self) -> float:
        """Get account balance in USD"""
        pass
    
    # ======================
    # Health & Status
    # ======================
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check provider health and connectivity"""
        pass
    
    @abstractmethod
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        pass
