"""Global Singleton Accessors for the Execution Recovery & State Management Runtime (Phase 12.8).

Provides thread-safe accessors (get_recovery_runtime, reset_recovery_runtime) for the global RecoveryRuntime instance.
"""

import logging
import threading
from typing import Optional

from brain.execution.recovery.recovery_provider import RecoveryProvider
from brain.execution.recovery.recovery_runtime import RecoveryRuntime

logger = logging.getLogger(__name__)

_global_recovery_lock = threading.RLock()
_global_recovery_runtime: Optional[RecoveryRuntime] = None


def get_recovery_runtime(
    provider: Optional[RecoveryProvider] = None,
    reset: bool = False,
) -> RecoveryRuntime:
    """Singleton accessor for the global RecoveryRuntime instance.

    Thread-safe. Automatically initializes on creation.

    Args:
        provider: Optional RecoveryProvider instance.
        reset: If True, resets and creates a new runtime instance.

    Returns:
        RecoveryRuntime singleton instance.
    """
    global _global_recovery_runtime
    with _global_recovery_lock:
        if reset or _global_recovery_runtime is None:
            if _global_recovery_runtime is not None:
                try:
                    _global_recovery_runtime.shutdown()
                except Exception:
                    pass
            _global_recovery_runtime = RecoveryRuntime(provider=provider)
            _global_recovery_runtime.initialize()
        return _global_recovery_runtime


def reset_recovery_runtime() -> None:
    """Resets the global RecoveryRuntime instance.

    Thread-safe. Gracefully shuts down active runtime and clears singleton instance.
    """
    global _global_recovery_runtime
    with _global_recovery_lock:
        if _global_recovery_runtime is not None:
            try:
                _global_recovery_runtime.shutdown()
                _global_recovery_runtime.clear()
            except Exception:
                pass
            _global_recovery_runtime = None
        logger.debug("Global RecoveryRuntime reset")
