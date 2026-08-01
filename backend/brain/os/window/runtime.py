"""Singleton accessor for Window Runtime (Phase 11.6).

Provides thread-safe singleton access for WindowRuntime coordinator.
"""

import threading
from typing import Optional

from brain.os.window.window_runtime import WindowRuntime

_window_runtime_lock = threading.RLock()
_window_instance: Optional[WindowRuntime] = None


def get_window_runtime() -> WindowRuntime:
    """Get or initialize singleton WindowRuntime instance."""
    global _window_instance
    with _window_runtime_lock:
        if _window_instance is None:
            _window_instance = WindowRuntime()
            _window_instance.initialize()
        return _window_instance


def reset_window_runtime() -> None:
    """Reset singleton instance (used for testing and teardown)."""
    global _window_instance
    with _window_runtime_lock:
        if _window_instance is not None:
            _window_instance.shutdown()
            _window_instance = None
