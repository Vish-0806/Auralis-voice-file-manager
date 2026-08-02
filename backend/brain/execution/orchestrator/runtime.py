"""Global Singleton Accessors for the Command Execution Orchestrator (Phase 12.3).

Provides thread-safe accessors (get_orchestrator_runtime, reset_orchestrator_runtime) for the global ExecutionRuntime instance.
"""

import logging
import threading
from typing import Optional

from brain.execution.orchestrator.execution_provider import ExecutionProvider
from brain.execution.orchestrator.execution_runtime import ExecutionRuntime

logger = logging.getLogger(__name__)

_global_orchestrator_lock = threading.RLock()
_global_orchestrator_runtime: Optional[ExecutionRuntime] = None


def get_orchestrator_runtime(
    provider: Optional[ExecutionProvider] = None,
    reset: bool = False,
) -> ExecutionRuntime:
    """Singleton accessor for the global ExecutionRuntime orchestrator instance.

    Thread-safe. Automatically initializes on creation.

    Args:
        provider: Optional ExecutionProvider instance.
        reset: If True, resets and creates a new runtime instance.

    Returns:
        ExecutionRuntime singleton instance.
    """
    global _global_orchestrator_runtime
    with _global_orchestrator_lock:
        if reset or _global_orchestrator_runtime is None:
            if _global_orchestrator_runtime is not None:
                try:
                    _global_orchestrator_runtime.shutdown()
                except Exception:
                    pass
            _global_orchestrator_runtime = ExecutionRuntime(provider=provider)
            _global_orchestrator_runtime.initialize()
        return _global_orchestrator_runtime


def reset_orchestrator_runtime() -> None:
    """Resets the global ExecutionRuntime orchestrator instance.

    Thread-safe. Gracefully shuts down active runtime and clears singleton instance.
    """
    global _global_orchestrator_runtime
    with _global_orchestrator_lock:
        if _global_orchestrator_runtime is not None:
            try:
                _global_orchestrator_runtime.shutdown()
                _global_orchestrator_runtime.clear()
            except Exception:
                pass
            _global_orchestrator_runtime = None
        logger.debug("Global Orchestrator ExecutionRuntime reset")
