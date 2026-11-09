"""
Provider SDK - GPU cloud provider integration framework
"""

from .base import (
    ProviderBase,
    GPU,
    ComputeSession,
    SessionMetrics,
    ProviderError,
    AuthenticationError,
    ProvisioningError,
)
from .registry import ProviderRegistry
from .manager import ProviderManager

# Global registry instance
provider_registry = ProviderRegistry()

# Global manager instance
provider_manager = ProviderManager(provider_registry)

__all__ = [
    "ProviderBase",
    "GPU",
    "ComputeSession",
    "SessionMetrics",
    "ProviderError",
    "AuthenticationError",
    "ProvisioningError",
    "ProviderRegistry",
    "ProviderManager",
    "provider_registry",
    "provider_manager",
]
