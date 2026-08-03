"""Conversation Runtime Singleton Accessors and Global Lifecycle Manager (Phase 13.2).

Provides thread-safe global accessors (get_conversation_runtime, reset_conversation_runtime)
for the ConversationRuntime singleton.
"""

import logging
import threading
from typing import Optional

from brain.assistant.conversation.conversation_runtime import ConversationRuntime
from brain.assistant.conversation.interfaces import IConversationProvider

logger = logging.getLogger(__name__)

_global_conversation_lock = threading.RLock()
_global_conversation_runtime: Optional[ConversationRuntime] = None


def get_conversation_runtime(
    provider: Optional[IConversationProvider] = None,
    reset: bool = False,
) -> ConversationRuntime:
    """Singleton accessor for the global ConversationRuntime instance.

    Thread-safe. Automatically initializes on access.

    Args:
        provider: Optional IConversationProvider instance.
        reset: If True, shuts down existing instance and creates a new runtime.

    Returns:
        ConversationRuntime singleton instance.
    """
    global _global_conversation_runtime
    with _global_conversation_lock:
        if reset or _global_conversation_runtime is None:
            if _global_conversation_runtime is not None:
                try:
                    _global_conversation_runtime.shutdown()
                except Exception as exc:
                    logger.warning("Error shutting down prior ConversationRuntime: %s", exc)
            _global_conversation_runtime = ConversationRuntime(provider=provider)
            _global_conversation_runtime.initialize()
        return _global_conversation_runtime


def reset_conversation_runtime() -> None:
    """Resets the global ConversationRuntime instance.

    Thread-safe. Gracefully shuts down active runtime and clears singleton reference.
    """
    global _global_conversation_runtime
    with _global_conversation_lock:
        if _global_conversation_runtime is not None:
            try:
                _global_conversation_runtime.shutdown()
                _global_conversation_runtime.clear()
            except Exception as exc:
                logger.warning("Error during ConversationRuntime reset: %s", exc)
            _global_conversation_runtime = None
        logger.debug("Global ConversationRuntime reset complete")
