"""Voice Runtime Singleton Accessors and Global Lifecycle Manager (Phase 13.7).

Provides thread-safe global accessors (get_voice_runtime, reset_voice_runtime)
for the VoiceRuntime singleton.
"""

import logging
import threading
from typing import Optional

from brain.assistant.voice.interfaces import IVoiceProvider
from brain.assistant.voice.voice_runtime import VoiceRuntime

logger = logging.getLogger(__name__)

_global_voice_lock = threading.RLock()
_global_voice_runtime: Optional[VoiceRuntime] = None


def get_voice_runtime(
    provider: Optional[IVoiceProvider] = None,
    reset: bool = False,
) -> VoiceRuntime:
    """Singleton accessor for the global VoiceRuntime instance.

    Thread-safe. Automatically initializes on access.

    Args:
        provider: Optional IVoiceProvider instance.
        reset: If True, shuts down existing instance and creates a new runtime.

    Returns:
        VoiceRuntime singleton instance.
    """
    global _global_voice_runtime
    with _global_voice_lock:
        if reset or _global_voice_runtime is None:
            if _global_voice_runtime is not None:
                try:
                    _global_voice_runtime.shutdown()
                except Exception as exc:
                    logger.warning("Error shutting down prior VoiceRuntime: %s", exc)
            _global_voice_runtime = VoiceRuntime(provider=provider)
            _global_voice_runtime.initialize()
        return _global_voice_runtime


def reset_voice_runtime() -> None:
    """Resets the global VoiceRuntime instance.

    Thread-safe. Gracefully shuts down active runtime and clears singleton reference.
    """
    global _global_voice_runtime
    with _global_voice_lock:
        if _global_voice_runtime is not None:
            try:
                _global_voice_runtime.shutdown()
                _global_voice_runtime.clear()
            except Exception as exc:
                logger.warning("Error during VoiceRuntime reset: %s", exc)
            _global_voice_runtime = None
        logger.debug("Global VoiceRuntime reset complete")
