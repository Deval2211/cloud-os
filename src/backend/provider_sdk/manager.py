"""
Provider Manager - High-level provider operations
"""

from typing import Dict, List, Optional, Any
import logging
import asyncio

from .base import ProviderBase, GPU, ComputeSession, ProviderError
from .registry import ProviderRegistry

logger = logging.getLogger(__name__)


class ProviderManager:
    """Manages provider operations and failover"""
    
    def __init__(self, registry: ProviderRegistry):
        self.registry = registry
    
    # =====================
    # Provider Management
    # =====================
    
    async def health_check_all(self) -> Dict[str, bool]:
        """
        Check health of all providers.
        
        Returns:
            Dict mapping provider name to health status
        """
        results = {}
        for name, provider in zip(
            self.registry.list_providers(),
            self.registry.get_all_providers()
        ):
            try:
                results[name] = await provider.health_check()
            except Exception as e:
                logger.error(f"Health check failed for {name}: {e}")
                results[name] = False
        return results
    
    async def get_usage_stats_all(self) -> Dict[str, Dict[str, Any]]:
        """Get usage stats from all providers"""
        results = {}
        for name, provider in zip(
            self.registry.list_providers(),
            self.registry.get_all_providers()
        ):
            try:
                results[name] = await provider.get_usage_stats()
            except Exception as e:
                logger.error(f"Failed to get usage stats from {name}: {e}")
                results[name] = {"error": str(e)}
        return results
    
    # =====================
    # GPU Discovery
    # =====================
    
    async def discover_all_gpus(
        self,
        filter_by: Optional[Dict[str, Any]] = None
    ) -> List[GPU]:
        """
        Discover GPUs from all providers.
        
        Args:
            filter_by: Optional filters
        
        Returns:
            List of all available GPUs
        """
        all_gpus = []
        tasks = []
        
        for provider in self.registry.get_all_providers():
            tasks.append(provider.get_available_gpus(filter_by))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                provider_name = list(self.registry.list_providers())[i]
                logger.error(f"Failed to get GPUs from {provider_name}: {result}")
            else:
                all_gpus.extend(result)
        
        return all_gpus
    
    async def find_gpu(
        self,
        provider_name: str,
        gpu_model: str,
        min_vram_gb: int = 0
    ) -> Optional[GPU]:
        """
        Find a specific GPU from a provider.
        
        Args:
            provider_name: Provider to search
            gpu_model: GPU model to find
            min_vram_gb: Minimum VRAM required
        
        Returns:
            GPU instance or None
        """
        provider = self.registry.get_provider(provider_name)
        if not provider:
            raise ProviderError(f"Provider {provider_name} not found")
        
        filter_by = {
            'model': gpu_model,
            'min_vram_gb': min_vram_gb,
        }
        
        gpus = await provider.get_available_gpus(filter_by)
        return gpus[0] if gpus else None
    
    # =====================
    # Session Management
    # =====================
    
    async def provision_with_failover(
        self,
        providers: List[str],
        gpu_model: str,
        image: str = "ubuntu:22.04",
        env: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> ComputeSession:
        """
        Provision session with failover to next provider if first fails.
        
        Args:
            providers: List of provider names to try (in order)
            gpu_model: GPU model to allocate
            image: Docker image
            env: Environment variables
        
        Returns:
            ComputeSession
        
        Raises:
            ProviderError: If all providers fail
        """
        errors = []
        
        for provider_name in providers:
            try:
                provider = self.registry.get_provider(provider_name)
                if not provider:
                    errors.append(f"{provider_name}: Not found")
                    continue
                
                logger.info(f"Attempting to provision on {provider_name}")
                
                # Find available GPU
                gpu = await provider.get_available_gpus({
                    'model': gpu_model,
                    'available': True,
                })
                
                if not gpu:
                    errors.append(f"{provider_name}: No GPUs available")
                    continue
                
                # Provision session
                session = await provider.provision_session(
                    gpu=gpu[0],
                    image=image,
                    env=env,
                    **kwargs
                )
                
                logger.info(f"Session {session.id} provisioned on {provider_name}")
                return session
            
            except Exception as e:
                logger.error(f"Failed to provision on {provider_name}: {e}")
                errors.append(f"{provider_name}: {str(e)}")
                continue
        
        # All providers failed
        error_msg = "Provisioning failed on all providers:\n" + "\n".join(errors)
        raise ProviderError(error_msg)
    
    async def get_session_from_any(self, session_id: str) -> Optional[tuple[str, ComputeSession]]:
        """
        Find and retrieve session from any provider.
        
        Returns:
            Tuple of (provider_name, session) or None
        """
        tasks = []
        for provider in self.registry.get_all_providers():
            tasks.append(provider.get_session(session_id))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if not isinstance(result, Exception):
                provider_name = list(self.registry.list_providers())[i]
                return (provider_name, result)
        
        return None
    
    # =====================
    # Cost Estimation
    # =====================
    
    async def estimate_cost_comparison(
        self,
        gpu_model: str,
        duration_hours: float
    ) -> Dict[str, float]:
        """
        Get cost estimates from all providers.
        
        Returns:
            Dict mapping provider name to estimated cost in USD
        """
        estimates = {}
        tasks = []
        providers_list = self.registry.get_all_providers()
        
        for provider in providers_list:
            async def get_estimate(p):
                try:
                    gpus = await p.get_available_gpus({'model': gpu_model})
                    if gpus:
                        return await p.estimate_cost(gpus[0], duration_hours)
                except Exception as e:
                    logger.error(f"Cost estimation failed for {p.name}: {e}")
                return None
            
            tasks.append(get_estimate(provider))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, (provider_name, result) in enumerate(
            zip(self.registry.list_providers(), results)
        ):
            if isinstance(result, Exception):
                estimates[provider_name] = None
            elif result is not None:
                estimates[provider_name] = result
        
        return estimates
