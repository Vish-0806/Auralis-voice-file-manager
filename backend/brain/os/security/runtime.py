"""Singleton accessor for Security Runtime (Phase 11.8).

Provides thread-safe singleton access for SecurityRuntime coordinator.
"""

import threading
from typing import Optional

from brain.os.security.security_runtime import SecurityRuntime

_security_runtime_lock = threading.RLock()
_security_instance: Optional[SecurityRuntime] = None


def get_security_runtime() -> SecurityRuntime:
    """Get or initialize singleton SecurityRuntime instance."""
    global _security_instance
    with _security_runtime_lock:
        if _security_instance is None:
            _security_instance = SecurityRuntime()
            _security_instance.initialize()
        return _security_instance


def reset_security_runtime() -> None:
    """Reset singleton instance (used for testing and teardown)."""
    global _security_instance
    with _security_runtime_lock:
        if _security_instance is not None:
            _security_instance.shutdown()
            _security_instance = None
