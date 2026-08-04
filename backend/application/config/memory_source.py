"""Memory Configuration Source (Phase 14.3.2).

Thread-safe in-memory configuration source for runtime dynamic setting and overriding.
"""

from datetime import datetime, timezone
import logging
from threading import RLock
from typing import Any, Dict, Optional, Tuple

from backend.application.config.interfaces import IConfigurationSource
from backend.application.config.models import (
    ConfigurationSourceType,
    SourceHealth,
    SourcePriority,
    SourceStatistics,
)

logger = logging.getLogger(__name__)


class MemoryConfigurationSource(IConfigurationSource):
    """Production thread-safe in-memory configuration source."""

    def __init__(
        self,
        source_name: str = "memory_source",
        priority: int = int(SourcePriority.MEMORY),
        initial_values: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize MemoryConfigurationSource.

        Args:
            source_name: Unique source identifier string.
            priority: Numerical priority level (default 500).
            initial_values: Optional initial dictionary of key-value pairs.
        """
        self._lock = RLock()
        self._source_name = source_name
        self._priority = priority
        self._enabled = True
        self._store: Dict[str, Any] = dict(initial_values or {})

        # Statistics Counters
        self._lookups_count: int = 0
        self._hits_count: int = 0
        self._misses_count: int = 0

    @property
    def source_name(self) -> str:
        """Get unique name of the configuration source."""
        with self._lock:
            return self._source_name

    @property
    def source_type(self) -> ConfigurationSourceType:
        """Get source provider type."""
        return ConfigurationSourceType.MEMORY

    @property
    def priority(self) -> int:
        """Get numerical priority level."""
        with self._lock:
            return self._priority

    @property
    def enabled(self) -> bool:
        """Check if source is enabled."""
        with self._lock:
            return self._enabled

    def set(self, key: str, value: Any) -> None:
        """Set a configuration property in memory.

        Args:
            key: Configuration key string.
            value: Value to store.
        """
        with self._lock:
            self._store[key] = value
            logger.debug("MemoryConfigurationSource set '%s' = %s", key, value)

    def remove(self, key: str) -> bool:
        """Remove a key from memory store.

        Args:
            key: Configuration key string.

        Returns:
            bool: True if key was present and removed.
        """
        with self._lock:
            if key in self._store:
                del self._store[key]
                logger.debug("MemoryConfigurationSource removed '%s'", key)
                return True
            return False

    def clear(self) -> None:
        """Clear all entries from memory store."""
        with self._lock:
            self._store.clear()

    def contains(self, key: str) -> bool:
        """Check if key exists in memory store."""
        with self._lock:
            return key in self._store

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get value for key from memory store."""
        with self._lock:
            self._lookups_count += 1
            if key in self._store:
                self._hits_count += 1
                return self._store[key]
            self._misses_count += 1
            return default

    def keys(self) -> Tuple[str, ...]:
        """Get all keys in memory store."""
        with self._lock:
            return tuple(self._store.keys())

    def values(self) -> Tuple[Any, ...]:
        """Get all values in memory store."""
        with self._lock:
            return tuple(self._store.values())

    def items(self) -> Tuple[Tuple[str, Any], ...]:
        """Get all (key, value) tuples in memory store."""
        with self._lock:
            return tuple(self._store.items())

    def health(self) -> SourceHealth:
        """Get health status of memory source."""
        with self._lock:
            return SourceHealth(
                is_healthy=self._enabled,
                source_name=self._source_name,
                checked_at=datetime.now(timezone.utc),
            )

    def statistics(self) -> SourceStatistics:
        """Get metrics of memory source."""
        with self._lock:
            return SourceStatistics(
                total_keys=len(self._store),
                lookups_count=self._lookups_count,
                hits_count=self._hits_count,
                misses_count=self._misses_count,
                metrics={
                    "total_keys": float(len(self._store)),
                    "lookups_count": float(self._lookups_count),
                    "hits_count": float(self._hits_count),
                    "misses_count": float(self._misses_count),
                },
            )
