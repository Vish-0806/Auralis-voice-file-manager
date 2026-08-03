"""Assistant Runtime Singleton Accessors and Lifecycle Manager (Phase 13.1).

Provides thread-safe global accessors (get_assistant_runtime, reset_assistant_runtime)
for the top-level AssistantRuntime singleton.
"""

import logging
import threading
from typing import Optional

from brain.assistant.assistant_runtime import AssistantRuntime
from brain.assistant.interfaces import IAssistantProvider
from brain.assistant.models import AssistantConfiguration

logger = logging.getLogger(__name__)

_global_assistant_lock = threading.RLock()
_global_assistant_runtime: Optional[AssistantRuntime] = None


def get_assistant_runtime(
    provider: Optional[IAssistantProvider] = None,
    configuration: Optional[AssistantConfiguration] = None,
    reset: bool = False,
) -> AssistantRuntime:
    """Singleton accessor for the global AssistantRuntime instance.

    Thread-safe. Automatically initializes on access.

    Args:
        provider: Optional IAssistantProvider instance.
        configuration: Optional AssistantConfiguration settings.
        reset: If True, shuts down existing instance and creates a new runtime.

    Returns:
        AssistantRuntime singleton instance.
    """
    global _global_assistant_runtime
    with _global_assistant_lock:
        if reset or _global_assistant_runtime is None:
            if _global_assistant_runtime is not None:
                try:
                    _global_assistant_runtime.shutdown()
                except Exception as exc:
                    logger.warning("Error shutting down prior AssistantRuntime: %s", exc)
            _global_assistant_runtime = AssistantRuntime(
                provider=provider,
                configuration=configuration,
            )
            _global_assistant_runtime.initialize()
        return _global_assistant_runtime


def reset_assistant_runtime() -> None:
    """Resets the global AssistantRuntime instance.

    Thread-safe. Gracefully shuts down the active runtime and clears the singleton reference.
    """
    global _global_assistant_runtime
    with _global_assistant_lock:
        if _global_assistant_runtime is not None:
            try:
                _global_assistant_runtime.shutdown()
                _global_assistant_runtime.clear()
            except Exception as exc:
                logger.warning("Error during AssistantRuntime reset: %s", exc)
            _global_assistant_runtime = None
        logger.debug("Global AssistantRuntime reset complete")
