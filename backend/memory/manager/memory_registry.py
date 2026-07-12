"""Provider registration and discovery module.

Enables registering concrete memory storage providers and resolving them dynamically,
supporting future extension and runtime discovery.
"""

import logging
from typing import Dict, Type
from memory.providers.base_provider import BaseProvider, InMemoryProvider

logger = logging.getLogger(__name__)


class MemoryRegistry:
    """Registry for storage providers in the memory subsystem."""

    _registry: Dict[str, Type[BaseProvider]] = {}

    @classmethod
    def register(cls, name: str, provider_class: Type[BaseProvider]) -> None:
        """Registers a memory provider class with the system.

        Args:
            name: The unique string identifier for the provider.
            provider_class: The provider class implementing BaseProvider.
        """
        cls._registry[name] = provider_class
        logger.info(
            "Provider registered in MemoryRegistry",
            extra={"provider_name": name, "provider_class": provider_class.__name__},
        )

    @classmethod
    def get(cls, name: str) -> Type[BaseProvider]:
        """Retrieves a registered provider class.

        Args:
            name: The unique identifier of the provider.

        Returns:
            The class of the requested provider.

        Raises:
            ValueError: If the provider is not registered.
        """
        if name not in cls._registry:
            logger.error(
                "Requested unregistered provider",
                extra={"provider_name": name},
            )
            raise ValueError(f"Memory provider '{name}' is not registered in the registry.")
        return cls._registry[name]

    @classmethod
    def list_registered(cls) -> Dict[str, Type[BaseProvider]]:
        """Returns a copy of all registered providers.

        Returns:
            A dictionary mapping registered names to their provider classes.
        """
        return cls._registry.copy()


# Auto-register the default in-memory provider
MemoryRegistry.register("in_memory", InMemoryProvider)
