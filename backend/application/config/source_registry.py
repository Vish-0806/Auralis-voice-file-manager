"""Configuration Source Registry (Phase 14.3.2).

Thread-safe registry for managing, prioritizing, and sorting configuration sources.
"""

from datetime import datetime, timezone
import logging
from threading import RLock
from typing import Dict, List, Optional, Tuple

from backend.application.config.exceptions import ConfigurationSourceError
from backend.application.config.interfaces import IConfigurationSource

logger = logging.getLogger(__name__)


class SourceRegistry:
    """Production thread-safe registry for configuration sources."""

    def __init__(self) -> None:
        """Initialize SourceRegistry."""
        self._lock = RLock()
        self._sources_map: Dict[str, IConfigurationSource] = {}
        self._registration_order: List[str] = []

    def register_source(self, source: IConfigurationSource) -> bool:
        """Register a configuration source.

        Args:
            source: Target IConfigurationSource instance.

        Returns:
            bool: True if registered.

        Raises:
            ConfigurationSourceError: If source or source_name is duplicate or None.
        """
        if source is None or not source.source_name:
            raise ConfigurationSourceError("Cannot register invalid or nameless configuration source.")

        with self._lock:
            name = source.source_name
            if name in self._sources_map:
                raise ConfigurationSourceError(f"Configuration source '{name}' is already registered.")

            self._sources_map[name] = source
            self._registration_order.append(name)
            logger.info("Registered configuration source '%s' with priority %d.", name, source.priority)
            return True

    def unregister_source(self, source_name: str) -> bool:
        """Unregister a configuration source by name.

        Args:
            source_name: Target source name.

        Returns:
            bool: True if unregistered.
        """
        with self._lock:
            if source_name in self._sources_map:
                del self._sources_map[source_name]
                self._registration_order.remove(source_name)
                logger.info("Unregistered configuration source '%s'.", source_name)
                return True
            return False

    def contains(self, source_name: str) -> bool:
        """Check if a source is registered."""
        with self._lock:
            return source_name in self._sources_map

    def get_source(self, source_name: str) -> Optional[IConfigurationSource]:
        """Get registered source by name."""
        with self._lock:
            return self._sources_map.get(source_name)

    def list_sources(self) -> Tuple[IConfigurationSource, ...]:
        """List all registered configuration sources in registration order."""
        with self._lock:
            return tuple(self._sources_map[name] for name in self._registration_order)

    def sort_sources(self) -> Tuple[IConfigurationSource, ...]:
        """Get all registered configuration sources sorted by priority descending (highest priority first)."""
        with self._lock:
            sources = list(self._sources_map.values())
            sources.sort(key=lambda s: s.priority, reverse=True)
            return tuple(sources)

    def count(self) -> int:
        """Get count of registered sources."""
        with self._lock:
            return len(self._sources_map)

    def clear(self) -> None:
        """Clear all registered sources."""
        with self._lock:
            self._sources_map.clear()
            self._registration_order.clear()
            logger.info("Cleared all registered configuration sources.")
