"""Dialogue Runtime Singleton Accessors and Global Lifecycle Manager (Phase 13.3).

Provides thread-safe global accessors (get_dialogue_runtime, reset_dialogue_runtime)
for the DialogueRuntime singleton.
"""

import logging
import threading
from typing import Optional

from brain.assistant.dialogue.dialogue_runtime import DialogueRuntime
from brain.assistant.dialogue.interfaces import IDialogueProvider

logger = logging.getLogger(__name__)

_global_dialogue_lock = threading.RLock()
_global_dialogue_runtime: Optional[DialogueRuntime] = None


def get_dialogue_runtime(
    provider: Optional[IDialogueProvider] = None,
    reset: bool = False,
) -> DialogueRuntime:
    """Singleton accessor for the global DialogueRuntime instance.

    Thread-safe. Automatically initializes on access.

    Args:
        provider: Optional IDialogueProvider instance.
        reset: If True, shuts down existing instance and creates a new runtime.

    Returns:
        DialogueRuntime singleton instance.
    """
    global _global_dialogue_runtime
    with _global_dialogue_lock:
        if reset or _global_dialogue_runtime is None:
            if _global_dialogue_runtime is not None:
                try:
                    _global_dialogue_runtime.shutdown()
                except Exception as exc:
                    logger.warning("Error shutting down prior DialogueRuntime: %s", exc)
            _global_dialogue_runtime = DialogueRuntime(provider=provider)
            _global_dialogue_runtime.initialize()
        return _global_dialogue_runtime


def reset_dialogue_runtime() -> None:
    """Resets the global DialogueRuntime instance.

    Thread-safe. Gracefully shuts down active runtime and clears singleton reference.
    """
    global _global_dialogue_runtime
    with _global_dialogue_lock:
        if _global_dialogue_runtime is not None:
            try:
                _global_dialogue_runtime.shutdown()
                _global_dialogue_runtime.clear()
            except Exception as exc:
                logger.warning("Error during DialogueRuntime reset: %s", exc)
            _global_dialogue_runtime = None
        logger.debug("Global DialogueRuntime reset complete")
