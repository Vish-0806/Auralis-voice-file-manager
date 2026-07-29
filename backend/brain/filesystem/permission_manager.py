"""Permission Manager for the Auralis Filesystem Engine (Phase 9.5).

Provides thread-safe, cached filesystem permission checking.
Does NOT perform filesystem mutations.
"""

import logging
import os
import threading
import time
from typing import Dict, Optional, Tuple

from brain.filesystem.filesystem_models import PermissionResult

logger = logging.getLogger(__name__)

# Default permission cache TTL in seconds
_DEFAULT_CACHE_TTL: float = 30.0
# Maximum number of entries in the permission cache
_DEFAULT_CACHE_SIZE: int = 512


class PermissionManager:
    """Thread-safe filesystem permission checker with LRU-style TTL cache.

    Responsibilities:
    - Check read / write / delete / execute permissions per path.
    - Cache results to avoid redundant ``os.access()`` calls on hot paths.
    - Invalidate cached entries after a configurable TTL.
    - Allow explicit cache invalidation after write / delete operations.

    Does NOT mutate the filesystem.
    """

    def __init__(
        self,
        cache_ttl_seconds: float = _DEFAULT_CACHE_TTL,
        max_cache_size: int = _DEFAULT_CACHE_SIZE,
    ) -> None:
        """Initializes PermissionManager.

        Args:
            cache_ttl_seconds: Seconds before a cached permission entry expires.
            max_cache_size: Maximum number of paths to keep in cache.
        """
        self._lock = threading.RLock()
        self._cache_ttl = cache_ttl_seconds
        self._max_cache_size = max_cache_size
        # cache maps path -> (PermissionResult, expiry_timestamp)
        self._cache: Dict[str, Tuple[PermissionResult, float]] = {}
        logger.debug(
            "PermissionManager initialized ttl=%.1fs max_size=%d",
            cache_ttl_seconds,
            max_cache_size,
        )

    # ------------------------------------------------------------------
    # Public Convenience Methods
    # ------------------------------------------------------------------

    def check_read(self, path: str) -> bool:
        """Return True if the current process can read *path*.

        Args:
            path: Filesystem path to check.

        Returns:
            True if readable, False otherwise.
        """
        return self.validate(path).can_read

    def check_write(self, path: str) -> bool:
        """Return True if the current process can write to *path*.

        Args:
            path: Filesystem path to check.

        Returns:
            True if writable, False otherwise.
        """
        return self.validate(path).can_write

    def check_delete(self, path: str) -> bool:
        """Return True if the current process can delete *path*.

        Deletion requires write permission on the *parent* directory.

        Args:
            path: Filesystem path to check.

        Returns:
            True if deletable, False otherwise.
        """
        result = self.validate(path)
        # Also need write on parent to unlink
        parent = os.path.dirname(path) or "."
        parent_result = self.validate(parent)
        return result.exists and parent_result.can_write

    def check_execute(self, path: str) -> bool:
        """Return True if the current process can execute *path*.

        Args:
            path: Filesystem path to check.

        Returns:
            True if executable, False otherwise.
        """
        return self.validate(path).can_execute

    def check_directory(self, path: str) -> bool:
        """Return True if *path* is a directory that is writable and listable.

        Args:
            path: Directory path to check.

        Returns:
            True if path is a writable, readable directory.
        """
        result = self.validate(path)
        return result.is_directory and result.can_read and result.can_write

    # ------------------------------------------------------------------
    # Core Validation
    # ------------------------------------------------------------------

    def validate(self, path: str) -> PermissionResult:
        """Return a :class:`PermissionResult` for *path*, using the cache.

        Args:
            path: Filesystem path to validate.

        Returns:
            Immutable ``PermissionResult`` snapshot.
        """
        with self._lock:
            cached = self._get_cached(path)
            if cached is not None:
                return cached

            result = self._check_permissions(path)
            self._set_cached(path, result)
            return result

    def invalidate(self, path: str) -> None:
        """Remove *path* (and its parent) from the permission cache.

        Should be called after any write or delete operation so that
        subsequent checks reflect the updated state.

        Args:
            path: Filesystem path to evict from cache.
        """
        with self._lock:
            self._cache.pop(path, None)
            parent = os.path.dirname(path) or "."
            self._cache.pop(parent, None)
            logger.debug("PermissionManager: cache invalidated for path=%s", path)

    def clear_cache(self) -> None:
        """Evict all entries from the permission cache."""
        with self._lock:
            self._cache.clear()
            logger.debug("PermissionManager: cache cleared")

    def cache_size(self) -> int:
        """Return the number of entries currently in the cache."""
        with self._lock:
            return len(self._cache)

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    def _check_permissions(self, path: str) -> PermissionResult:
        """Perform the actual OS-level permission checks.

        Args:
            path: Filesystem path to inspect.

        Returns:
            Fresh :class:`PermissionResult`.
        """
        try:
            exists = os.path.exists(path)
            is_dir = os.path.isdir(path) if exists else False
            can_read = os.access(path, os.R_OK) if exists else False
            can_write = os.access(path, os.W_OK) if exists else False
            can_execute = os.access(path, os.X_OK) if exists else False
            # Delete: need write on parent
            parent = os.path.dirname(path) or "."
            parent_writable = os.access(parent, os.W_OK) if os.path.exists(parent) else False
            can_delete = exists and parent_writable

            return PermissionResult(
                path=path,
                can_read=can_read,
                can_write=can_write,
                can_delete=can_delete,
                can_execute=can_execute,
                is_directory=is_dir,
                exists=exists,
            )
        except Exception as exc:
            logger.warning("PermissionManager._check_permissions error path=%s: %s", path, exc)
            return PermissionResult(path=path)

    def _get_cached(self, path: str) -> Optional[PermissionResult]:
        """Return cached result if it has not expired, otherwise None."""
        entry = self._cache.get(path)
        if entry is None:
            return None
        result, expiry = entry
        if time.monotonic() > expiry:
            del self._cache[path]
            return None
        return result

    def _set_cached(self, path: str, result: PermissionResult) -> None:
        """Store result in cache, evicting oldest entry if at capacity."""
        if len(self._cache) >= self._max_cache_size:
            # Evict oldest entry (insertion-ordered dict on Python 3.7+)
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
        expiry = time.monotonic() + self._cache_ttl
        self._cache[path] = (result, expiry)
