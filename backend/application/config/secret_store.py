"""Secret Store (Phase 14.3.5).

Thread-safe in-memory secure storage abstraction for secret entries.
No persistence, memory-only execution.
"""

from datetime import datetime, timezone
import logging
from threading import RLock
from typing import Dict, List, Optional, Tuple, Any

from backend.application.config.exceptions import ConfigurationSourceError
from backend.application.config.models import (
    SecretEntry,
    SecretSnapshot,
)

logger = logging.getLogger(__name__)


class SecretStore:
    """Production thread-safe in-memory secret store."""

    def __init__(self) -> None:
        """Initialize SecretStore."""
        self._lock = RLock()
        self._store: Dict[str, SecretEntry] = {}

    def register_secret(self, entry: SecretEntry) -> bool:
        """Register a new secret entry.

        Args:
            entry: Target SecretEntry model.

        Returns:
            bool: True if registered.

        Raises:
            ConfigurationSourceError: If secret_name is invalid or already registered.
        """
        if entry is None or not entry.secret_name:
            raise ConfigurationSourceError("Cannot register invalid or nameless secret.")

        with self._lock:
            name = entry.secret_name
            if name in self._store:
                raise ConfigurationSourceError(f"Secret '{name}' is already registered in store.")

            self._store[name] = entry
            logger.info("Registered secret metadata for secret_name='%s' (type=%s).", name, entry.secret_type.value)
            return True

    def update_secret(self, entry: SecretEntry) -> bool:
        """Update an existing secret entry.

        Args:
            entry: Updated SecretEntry model.

        Returns:
            bool: True if updated.
        """
        if entry is None or not entry.secret_name:
            return False

        with self._lock:
            name = entry.secret_name
            if name in self._store:
                self._store[name] = entry
                logger.info("Updated secret metadata for secret_name='%s'.", name)
                return True
            return False

    def remove_secret(self, secret_name: str) -> bool:
        """Remove a secret entry from store.

        Args:
            secret_name: Target secret name string.

        Returns:
            bool: True if removed.
        """
        with self._lock:
            if secret_name in self._store:
                del self._store[secret_name]
                logger.info("Removed secret secret_name='%s'.", secret_name)
                return True
            return False

    def contains(self, secret_name: str) -> bool:
        """Check if secret exists in store."""
        with self._lock:
            return secret_name in self._store

    def get_secret(self, secret_name: str) -> Optional[SecretEntry]:
        """Get SecretEntry model by name."""
        with self._lock:
            return self._store.get(secret_name)

    def list_secret_names(self) -> Tuple[str, ...]:
        """List all registered secret names."""
        with self._lock:
            return tuple(self._store.keys())

    def create_snapshot(self) -> SecretSnapshot:
        """Create an immutable snapshot containing metadata and redacted values only."""
        with self._lock:
            meta_list: List[Dict[str, Any]] = []
            redacted_map: Dict[str, str] = {}

            for entry in self._store.values():
                meta_list.append(
                    {
                        "secret_name": entry.secret_name,
                        "secret_type": entry.secret_type.value,
                        "allow_read": entry.policy.allow_read,
                        "allow_export": entry.policy.allow_export,
                        "created_at": entry.created_at.isoformat(),
                    }
                )
                redacted_map[entry.secret_name] = entry.redacted_value

            return SecretSnapshot(
                registered_secrets_metadata=tuple(meta_list),
                redacted_values=redacted_map,
                created_at=datetime.now(timezone.utc),
            )

    def clear(self) -> None:
        """Clear all secret entries from memory."""
        with self._lock:
            self._store.clear()
            logger.info("Cleared all secret entries from SecretStore.")
