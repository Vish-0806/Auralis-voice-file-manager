"""Singleton accessor for Desktop Runtime (Phase 11.5).

Provides thread-safe singleton access for DesktopRuntime coordinator.
"""

import threading
from typing import Optional

from brain.os.desktop.desktop_runtime import DesktopRuntime

_desktop_runtime_lock = threading.RLock()
_desktop_instance: Optional[DesktopRuntime] = None


def get_desktop_runtime() -> DesktopRuntime:
    """Get or initialize singleton DesktopRuntime instance."""
    global _desktop_instance
    with _desktop_runtime_lock:
        if _desktop_instance is None:
            _desktop_instance = DesktopRuntime()
            _desktop_instance.initialize()
        return _desktop_instance


def reset_desktop_runtime() -> None:
    """Reset singleton instance (used for testing and teardown)."""
    global _desktop_instance
    with _desktop_runtime_lock:
        if _desktop_instance is not None:
            _desktop_instance.shutdown()
            _desktop_instance = None
