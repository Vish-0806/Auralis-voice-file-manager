"""Singleton accessor for Filesystem Runtime (Phase 11.2).

Provides thread-safe singleton access for FilesystemRuntime coordinator.
"""

import threading
from typing import Optional

from brain.os.filesystem.filesystem_runtime import FilesystemRuntime

_filesystem_runtime_lock = threading.RLock()
_filesystem_instance: Optional[FilesystemRuntime] = None


def get_filesystem_runtime() -> FilesystemRuntime:
    """Get or initialize singleton FilesystemRuntime instance."""
    global _filesystem_instance
    with _filesystem_runtime_lock:
        if _filesystem_instance is None:
            _filesystem_instance = FilesystemRuntime()
            _filesystem_instance.initialize()
        return _filesystem_instance


def reset_filesystem_runtime() -> None:
    """Reset singleton instance (used for testing and teardown)."""
    global _filesystem_instance
    with _filesystem_runtime_lock:
        if _filesystem_instance is not None:
            _filesystem_instance.shutdown()
            _filesystem_instance = None
