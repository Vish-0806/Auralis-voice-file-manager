"""DotEnv Configuration Source (Phase 14.3.2).

Lazy loading read-only configuration source for .env files.
"""

from datetime import datetime, timezone
import logging
from pathlib import Path
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


class DotEnvConfigurationSource(IConfigurationSource):
    """Production read-only .env file configuration source."""

    def __init__(
        self,
        filepath: str = ".env",
        source_name: str = "dotenv_source",
        priority: int = int(SourcePriority.DOTENV),
    ) -> None:
        """Initialize DotEnvConfigurationSource.

        Args:
            filepath: Path to target .env file.
            source_name: Unique source identifier string.
            priority: Priority level (default 300).
        """
        self._lock = RLock()
        self._filepath = Path(filepath)
        self._source_name = source_name
        self._priority = priority
        self._enabled = True
        self._is_loaded = False
        self._store: Dict[str, str] = {}

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
        return ConfigurationSourceType.DOTENV

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

    def _ensure_loaded(self) -> None:
        """Lazy load .env file contents into memory store."""
        if self._is_loaded:
            return

        self._is_loaded = True
        if not self._filepath.exists():
            logger.info("DotEnv file '%s' does not exist. Skipping.", self._filepath)
            return

        try:
            # Attempt using python-dotenv if installed
            try:
                # pyrefly: ignore [missing-import]
                from dotenv import dotenv_values
                values = dotenv_values(self._filepath)
                self._store = {k: str(v) for k, v in values.items() if k and v is not None}
            except ImportError:
                # Custom line-by-line fallback parser
                self._store = {}
                with open(self._filepath, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        k, v = line.split("=", 1)
                        self._store[k.strip()] = v.strip().strip("'\"")

            logger.info("Loaded %d properties from DotEnv file '%s'.", len(self._store), self._filepath)
        except Exception as exc:
            logger.warning("Failed to load DotEnv file '%s': %s", self._filepath, exc)

    def contains(self, key: str) -> bool:
        """Check if key exists in .env source."""
        with self._lock:
            self._ensure_loaded()
            return key in self._store

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get value for key from .env source."""
        with self._lock:
            self._ensure_loaded()
            self._lookups_count += 1
            if key in self._store:
                self._hits_count += 1
                return self._store[key]
            self._misses_count += 1
            return default

    def keys(self) -> Tuple[str, ...]:
        """Get all keys in .env source."""
        with self._lock:
            self._ensure_loaded()
            return tuple(self._store.keys())

    def values(self) -> Tuple[Any, ...]:
        """Get all values in .env source."""
        with self._lock:
            self._ensure_loaded()
            return tuple(self._store.values())

    def items(self) -> Tuple[Tuple[str, Any], ...]:
        """Get all (key, value) pairs in .env source."""
        with self._lock:
            self._ensure_loaded()
            return tuple(self._store.items())

    def health(self) -> SourceHealth:
        """Get health assessment of .env source."""
        with self._lock:
            is_healthy = self._enabled and (not self._filepath.exists() or self._filepath.is_file())
            issues = () if is_healthy else (f"DotEnv file path '{self._filepath}' is invalid.",)
            return SourceHealth(
                is_healthy=is_healthy,
                source_name=self._source_name,
                issues=issues,
                checked_at=datetime.now(timezone.utc),
            )

    def statistics(self) -> SourceStatistics:
        """Get metrics of .env source."""
        with self._lock:
            self._ensure_loaded()
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
