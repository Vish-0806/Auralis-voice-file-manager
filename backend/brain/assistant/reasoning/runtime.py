"""Decision Runtime Singleton Accessors and Global Lifecycle Manager (Phase 13.4).

Provides thread-safe global accessors (get_decision_runtime, reset_decision_runtime)
for the DecisionRuntime singleton.
"""

import logging
import threading
from typing import Optional

from brain.assistant.reasoning.decision_runtime import DecisionRuntime
from brain.assistant.reasoning.interfaces import IDecisionProvider

logger = logging.getLogger(__name__)

_global_decision_lock = threading.RLock()
_global_decision_runtime: Optional[DecisionRuntime] = None


def get_decision_runtime(
    provider: Optional[IDecisionProvider] = None,
    reset: bool = False,
) -> DecisionRuntime:
    """Singleton accessor for the global DecisionRuntime instance.

    Thread-safe. Automatically initializes on access.

    Args:
        provider: Optional IDecisionProvider instance.
        reset: If True, shuts down existing instance and creates a new runtime.

    Returns:
        DecisionRuntime singleton instance.
    """
    global _global_decision_runtime
    with _global_decision_lock:
        if reset or _global_decision_runtime is None:
            if _global_decision_runtime is not None:
                try:
                    _global_decision_runtime.shutdown()
                except Exception as exc:
                    logger.warning("Error shutting down prior DecisionRuntime: %s", exc)
            _global_decision_runtime = DecisionRuntime(provider=provider)
            _global_decision_runtime.initialize()
        return _global_decision_runtime


def reset_decision_runtime() -> None:
    """Resets the global DecisionRuntime instance.

    Thread-safe. Gracefully shuts down active runtime and clears singleton reference.
    """
    global _global_decision_runtime
    with _global_decision_lock:
        if _global_decision_runtime is not None:
            try:
                _global_decision_runtime.shutdown()
                _global_decision_runtime.clear()
            except Exception as exc:
                logger.warning("Error during DecisionRuntime reset: %s", exc)
            _global_decision_runtime = None
        logger.debug("Global DecisionRuntime reset complete")
