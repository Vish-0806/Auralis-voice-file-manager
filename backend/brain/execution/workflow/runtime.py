"""Global Singleton Accessors for the Workflow Execution Engine (Phase 12.4).

Provides thread-safe accessors (get_workflow_runtime, reset_workflow_runtime) for the global WorkflowRuntime instance.
"""

import logging
import threading
from typing import Optional

from brain.execution.workflow.workflow_provider import WorkflowProvider
from brain.execution.workflow.workflow_runtime import WorkflowRuntime

logger = logging.getLogger(__name__)

_global_workflow_lock = threading.RLock()
_global_workflow_runtime: Optional[WorkflowRuntime] = None


def get_workflow_runtime(
    provider: Optional[WorkflowProvider] = None,
    reset: bool = False,
) -> WorkflowRuntime:
    """Singleton accessor for the global WorkflowRuntime instance.

    Thread-safe. Automatically initializes on creation.

    Args:
        provider: Optional WorkflowProvider instance.
        reset: If True, resets and creates a new runtime instance.

    Returns:
        WorkflowRuntime singleton instance.
    """
    global _global_workflow_runtime
    with _global_workflow_lock:
        if reset or _global_workflow_runtime is None:
            if _global_workflow_runtime is not None:
                try:
                    _global_workflow_runtime.shutdown()
                except Exception:
                    pass
            _global_workflow_runtime = WorkflowRuntime(provider=provider)
            _global_workflow_runtime.initialize()
        return _global_workflow_runtime


def reset_workflow_runtime() -> None:
    """Resets the global WorkflowRuntime instance.

    Thread-safe. Gracefully shuts down active runtime and clears singleton instance.
    """
    global _global_workflow_runtime
    with _global_workflow_lock:
        if _global_workflow_runtime is not None:
            try:
                _global_workflow_runtime.shutdown()
                _global_workflow_runtime.clear()
            except Exception:
                pass
            _global_workflow_runtime = None
        logger.debug("Global WorkflowRuntime reset")
