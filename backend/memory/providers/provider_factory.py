"""Provider Factory for instantiating the active memory storage provider.

Retrieves settings, fetches the designated provider class from the MemoryRegistry,
and instantiates the provider instance.
"""

from memory.providers.base_provider import BaseProvider
from memory.manager.memory_registry import MemoryRegistry
from memory.config import settings


class ProviderFactory:
    """Factory to resolve and instantiate memory storage providers based on configuration settings."""

    _postgres_instance = None

    @staticmethod
    def get_provider() -> BaseProvider:
        """Instantiates the configured storage provider.

        Returns:
            An instance of BaseProvider.

        Raises:
            ValueError: If the configured provider name is unregistered.
        """
        provider_name = settings.provider_type
        if provider_name == "postgres":
            if ProviderFactory._postgres_instance is None:
                provider_class = MemoryRegistry.get(provider_name)
                ProviderFactory._postgres_instance = provider_class()
            return ProviderFactory._postgres_instance

        provider_class = MemoryRegistry.get(provider_name)
        return provider_class()
