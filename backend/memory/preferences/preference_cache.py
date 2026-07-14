"""Thread-safe TTL-based User Preference Cache."""

import time
import threading
from typing import Any, Dict, Optional, Tuple


class PreferenceCache:
    """In-memory cache for user preferences with TTL expiration and thread safety."""

    def __init__(self, ttl_seconds: int = 300) -> None:
        """Initializes the cache.

        Args:
            ttl_seconds: Duration in seconds to retain cache entries. Defaults to 300.
        """
        self._ttl = ttl_seconds
        self._lock = threading.Lock()
        # Storage format: { f"{user_id}:{category}:{key}": (value, expiry_timestamp) }
        self._store: Dict[str, Tuple[Any, float]] = {}

    def _get_cache_key(self, user_id: int, category: str, key: str) -> str:
        """Builds a unique cache index key."""
        return f"{user_id}:{category.lower()}:{key.lower()}"

    def get(self, user_id: int, category: str, key: str) -> Optional[Any]:
        """Retrieves a value from the cache if present and not expired.

        Args:
            user_id: Owner user identifier.
            category: Preference category.
            key: Preference key name.

        Returns:
            The cached value if hit, else None.
        """
        cache_key = self._get_cache_key(user_id, category, key)
        with self._lock:
            entry = self._store.get(cache_key)
            if entry is None:
                return None

            val, expiry = entry
            if time.time() > expiry:
                # Expired: Remove from cache
                self._store.pop(cache_key, None)
                return None

            return val

    def set(self, user_id: int, category: str, key: str, value: Any) -> None:
        """Saves a value in the cache with a configured TTL expiry.

        Args:
            user_id: Owner user identifier.
            category: Preference category.
            key: Preference key name.
            value: Setting value to cache.
        """
        cache_key = self._get_cache_key(user_id, category, key)
        expiry = time.time() + self._ttl
        with self._lock:
            self._store[cache_key] = (value, expiry)

    def invalidate(self, user_id: int, category: str, key: str) -> None:
        """Removes a specific entry from the cache.

        Args:
            user_id: Owner user identifier.
            category: Preference category.
            key: Preference key name.
        """
        cache_key = self._get_cache_key(user_id, category, key)
        with self._lock:
            self._store.pop(cache_key, None)

    def clear(self, user_id: int) -> None:
        """Removes all cache entries associated with a specific user.

        Args:
            user_id: Owner user identifier.
        """
        prefix = f"{user_id}:"
        with self._lock:
            keys_to_remove = [k for k in self._store if k.startswith(prefix)]
            for k in keys_to_remove:
                self._store.pop(k, None)
