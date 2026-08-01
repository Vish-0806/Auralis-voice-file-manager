"""Singleton accessor for Process Runtime (Phase 11.4).

Provides thread-safe singleton access for ProcessRuntime coordinator.
"""

import threading
from typing import Optional

from brain.os.process.process_runtime import ProcessRuntime

_process_runtime_lock = threading.RLock()
_process_instance: Optional[ProcessRuntime] = None


def get_process_runtime() -> ProcessRuntime:
    """Get or initialize singleton ProcessRuntime instance."""
    global _process_instance
    with _process_runtime_lock:
        if _process_instance is None:
            _process_instance = ProcessRuntime()
            _process_instance.initialize()
        return _process_instance


def reset_process_runtime() -> None:
    """Reset singleton instance (used for testing and teardown)."""
    global _process_instance
    with _process_runtime_lock:
        if _process_instance is not None:
            _process_instance.shutdown()
            _process_instance = None
