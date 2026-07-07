"""Temporary session-scoped memory storage for conversation sessions."""

import threading
from typing import Any, Dict


class TemporaryMemory:
    """Provides thread-safe in-memory storage for temporary session parameters."""

    def __init__(self) -> None:
        """Initializes an empty TemporaryMemory container."""
        self._data: Dict[str, Any] = {}
        self._lock = threading.Lock()

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieves a value from temporary memory.

        Args:
            key: Storage lookup key.
            default: Default value returned if key is missing.

        Returns:
            The stored value or default.
        """
        with self._lock:
            return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Saves or updates a value in temporary memory.

        Args:
            key: Storage lookup key.
            value: The data to store.
        """
        with self._lock:
            self._data[key] = value

    def delete(self, key: str) -> bool:
        """Removes a key from temporary memory.

        Args:
            key: The storage key to delete.

        Returns:
            True if the key existed and was deleted, False otherwise.
        """
        with self._lock:
            if key in self._data:
                del self._data[key]
                return True
            return False

    def clear(self) -> None:
        """Wipes all stored session data from memory."""
        with self._lock:
            self._data.clear()
