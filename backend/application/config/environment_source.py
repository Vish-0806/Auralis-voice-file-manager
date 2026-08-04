"""Environment Configuration Source (Phase 14.3.2).

Read-only configuration source reading environment variables from os.environ.
"""

from datetime import datetime, timezone
import logging
import os
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


class EnvironmentConfigurationSource(IConfigurationSource):
    """Production read-only environment variable configuration source."""

    def __init__(
        self,
        source_name: str = "environment_source",
        priority: int = int(SourcePriority.ENVIRONMENT),
        prefix: Optional[str] = None,
    ) -> None:
        """Initialize EnvironmentConfigurationSource.

        Args:
            source_name: Unique source name.
            priority: Priority level (default 400).
            prefix: Optional environment key prefix string (e.g. 'AURALIS_').
        """
        self._lock = RLock()
        self._source_name = source_name
        self._priority = priority
        self._prefix = prefix or ""
        self._enabled = True

        # Statistics Counters
        self._lookups_count: int = 0
        self._hits_count: int = 0
        self._misses_count: int = 0

    @property
    def source_name(self) -> str:
        """Get source name."""
        with self._lock:
            return self._source_name

    @property
    def source_type(self) -> ConfigurationSourceType:
        """Get source type."""
        return ConfigurationSourceType.ENVIRONMENT

    @property
    def priority(self) -> int:
        """Get priority level."""
        with self._lock:
            return self._priority

    @property
    def enabled(self) -> bool:
        """Check if source is enabled."""
        with self._lock:
            return self._enabled

    def _env_key(self, key: str) -> str:
        """Format configuration key with optional prefix."""
        if self._prefix and not key.startswith(self._prefix):
            return f"{self._prefix}{key}"
        return key

    def contains(self, key: str) -> bool:
        """Check if environment variable exists."""
        with self._lock:
            env_key = self._env_key(key)
            return env_key in os.environ or key in os.environ

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get value from os.environ."""
        with self._lock:
            self._lookups_count += 1
            env_key = self._env_key(key)

            if env_key in os.environ:
                self._hits_count += 1
                return os.environ[env_key]
            elif key in os.environ:
                self._hits_count += 1
                return os.environ[key]

            self._misses_count += 1
            return default

    def keys(self) -> Tuple[str, ...]:
        """Get all matching environment variable keys."""
        with self._lock:
            if not self._prefix:
                return tuple(os.environ.keys())
            return tuple(k for k in os.environ.keys() if k.startswith(self._prefix))

    def values(self) -> Tuple[Any, ...]:
        """Get all matching environment variable values."""
        with self._lock:
            keys = self.keys()
            return tuple(os.environ[k] for k in keys)

    def items(self) -> Tuple[Tuple[str, Any], ...]:
        """Get all matching (key, value) pairs."""
        with self._lock:
            keys = self.keys()
            return tuple((k, os.environ[k]) for k in keys)

    def health(self) -> SourceHealth:
        """Get health assessment of environment source."""
        with self._lock:
            return SourceHealth(
                is_healthy=self._enabled,
                source_name=self._source_name,
                checked_at=datetime.now(timezone.utc),
            )

    def statistics(self) -> SourceStatistics:
        """Get metrics of environment source."""
        with self._lock:
            total = len(self.keys())
            return SourceStatistics(
                total_keys=total,
                lookups_count=self._lookups_count,
                hits_count=self._hits_count,
                misses_count=self._misses_count,
                metrics={
                    "total_keys": float(total),
                    "lookups_count": float(self._lookups_count),
                    "hits_count": float(self._hits_count),
                    "misses_count": float(self._misses_count),
                },
            )
