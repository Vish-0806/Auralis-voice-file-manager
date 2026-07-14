"""Memory Service Registry catalog."""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class MemoryRegistry:
    """Catalog holding registrations for all memory services and custom plugins."""

    _services: Dict[str, Any] = {}

    @classmethod
    def register(cls, name: str, service: Any) -> None:
        """Registers a memory service instance under a unique identifier.

        Args:
            name: The service identifier name.
            service: The service class instance.
        """
        name_lower = name.lower().strip()
        logger.info(f"Registering service '{name_lower}' in MemoryRegistry.")
        cls._services[name_lower] = service

    @classmethod
    def get(cls, name: str) -> Any:
        """Retrieves a registered memory service instance.

        Args:
            name: The service identifier name.

        Returns:
            The service instance if registered, else None.
        """
        return cls._services.get(name.lower().strip())

    @classmethod
    def clear(cls) -> None:
        """Clears all service registrations."""
        cls._services.clear()

    @classmethod
    def list_services(cls) -> Dict[str, Any]:
        """Returns a copy of all registered services.

        Returns:
            Dictionary copy of all registered memory service mappings.
        """
        return dict(cls._services)
