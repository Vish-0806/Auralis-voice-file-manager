"""Execution Runtime Coordinator and Global Accessors for Auralis (Phase 12.1).

Provides singleton lifecycle management, global accessors (get_execution_runtime, reset_execution_runtime),
health monitoring, and backward compatibility for legacy ExecutionRuntimeCoordinator.
"""

import logging
import threading
from typing import Any, Dict, List, Optional

from brain.execution.execution_coordinator import ExecutionCoordinator
from brain.execution.execution_models import (
    ExecutionHealth,
    ExecutionResult,
    ExecutionStatistics,
    ExecutionStatus,
)
from brain.execution.execution_policy import ExecutionPolicy
from brain.execution.execution_provider import ExecutionProvider
from brain.execution.execution_runtime import (
    ExecutionRuntime,
    ExecutionRuntimeStatus,
)
from brain.execution.execution_session import ExecutionSession
from brain.execution.execution_step_runner import ExecutionStepRunner
from brain.planning.execution_plan_builder import ExecutionPlan

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Global Singleton Accessors (Phase 12.1 Canonical)
# ---------------------------------------------------------------------------

_global_execution_lock = threading.RLock()
_global_execution_runtime: Optional[ExecutionRuntime] = None


def get_execution_runtime(
    provider: Optional[ExecutionProvider] = None,
    coordinator: Optional[ExecutionCoordinator] = None,
    step_runner: Optional[ExecutionStepRunner] = None,
    default_policy: Optional[ExecutionPolicy] = None,
    reset: bool = False,
) -> ExecutionRuntime:
    """Singleton accessor for the global ExecutionRuntime instance.

    Thread-safe. Automatically initializes on creation.

    Args:
        provider: Optional ExecutionProvider instance.
        coordinator: Optional ExecutionCoordinator instance (legacy).
        step_runner: Optional ExecutionStepRunner instance (legacy).
        default_policy: Optional ExecutionPolicy instance (legacy).
        reset: If True, resets and creates a new runtime instance.

    Returns:
        ExecutionRuntime singleton instance.
    """
    global _global_execution_runtime
    with _global_execution_lock:
        if reset or _global_execution_runtime is None:
            if _global_execution_runtime is not None:
                try:
                    _global_execution_runtime.shutdown()
                except Exception:
                    pass
            _global_execution_runtime = ExecutionRuntime(
                provider=provider,
                coordinator=coordinator,
                step_runner=step_runner,
                default_policy=default_policy,
            )
            _global_execution_runtime.initialize()
        return _global_execution_runtime


def reset_execution_runtime() -> None:
    """Resets the global ExecutionRuntime instance.

    Thread-safe. Gracefully shuts down active runtime and clears singleton instance.
    """
    global _global_execution_runtime
    with _global_execution_lock:
        if _global_execution_runtime is not None:
            try:
                _global_execution_runtime.shutdown()
                _global_execution_runtime.clear()
            except Exception:
                pass
            _global_execution_runtime = None
        logger.debug("Global ExecutionRuntime reset")


# ---------------------------------------------------------------------------
# Legacy Aliases (Backward Compatibility)
# ---------------------------------------------------------------------------

ExecutionRuntimeStatistics = ExecutionStatistics
ExecutionRuntimeHealth = ExecutionHealth
ExecutionRuntimeCoordinator = ExecutionRuntime
