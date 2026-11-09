"""
Provider Registry - Plugin management system
"""

from typing import Dict, List, Type, Optional, Any
import logging

from .base import ProviderBase, ProviderError

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """Manages provider lifecycle and plugin system"""
    
    def __init__(self):
        self._providers: Dict[str, ProviderBase] = {}
    
    def register(self, name: str, provider: ProviderBase) -> None:
        """
        Register a provider instance.
        
        Args:
            name: Unique provider name
            provider: Instance of ProviderBase subclass
        
        Raises:
            TypeError: If provider doesn't inherit ProviderBase
            ValueError: If name already registered
        """
        if not isinstance(provider, ProviderBase):
            raise TypeError(
                f"{provider.__class__.__name__} must inherit ProviderBase"
            )
        
        if name in self._providers:
            raise ValueError(f"Provider '{name}' already registered")
        
        self._providers[name] = provider
        logger.info(f"Registered provider: {name}")
    
    def unregister(self, name: str) -> None:
        """
        Unregister a provider.
        
        Args:
            name: Provider name
        """
        if name in self._providers:
            del self._providers[name]
            logger.info(f"Unregistered provider: {name}")
        else:
            logger.warning(f"Provider '{name}' not found")
    
    def get_provider(self, name: str) -> Optional[ProviderBase]:
        """
        Get provider instance by name.
        
        Args:
            name: Provider name
        
        Returns:
            ProviderBase instance or None if not found
        """
        return self._providers.get(name)
    
    def get_provider_or_raise(self, name: str) -> ProviderBase:
        """
        Get provider instance by name (raises if not found).
        
        Args:
            name: Provider name
        
        Returns:
            ProviderBase instance
        
        Raises:
            ProviderError: If provider not found
        """
        provider = self._providers.get(name)
        if not provider:
            raise ProviderError(f"Provider '{name}' not found. Available: {list(self._providers.keys())}")
        return provider
    
    def list_providers(self) -> List[str]:
        """
        List all registered provider names.
        
        Returns:
            List of provider names
        """
        return sorted(list(self._providers.keys()))
    
    def get_all_providers(self) -> List[ProviderBase]:
        """
        Get all provider instances.
        
        Returns:
            List of ProviderBase instances
        """
        return list(self._providers.values())
    
    def has_provider(self, name: str) -> bool:
        """Check if provider is registered"""
        return name in self._providers
    
    def count_providers(self) -> int:
        """Get number of registered providers"""
        return len(self._providers)
    
    def clear(self) -> None:
        """Unregister all providers"""
        self._providers.clear()
        logger.info("Cleared all providers")
