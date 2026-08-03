"""Assistant Integration Runtime Singleton Accessors and Global Lifecycle Manager (Phase 13.9).

Provides thread-safe global accessors (get_assistant_integration_runtime, reset_assistant_integration_runtime)
for the AssistantIntegrationRuntime singleton.
"""

import logging
import threading
from typing import Optional

from brain.assistant.integration.assistant_integration_runtime import AssistantIntegrationRuntime
from brain.assistant.integration.interfaces import IAssistantIntegrationProvider

logger = logging.getLogger(__name__)

_global_integration_lock = threading.RLock()
_global_integration_runtime: Optional[AssistantIntegrationRuntime] = None


def get_assistant_integration_runtime(
    provider: Optional[IAssistantIntegrationProvider] = None,
    reset: bool = False,
) -> AssistantIntegrationRuntime:
    """Singleton accessor for the global AssistantIntegrationRuntime instance.

    Thread-safe. Automatically initializes on access.

    Args:
        provider: Optional IAssistantIntegrationProvider instance.
        reset: If True, shuts down existing instance and creates a new runtime.

    Returns:
        AssistantIntegrationRuntime singleton instance.
    """
    global _global_integration_runtime
    with _global_integration_lock:
        if reset or _global_integration_runtime is None:
            if _global_integration_runtime is not None:
                try:
                    _global_integration_runtime.shutdown()
                except Exception as exc:
                    logger.warning("Error shutting down prior AssistantIntegrationRuntime: %s", exc)
            _global_integration_runtime = AssistantIntegrationRuntime(provider=provider)
            _global_integration_runtime.initialize()
        return _global_integration_runtime


def reset_assistant_integration_runtime() -> None:
    """Resets the global AssistantIntegrationRuntime instance.

    Thread-safe. Gracefully shuts down active runtime and clears singleton reference.
    """
    global _global_integration_runtime
    with _global_integration_lock:
        if _global_integration_runtime is not None:
            try:
                _global_integration_runtime.shutdown()
                _global_integration_runtime.clear()
            except Exception as exc:
                logger.warning("Error during AssistantIntegrationRuntime reset: %s", exc)
            _global_integration_runtime = None
        logger.debug("Global AssistantIntegrationRuntime reset complete")
