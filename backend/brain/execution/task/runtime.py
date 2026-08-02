"""Global Singleton Accessors for the Task Management Runtime (Phase 12.5).

Provides thread-safe accessors (get_task_runtime, reset_task_runtime) for the global TaskRuntime instance.
"""

import logging
import threading
from typing import Optional

from brain.execution.task.task_provider import TaskProvider
from brain.execution.task.task_runtime import TaskRuntime

logger = logging.getLogger(__name__)

_global_task_lock = threading.RLock()
_global_task_runtime: Optional[TaskRuntime] = None


def get_task_runtime(
    provider: Optional[TaskProvider] = None,
    reset: bool = False,
) -> TaskRuntime:
    """Singleton accessor for the global TaskRuntime instance.

    Thread-safe. Automatically initializes on creation.

    Args:
        provider: Optional TaskProvider instance.
        reset: If True, resets and creates a new runtime instance.

    Returns:
        TaskRuntime singleton instance.
    """
    global _global_task_runtime
    with _global_task_lock:
        if reset or _global_task_runtime is None:
            if _global_task_runtime is not None:
                try:
                    _global_task_runtime.shutdown()
                except Exception:
                    pass
            _global_task_runtime = TaskRuntime(provider=provider)
            _global_task_runtime.initialize()
        return _global_task_runtime


def reset_task_runtime() -> None:
    """Resets the global TaskRuntime instance.

    Thread-safe. Gracefully shuts down active runtime and clears singleton instance.
    """
    global _global_task_runtime
    with _global_task_lock:
        if _global_task_runtime is not None:
            try:
                _global_task_runtime.shutdown()
                _global_task_runtime.clear()
            except Exception:
                pass
            _global_task_runtime = None
        logger.debug("Global TaskRuntime reset")
