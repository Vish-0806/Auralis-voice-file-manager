"""Provider Factory for instantiating the active memory storage provider.

Retrieves settings, fetches the designated provider class from the MemoryRegistry,
and instantiates the provider instance.
"""

from memory.providers.base_provider import BaseProvider
from memory.manager.memory_registry import MemoryRegistry
from memory.config import settings


class ProviderFactory:
    """Factory to resolve and instantiate memory storage providers based on configuration settings."""

    @staticmethod
    def get_provider() -> BaseProvider:
        """Instantiates the configured storage provider.

        Returns:
            An instance of BaseProvider.

        Raises:
            ValueError: If the configured provider name is unregistered.
        """
        provider_name = settings.provider_type
        provider_class = MemoryRegistry.get(provider_name)
        return provider_class()
