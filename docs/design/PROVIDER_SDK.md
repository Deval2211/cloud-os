# Provider Plugin SDK

**Document**: Provider Plugin Interface & Implementation Guide
**Version**: 1.0
**Status**: Design Phase

## Overview

The Provider Plugin System allows third-party GPU cloud providers to be integrated into Cloud OS. Providers are implemented as Python modules that conform to the standard `ProviderBase` interface.

**Design Goals:**
- **Hot-pluggable**: Load/unload providers without restart
- **Extensible**: New providers added without core changes
- **Resilient**: Provider failures don't crash the system
- **Observable**: Full metrics and monitoring
- **Cost-aware**: Support cost estimation and optimization

## Architecture

### Provider Registry

```
/src/backend/providers/
├── __init__.py
├── base.py                 # ProviderBase interface
├── registry.py             # Provider registry
├── manager.py              # Provider manager
├── runpod.py               # RunPod implementation
├── vastai.py               # Vast.ai implementation
├── lambda_labs.py          # Lambda Labs implementation
├── paperspace.py           # Paperspace implementation
├── local_docker.py         # Local Docker implementation
└── examples/
    └── custom_provider_template.py
```

### Provider Registry Class

```python
# providers/registry.py
class ProviderRegistry:
    """Manages provider lifecycle"""
    
    def __init__(self):
        self._providers: Dict[str, ProviderBase] = {}
        self._instances: Dict[str, Any] = {}
    
    def register(self, name: str, provider_class: Type[ProviderBase]):
        """Register a provider plugin"""
        if not issubclass(provider_class, ProviderBase):
            raise TypeError(f"{provider_class} must inherit ProviderBase")
        
        self._providers[name] = provider_class()
        logger.info(f"Registered provider: {name}")
    
    def unregister(self, name: str):
        """Unregister a provider"""
        if name in self._providers:
            del self._providers[name]
            logger.info(f"Unregistered provider: {name}")
    
    def get_provider(self, name: str) -> ProviderBase:
        """Get provider instance"""
        return self._providers.get(name)
    
    def list_providers(self) -> List[str]:
        """List available providers"""
        return list(self._providers.keys())
    
    def get_all_providers(self) -> List[ProviderBase]:
        """Get all providers"""
        return list(self._providers.values())

# Global registry
provider_registry = ProviderRegistry()
```

## ProviderBase Interface

```python
# providers/base.py
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

@dataclass
class GPU:
    """GPU specification"""
    id: str
    model: str  # 'RTX 4090', 'A100', 'H100', etc.
    vram_gb: int
    cuda_version: str
    cuda_capability: str  # '8.9', '9.0', etc.
    provider: str
    available: bool
    utilization: float  # 0.0-1.0
    temperature: Optional[int]
    power_usage_w: Optional[int]
    hourly_cost_cents: int
    
    # Additional metadata
    region: Optional[str]
    availability_zone: Optional[str]
    metadata: Dict[str, Any] = None

@dataclass
class ComputeSession:
    """Compute session specification"""
    id: str
    provider: str
    status: str  # 'pending', 'running', 'stopped'
    gpu: GPU
    
    # Connection info
    ssh_host: str
    ssh_port: int
    ssh_key_path: str
    
    # URLs
    ide_url: Optional[str]
    jupyter_url: Optional[str]
    
    # Timing
    created_at: datetime
    expires_at: Optional[datetime]
    
    # Metadata
    metadata: Dict[str, Any] = None

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
    network_in_mbps: float
    network_out_mbps: float
    disk_read_mbps: float
    disk_write_mbps: float

class ProviderBase(ABC):
    """Abstract base class for all providers"""
    
    def __init__(self):
        self.name: str = self.__class__.__name__.lower()
        self.credentials: Optional[Dict[str, str]] = None
        self.is_authenticated: bool = False
    
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
                Example for Vast.ai: {'api_key': '...'}
        
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
        image: str,
        env: Dict[str, str],
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
    ):
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
    async def get_health_status(self) -> Dict[str, Any]:
        """
        Get provider health status.
        
        Returns:
            {
                'status': 'healthy' | 'degraded' | 'down',
                'message': '...',
                'last_check': datetime,
                'services': {
                    'gpu_provisioning': 'up',
                    'api': 'up'
                }
            }
        """
        pass
    
    # ======================
    # Utility Methods
    # ======================
    
    @abstractmethod
    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider metadata"""
        return {
            'name': self.name,
            'display_name': 'Provider Display Name',
            'version': '1.0',
            'gpu_models': ['RTX 4090', 'A100'],
            'regions': ['us-east-1', 'us-west-1'],
            'supports_checkpoint': True,
            'supports_scaling': False
        }
```

## Example Implementations

### RunPod Provider

```python
# providers/runpod.py
class RunPodProvider(ProviderBase):
    """RunPod GPU Cloud integration"""
    
    API_BASE_URL = "https://api.runpod.io/graphql"
    
    async def authenticate(self, credentials: Dict[str, str]) -> bool:
        self.credentials = credentials
        api_key = credentials.get('api_key')
        
        if not api_key:
            raise ValueError("api_key required")
        
        # Test API connectivity
        result = await self.validate_credentials()
        self.is_authenticated = result
        return result
    
    async def get_available_gpus(
        self,
        filter_by: Optional[Dict[str, Any]] = None
    ) -> List[GPU]:
        query = """
        query {
            gpuTypes {
                id
                displayName
                memoryInGb
                minBidPrice
                maxBidPrice
                securePrice
            }
        }
        """
        
        response = await self._graphql_request(query)
        gpus = []
        
        for gpu_type in response['data']['gpuTypes']:
            gpu = GPU(
                id=gpu_type['id'],
                model=gpu_type['displayName'],
                vram_gb=gpu_type['memoryInGb'],
                cuda_version='12.4',  # Get from pod specs
                cuda_capability='8.9',
                provider='runpod',
                available=True,
                utilization=0.0,
                temperature=None,
                power_usage_w=None,
                hourly_cost_cents=int(gpu_type['minBidPrice'] * 100)
            )
            gpus.append(gpu)
        
        return gpus
    
    async def provision_session(
        self,
        gpu: GPU,
        image: str,
        env: Dict[str, str],
        startup_script: Optional[str] = None,
        timeout_minutes: int = 30
    ) -> ComputeSession:
        mutation = """
        mutation {
            podFindAndDeployOnDemand(
                input: {
                    gpuCount: 1
                    volumeInGb: 50
                    containerDiskInGb: 50
                    minVolumeInGb: 0
                    gpuTypeId: $gpuTypeId
                    name: $name
                    imageName: $image
                    startJupyter: true
                    startSsh: true
                    env: $env
                }
            ) {
                id
                machineId
                pod {
                    id
                    name
                    status
                    desiredStatus
                    podFqdn
                }
            }
        }
        """
        
        variables = {
            'gpuTypeId': gpu.id,
            'name': f'cloud-os-{uuid4()}',
            'image': image,
            'env': [{'key': k, 'value': v} for k, v in env.items()]
        }
        
        response = await self._graphql_request(mutation, variables)
        pod = response['data']['podFindAndDeployOnDemand']['pod']
        
        return ComputeSession(
            id=pod['id'],
            provider='runpod',
            status=pod['status'],
            gpu=gpu,
            ssh_host=pod['podFqdn'],
            ssh_port=22,
            ssh_key_path='/root/.ssh/id_rsa',
            ide_url=f"https://code.runpod.io?pod_id={pod['id']}",
            jupyter_url=f"https://jupyter.runpod.io?pod_id={pod['id']}",
            created_at=datetime.utcnow()
        )
    
    async def _graphql_request(
        self,
        query: str,
        variables: Optional[Dict] = None
    ) -> Dict:
        """Make GraphQL request to RunPod API"""
        headers = {
            'Content-Type': 'application/json',
            'api_key': self.credentials['api_key']
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.API_BASE_URL,
                json={'query': query, 'variables': variables or {}},
                headers=headers
            ) as resp:
                return await resp.json()
    
    # ... implement other abstract methods
```

### Local Docker Provider (for development)

```python
# providers/local_docker.py
class LocalDockerProvider(ProviderBase):
    """Local Docker provider for development"""
    
    def __init__(self):
        super().__init__()
        self.client = docker.from_env()
    
    async def authenticate(self, credentials: Dict[str, str]) -> bool:
        # No authentication needed for local Docker
        self.is_authenticated = True
        return True
    
    async def get_available_gpus(self) -> List[GPU]:
        # Check NVIDIA GPUs
        try:
            result = subprocess.run(['nvidia-smi', '-L'], capture_output=True, text=True)
            gpus = []
            
            for idx, line in enumerate(result.stdout.strip().split('\n')):
                # Parse: "GPU 0: NVIDIA RTX A5000 (UUID: ...)"
                gpu = GPU(
                    id=f'local-gpu-{idx}',
                    model=line.split(':')[1].strip(),
                    vram_gb=24,  # Get from nvidia-smi
                    cuda_version='12.4',
                    cuda_capability='8.0',
                    provider='local_docker',
                    available=True,
                    utilization=0.0,
                    temperature=None,
                    power_usage_w=None,
                    hourly_cost_cents=0  # Local = free
                )
                gpus.append(gpu)
            
            return gpus
        except:
            return []
    
    async def provision_session(
        self,
        gpu: GPU,
        image: str,
        env: Dict[str, str],
        startup_script: Optional[str] = None,
        timeout_minutes: int = 30
    ) -> ComputeSession:
        # Pull image
        self.client.images.pull(image)
        
        # Start container with GPU
        container = self.client.containers.run(
            image,
            detach=True,
            runtime='nvidia',
            environment={
                **env,
                'NVIDIA_VISIBLE_DEVICES': 'all'
            },
            ports={'22/tcp': None, '8888/tcp': None},
            volumes={'/tmp': {'bind': '/workspace', 'mode': 'rw'}}
        )
        
        # Get mapped ports
        inspect = self.client.api.inspect_container(container.id)
        ssh_port = inspect['NetworkSettings']['Ports']['22/tcp'][0]['HostPort']
        jupyter_port = inspect['NetworkSettings']['Ports']['8888/tcp'][0]['HostPort']
        
        return ComputeSession(
            id=container.id[:12],
            provider='local_docker',
            status='running',
            gpu=gpu,
            ssh_host='localhost',
            ssh_port=int(ssh_port),
            ssh_key_path='/home/user/.ssh/id_rsa',
            ide_url=f'http://localhost:{jupyter_port}',
            jupyter_url=f'http://localhost:{jupyter_port}',
            created_at=datetime.utcnow()
        )
```

## Provider Manager

```python
# providers/manager.py
class ProviderManager:
    """Manages provider lifecycle and routing"""
    
    def __init__(self):
        self.registry = ProviderRegistry()
        self._load_builtin_providers()
    
    def _load_builtin_providers(self):
        """Load built-in providers"""
        from . import runpod, vastai, lambda_labs, local_docker
        
        self.registry.register('runpod', runpod.RunPodProvider)
        self.registry.register('vastai', vastai.VastAIProvider)
        self.registry.register('lambda_labs', lambda_labs.LambdaLabsProvider)
        self.registry.register('local_docker', local_docker.LocalDockerProvider)
    
    def load_custom_provider(self, path: str, name: str):
        """Dynamically load custom provider"""
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        provider_class = getattr(module, 'CustomProvider')
        self.registry.register(name, provider_class)
    
    async def allocate_gpu(
        self,
        requirements: Dict[str, Any]
    ) -> Tuple[ProviderBase, GPU]:
        """Find best GPU meeting requirements"""
        
        candidates = []
        
        for provider in self.registry.get_all_providers():
            try:
                gpus = await provider.get_available_gpus()
                for gpu in gpus:
                    if self._meets_requirements(gpu, requirements):
                        candidates.append((provider, gpu))
            except Exception as e:
                logger.error(f"Error querying {provider.name}: {e}")
                continue
        
        if not candidates:
            raise NoGPUAvailableError("No GPUs match requirements")
        
        # Score and sort
        candidates.sort(
            key=lambda x: self._score_gpu(x[1], requirements),
            reverse=True
        )
        
        return candidates[0]
    
    def _meets_requirements(self, gpu: GPU, reqs: Dict) -> bool:
        """Check if GPU meets requirements"""
        if reqs.get('min_vram_gb', 0) > gpu.vram_gb:
            return False
        if reqs.get('gpu_models') and gpu.model not in reqs['gpu_models']:
            return False
        if reqs.get('max_cost_per_hour'):
            if gpu.hourly_cost_cents / 100 > reqs['max_cost_per_hour']:
                return False
        return True

# Global manager
provider_manager = ProviderManager()
```

## Testing Provider Implementations

```python
# tests/test_providers.py
import pytest
from providers.base import ProviderBase
from providers.runpod import RunPodProvider

@pytest.fixture
async def provider():
    p = RunPodProvider()
    await p.authenticate({'api_key': os.getenv('RUNPOD_API_KEY')})
    yield p

@pytest.mark.asyncio
async def test_get_available_gpus(provider):
    gpus = await provider.get_available_gpus()
    assert len(gpus) > 0
    assert all(g.vram_gb > 0 for g in gpus)

@pytest.mark.asyncio
async def test_provision_session(provider):
    gpus = await provider.get_available_gpus()
    gpu = gpus[0]
    
    session = await provider.provision_session(
        gpu=gpu,
        image='python:3.11',
        env={'TEST': 'value'}
    )
    
    assert session.id
    assert session.ssh_host
    assert session.created_at
    
    # Cleanup
    await provider.terminate_session(session.id)
```

## Next Steps

- Review [Backend Architecture](../architecture/02-BACKEND_ARCHITECTURE.md)
- See [API Specifications](../api/API_SPECIFICATIONS.md)
