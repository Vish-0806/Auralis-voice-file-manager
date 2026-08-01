"""Singleton accessor for Application Runtime (Phase 11.3).

Provides thread-safe singleton access for ApplicationRuntime coordinator.
"""

import threading
from typing import Optional

from brain.os.application.application_runtime import ApplicationRuntime

_application_runtime_lock = threading.RLock()
_application_instance: Optional[ApplicationRuntime] = None


def get_application_runtime() -> ApplicationRuntime:
    """Get or initialize singleton ApplicationRuntime instance."""
    global _application_instance
    with _application_runtime_lock:
        if _application_instance is None:
            _application_instance = ApplicationRuntime()
            _application_instance.initialize()
        return _application_instance


def reset_application_runtime() -> None:
    """Reset singleton instance (used for testing and teardown)."""
    global _application_instance
    with _application_runtime_lock:
        if _application_instance is not None:
            _application_instance.shutdown()
            _application_instance = None
