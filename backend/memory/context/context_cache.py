"""Thread-safe Context Memory Cache."""

import threading
from typing import Dict, Optional


class ContextCache:
    """Thread-safe cache storing user session context states in memory."""

    def __init__(self) -> None:
        """Initializes the cache lock and dictionary storage."""
        self._lock = threading.Lock()
        # Storage format: { f"{user_id}:{session_id}": metadata_bag_dict }
        self._store: Dict[str, dict] = {}

    def _get_cache_key(self, user_id: int, session_id: str) -> str:
        """Builds a unique cache index key."""
        return f"{user_id}:{session_id}"

    def get(self, user_id: int, session_id: str) -> Optional[dict]:
        """Retrieves a cached context state.

        Args:
            user_id: Owner user identifier.
            session_id: Active session identifier.

        Returns:
            The cached metadata_bag dictionary if hit, else None.
        """
        key = self._get_cache_key(user_id, session_id)
        with self._lock:
            return self._store.get(key)

    def set(self, user_id: int, session_id: str, metadata_bag: dict) -> None:
        """Caches a context metadata bag state.

        Args:
            user_id: Owner user identifier.
            session_id: Active session identifier.
            metadata_bag: The context dictionary state to cache.
        """
        key = self._get_cache_key(user_id, session_id)
        with self._lock:
            # Store a shallow copy to prevent external mutation side-effects
            self._store[key] = dict(metadata_bag)

    def invalidate(self, user_id: int, session_id: str) -> None:
        """Removes an active session entry from cache.

        Args:
            user_id: Owner user identifier.
            session_id: Active session identifier.
        """
        key = self._get_cache_key(user_id, session_id)
        with self._lock:
            self._store.pop(key, None)

    def clear(self, user_id: int) -> None:
        """Removes all cache entries associated with a user.

        Args:
            user_id: Owner user identifier.
        """
        prefix = f"{user_id}:"
        with self._lock:
            keys_to_remove = [k for k in self._store if k.startswith(prefix)]
            for k in keys_to_remove:
                self._store.pop(k, None)
