"""Global Singleton Accessors for the Execution Runtime Integration (Phase 12.9).

Provides thread-safe accessors (get_execution_runtime, reset_execution_runtime) for the global ExecutionRuntime instance.
"""

import logging
import threading
from typing import Optional

from brain.execution.integration.execution_provider import ExecutionProvider
from brain.execution.integration.execution_runtime import ExecutionRuntime

logger = logging.getLogger(__name__)

_global_integration_lock = threading.RLock()
_global_integration_runtime: Optional[ExecutionRuntime] = None


def get_execution_runtime(
    provider: Optional[ExecutionProvider] = None,
    reset: bool = False,
) -> ExecutionRuntime:
    """Singleton accessor for the global ExecutionRuntime instance.

    Thread-safe. Automatically initializes on creation.

    Args:
        provider: Optional ExecutionProvider instance.
        reset: If True, resets and creates a new runtime instance.

    Returns:
        ExecutionRuntime singleton instance.
    """
    global _global_integration_runtime
    with _global_integration_lock:
        if reset or _global_integration_runtime is None:
            if _global_integration_runtime is not None:
                try:
                    _global_integration_runtime.shutdown()
                except Exception:
                    pass
            _global_integration_runtime = ExecutionRuntime(provider=provider)
            _global_integration_runtime.initialize()
        return _global_integration_runtime


def reset_execution_runtime() -> None:
    """Resets the global ExecutionRuntime instance.

    Thread-safe. Gracefully shuts down active runtime and clears singleton instance.
    """
    global _global_integration_runtime
    with _global_integration_lock:
        if _global_integration_runtime is not None:
            try:
                _global_integration_runtime.shutdown()
                _global_integration_runtime.clear()
            except Exception:
                pass
            _global_integration_runtime = None
        logger.debug("Global ExecutionRuntime reset")
