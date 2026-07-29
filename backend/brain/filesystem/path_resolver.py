"""Path Resolver for the Auralis Filesystem Engine (Phase 9.5).

Provides secure, cross-platform path normalization, resolution, and traversal-prevention.
Does NOT perform any filesystem mutations. All operations are pure path transformations.
"""

import logging
import os
import threading
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class PathResolver:
    """Thread-safe, cross-platform path normalization and safety checker.

    Responsibilities:
    - Normalize paths (collapse ``..``, handle separators).
    - Expand environment variables and ``~`` user shorthand.
    - Validate canonical paths against a configured base directory.
    - Prevent directory-traversal attacks.

    Does NOT interact with the filesystem beyond ``Path.resolve()`` /
    ``os.path`` utilities.
    """

    def __init__(self, base_path: Optional[str] = None) -> None:
        """Initializes PathResolver with an optional base (jail) path.

        Args:
            base_path: If provided, ``is_safe()`` rejects any resolved path
                       that escapes this directory.  Defaults to the current
                       working directory.
        """
        self._lock = threading.RLock()
        self._base_path: Path = Path(base_path).resolve() if base_path else Path.cwd()
        logger.debug("PathResolver initialized with base_path=%s", self._base_path)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def resolve(self, path: str) -> str:
        """Normalize, expand variables, expand user, and make path absolute.

        Args:
            path: Raw path string (may contain ``~``, ``$ENV``, ``..``).

        Returns:
            Absolute, normalized path string.
        """
        with self._lock:
            return str(self._resolve_internal(path))

    def is_safe(self, path: str, base: Optional[str] = None) -> bool:
        """Return True if the resolved path stays within the jail directory.

        Prevents directory-traversal attacks (e.g. ``../../etc/passwd``).

        Args:
            path: Path to validate.
            base: Override jail root.  Falls back to ``self._base_path``.

        Returns:
            True if the resolved path is inside *base*, False otherwise.
        """
        with self._lock:
            try:
                resolved = self._resolve_internal(path)
                jail = Path(base).resolve() if base else self._base_path
                # ``Path.is_relative_to`` available from Python 3.9+
                try:
                    resolved.relative_to(jail)
                    return True
                except ValueError:
                    logger.warning(
                        "PathResolver.is_safe: traversal detected path=%s jail=%s",
                        resolved,
                        jail,
                    )
                    return False
            except Exception as exc:
                logger.warning("PathResolver.is_safe error: %s", exc)
                return False

    def canonicalize(self, path: str) -> str:
        """Resolve symlinks and return the real (canonical) path.

        Falls back to the normalized non-symlink path if the path does not
        exist on the filesystem (symlinks can only be resolved for existing
        paths).

        Args:
            path: Path to canonicalize.

        Returns:
            Canonical (real) path string.
        """
        with self._lock:
            try:
                p = self._resolve_internal(path)
                # os.path.realpath resolves symlinks without requiring existence
                return os.path.realpath(str(p))
            except Exception as exc:
                logger.warning("PathResolver.canonicalize error for path=%s: %s", path, exc)
                return self.resolve(path)

    def normalize(self, path: str) -> str:
        """Return the normalized path without expanding ~ or env vars.

        Useful when the caller has already performed expansion and only
        needs ``os.path.normpath``-style cleanup.

        Args:
            path: Path string to normalize.

        Returns:
            Normalized path string.
        """
        with self._lock:
            return str(Path(os.path.normpath(path)))

    def join(self, *parts: str) -> str:
        """Join and normalize multiple path components.

        Args:
            *parts: Path components to join.

        Returns:
            Joined, normalized path string.
        """
        with self._lock:
            return str(Path(*parts))

    def parent(self, path: str) -> str:
        """Return the parent directory of a path.

        Args:
            path: Path string.

        Returns:
            Parent directory path string.
        """
        with self._lock:
            return str(self._resolve_internal(path).parent)

    def name(self, path: str) -> str:
        """Return the final component (filename or directory name) of a path.

        Args:
            path: Path string.

        Returns:
            Final path component string.
        """
        with self._lock:
            return Path(path).name

    def stem(self, path: str) -> str:
        """Return the filename without its extension.

        Args:
            path: Path string.

        Returns:
            Filename stem string.
        """
        with self._lock:
            return Path(path).stem

    def suffix(self, path: str) -> str:
        """Return the file extension (including the leading dot).

        Args:
            path: Path string.

        Returns:
            Extension string, e.g. ``'.txt'``.  Empty string if no extension.
        """
        with self._lock:
            return Path(path).suffix

    def get_base_path(self) -> str:
        """Return the configured jail (base) path.

        Returns:
            Base path string.
        """
        with self._lock:
            return str(self._base_path)

    def set_base_path(self, base_path: str) -> None:
        """Update the jail directory.

        Args:
            base_path: New base path string.
        """
        with self._lock:
            self._base_path = Path(base_path).resolve()
            logger.debug("PathResolver base_path updated to %s", self._base_path)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_internal(self, path: str) -> Path:
        """Expand user, expand vars, and create an absolute ``Path``.

        Uses ``Path.expanduser()`` for ``~`` and ``os.path.expandvars``
        for ``$VARIABLE`` / ``%VARIABLE%`` (Windows) references.

        Args:
            path: Raw path string.

        Returns:
            Absolute ``Path`` object.
        """
        expanded = os.path.expandvars(path)
        p = Path(expanded).expanduser()
        if not p.is_absolute():
            p = self._base_path / p
        return p.resolve() if _path_exists_or_can_resolve(p) else Path(os.path.normpath(str(p)))


def _path_exists_or_can_resolve(p: Path) -> bool:
    """Return True if the path exists (or its parent does) so resolve() is safe.

    ``Path.resolve()`` on a non-existent path works on Python 3.6+ but
    may raise on some platforms if intermediate components are missing.
    We attempt it and fall back gracefully.
    """
    try:
        p.resolve()
        return True
    except (OSError, RuntimeError):
        return False
