"""Response Runtime Singleton Accessors and Global Lifecycle Manager (Phase 13.6).

Provides thread-safe global accessors (get_response_runtime, reset_response_runtime)
for the ResponseRuntime singleton.
"""

import logging
import threading
from typing import Optional

from brain.assistant.response.interfaces import IResponseProvider
from brain.assistant.response.response_runtime import ResponseRuntime

logger = logging.getLogger(__name__)

_global_response_lock = threading.RLock()
_global_response_runtime: Optional[ResponseRuntime] = None


def get_response_runtime(
    provider: Optional[IResponseProvider] = None,
    reset: bool = False,
) -> ResponseRuntime:
    """Singleton accessor for the global ResponseRuntime instance.

    Thread-safe. Automatically initializes on access.

    Args:
        provider: Optional IResponseProvider instance.
        reset: If True, shuts down existing instance and creates a new runtime.

    Returns:
        ResponseRuntime singleton instance.
    """
    global _global_response_runtime
    with _global_response_lock:
        if reset or _global_response_runtime is None:
            if _global_response_runtime is not None:
                try:
                    _global_response_runtime.shutdown()
                except Exception as exc:
                    logger.warning("Error shutting down prior ResponseRuntime: %s", exc)
            _global_response_runtime = ResponseRuntime(provider=provider)
            _global_response_runtime.initialize()
        return _global_response_runtime


def reset_response_runtime() -> None:
    """Resets the global ResponseRuntime instance.

    Thread-safe. Gracefully shuts down active runtime and clears singleton reference.
    """
    global _global_response_runtime
    with _global_response_lock:
        if _global_response_runtime is not None:
            try:
                _global_response_runtime.shutdown()
                _global_response_runtime.clear()
            except Exception as exc:
                logger.warning("Error during ResponseRuntime reset: %s", exc)
            _global_response_runtime = None
        logger.debug("Global ResponseRuntime reset complete")
