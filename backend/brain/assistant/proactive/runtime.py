"""Proactive Runtime Singleton Accessors and Global Lifecycle Manager (Phase 13.8).

Provides thread-safe global accessors (get_proactive_runtime, reset_proactive_runtime)
for the ProactiveRuntime singleton.
"""

import logging
import threading
from typing import Optional

from brain.assistant.proactive.interfaces import IProactiveProvider
from brain.assistant.proactive.proactive_runtime import ProactiveRuntime

logger = logging.getLogger(__name__)

_global_proactive_lock = threading.RLock()
_global_proactive_runtime: Optional[ProactiveRuntime] = None


def get_proactive_runtime(
    provider: Optional[IProactiveProvider] = None,
    reset: bool = False,
) -> ProactiveRuntime:
    """Singleton accessor for the global ProactiveRuntime instance.

    Thread-safe. Automatically initializes on access.

    Args:
        provider: Optional IProactiveProvider instance.
        reset: If True, shuts down existing instance and creates a new runtime.

    Returns:
        ProactiveRuntime singleton instance.
    """
    global _global_proactive_runtime
    with _global_proactive_lock:
        if reset or _global_proactive_runtime is None:
            if _global_proactive_runtime is not None:
                try:
                    _global_proactive_runtime.shutdown()
                except Exception as exc:
                    logger.warning("Error shutting down prior ProactiveRuntime: %s", exc)
            _global_proactive_runtime = ProactiveRuntime(provider=provider)
            _global_proactive_runtime.initialize()
        return _global_proactive_runtime


def reset_proactive_runtime() -> None:
    """Resets the global ProactiveRuntime instance.

    Thread-safe. Gracefully shuts down active runtime and clears singleton reference.
    """
    global _global_proactive_runtime
    with _global_proactive_lock:
        if _global_proactive_runtime is not None:
            try:
                _global_proactive_runtime.shutdown()
                _global_proactive_runtime.clear()
            except Exception as exc:
                logger.warning("Error during ProactiveRuntime reset: %s", exc)
            _global_proactive_runtime = None
        logger.debug("Global ProactiveRuntime reset complete")
