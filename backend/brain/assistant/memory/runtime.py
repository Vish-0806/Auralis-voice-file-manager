"""Assistant Memory Runtime Singleton Accessors and Global Lifecycle Manager (Phase 13.5).

Provides thread-safe global accessors (get_assistant_memory_runtime, reset_assistant_memory_runtime)
for the AssistantMemoryRuntime singleton.
"""

import logging
import threading
from typing import Optional

from brain.assistant.memory.assistant_memory_runtime import AssistantMemoryRuntime
from brain.assistant.memory.interfaces import IAssistantMemoryProvider

logger = logging.getLogger(__name__)

_global_assistant_memory_lock = threading.RLock()
_global_assistant_memory_runtime: Optional[AssistantMemoryRuntime] = None


def get_assistant_memory_runtime(
    provider: Optional[IAssistantMemoryProvider] = None,
    reset: bool = False,
) -> AssistantMemoryRuntime:
    """Singleton accessor for the global AssistantMemoryRuntime instance.

    Thread-safe. Automatically initializes on access.

    Args:
        provider: Optional IAssistantMemoryProvider instance.
        reset: If True, shuts down existing instance and creates a new runtime.

    Returns:
        AssistantMemoryRuntime singleton instance.
    """
    global _global_assistant_memory_runtime
    with _global_assistant_memory_lock:
        if reset or _global_assistant_memory_runtime is None:
            if _global_assistant_memory_runtime is not None:
                try:
                    _global_assistant_memory_runtime.shutdown()
                except Exception as exc:
                    logger.warning("Error shutting down prior AssistantMemoryRuntime: %s", exc)
            _global_assistant_memory_runtime = AssistantMemoryRuntime(provider=provider)
            _global_assistant_memory_runtime.initialize()
        return _global_assistant_memory_runtime


def reset_assistant_memory_runtime() -> None:
    """Resets the global AssistantMemoryRuntime instance.

    Thread-safe. Gracefully shuts down active runtime and clears singleton reference.
    """
    global _global_assistant_memory_runtime
    with _global_assistant_memory_lock:
        if _global_assistant_memory_runtime is not None:
            try:
                _global_assistant_memory_runtime.shutdown()
                _global_assistant_memory_runtime.clear()
            except Exception as exc:
                logger.warning("Error during AssistantMemoryRuntime reset: %s", exc)
            _global_assistant_memory_runtime = None
        logger.debug("Global AssistantMemoryRuntime reset complete")
