"""Singleton accessor for Operating System Runtime (Phase 11.1).

Provides thread-safe singleton management for OperatingSystemRuntime coordinator.
"""

import threading
from typing import Optional

from brain.os.os_runtime import OperatingSystemRuntime

_runtime_lock = threading.RLock()
_instance: Optional[OperatingSystemRuntime] = None


def get_os_runtime() -> OperatingSystemRuntime:
    """Get or initialize the singleton OperatingSystemRuntime instance."""
    global _instance
    with _runtime_lock:
        if _instance is None:
            _instance = OperatingSystemRuntime()
            _instance.initialize()
        return _instance


def reset_os_runtime() -> None:
    """Reset singleton instance (primarily for testing and clean teardown)."""
    global _instance
    with _runtime_lock:
        if _instance is not None:
            _instance.shutdown()
            _instance = None
