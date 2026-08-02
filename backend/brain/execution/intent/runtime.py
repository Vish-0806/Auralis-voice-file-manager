"""Global Singleton Accessors for the Intent Resolution Subsystem (Phase 12.2).

Provides thread-safe accessors (get_intent_runtime, reset_intent_runtime) for the global IntentRuntime instance.
"""

import logging
import threading
from typing import Optional

from brain.execution.intent.intent_provider import IntentProvider
from brain.execution.intent.intent_runtime import IntentRuntime

logger = logging.getLogger(__name__)

_global_intent_lock = threading.RLock()
_global_intent_runtime: Optional[IntentRuntime] = None


def get_intent_runtime(
    provider: Optional[IntentProvider] = None,
    reset: bool = False,
) -> IntentRuntime:
    """Singleton accessor for the global IntentRuntime instance.

    Thread-safe. Automatically initializes on creation.

    Args:
        provider: Optional IntentProvider instance.
        reset: If True, resets and creates a new runtime instance.

    Returns:
        IntentRuntime singleton instance.
    """
    global _global_intent_runtime
    with _global_intent_lock:
        if reset or _global_intent_runtime is None:
            if _global_intent_runtime is not None:
                try:
                    _global_intent_runtime.shutdown()
                except Exception:
                    pass
            _global_intent_runtime = IntentRuntime(provider=provider)
            _global_intent_runtime.initialize()
        return _global_intent_runtime


def reset_intent_runtime() -> None:
    """Resets the global IntentRuntime instance.

    Thread-safe. Gracefully shuts down active runtime and clears singleton instance.
    """
    global _global_intent_runtime
    with _global_intent_lock:
        if _global_intent_runtime is not None:
            try:
                _global_intent_runtime.shutdown()
                _global_intent_runtime.clear()
            except Exception:
                pass
            _global_intent_runtime = None
        logger.debug("Global IntentRuntime reset")
