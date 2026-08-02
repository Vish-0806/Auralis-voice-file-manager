"""Global Singleton Accessors for the Automation & Scheduling Runtime (Phase 12.6).

Provides thread-safe accessors (get_automation_runtime, reset_automation_runtime) for the global AutomationRuntime instance.
"""

import logging
import threading
from typing import Optional

from brain.execution.automation.automation_provider import AutomationProvider
from brain.execution.automation.automation_runtime import AutomationRuntime

logger = logging.getLogger(__name__)

_global_automation_lock = threading.RLock()
_global_automation_runtime: Optional[AutomationRuntime] = None


def get_automation_runtime(
    provider: Optional[AutomationProvider] = None,
    reset: bool = False,
) -> AutomationRuntime:
    """Singleton accessor for the global AutomationRuntime instance.

    Thread-safe. Automatically initializes on creation.

    Args:
        provider: Optional AutomationProvider instance.
        reset: If True, resets and creates a new runtime instance.

    Returns:
        AutomationRuntime singleton instance.
    """
    global _global_automation_runtime
    with _global_automation_lock:
        if reset or _global_automation_runtime is None:
            if _global_automation_runtime is not None:
                try:
                    _global_automation_runtime.shutdown()
                except Exception:
                    pass
            _global_automation_runtime = AutomationRuntime(provider=provider)
            _global_automation_runtime.initialize()
        return _global_automation_runtime


def reset_automation_runtime() -> None:
    """Resets the global AutomationRuntime instance.

    Thread-safe. Gracefully shuts down active runtime and clears singleton instance.
    """
    global _global_automation_runtime
    with _global_automation_lock:
        if _global_automation_runtime is not None:
            try:
                _global_automation_runtime.shutdown()
                _global_automation_runtime.clear()
            except Exception:
                pass
            _global_automation_runtime = None
        logger.debug("Global AutomationRuntime reset")
