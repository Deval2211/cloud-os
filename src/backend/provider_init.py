"""
Provider initialization and registration
"""

import logging
from provider_sdk import provider_registry, provider_manager
from provider_sdk.local_docker import LocalDockerProvider
from provider_sdk.runpod import RunPodProvider

logger = logging.getLogger(__name__)


def initialize_providers():
    """Initialize and register all available providers"""
    
    logger.info("Initializing GPU providers...")
    
    try:
        # Register Local Docker provider (always available)
        local_docker = LocalDockerProvider()
        provider_registry.register("local_docker", local_docker)
        logger.info("✓ Registered Local Docker provider")
    except Exception as e:
        logger.error(f"Failed to register Local Docker provider: {e}")
    
    try:
        # Register RunPod provider
        runpod = RunPodProvider()
        provider_registry.register("runpod", runpod)
        logger.info("✓ Registered RunPod provider")
    except Exception as e:
        logger.error(f"Failed to register RunPod provider: {e}")
    
    # Print registered providers
    providers = provider_registry.list_providers()
    logger.info(f"Registered providers: {', '.join(providers)}")
    
    return providers


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    initialize_providers()
