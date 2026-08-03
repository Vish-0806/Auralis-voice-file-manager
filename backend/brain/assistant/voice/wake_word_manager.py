"""Wake Word Manager implementation for Auralis (Phase 13.7).

Manages wake word orchestration state (enabled, disabled, paused, resumed), configuration,
health diagnostics, and statistics without executing detection algorithms.
Thread-safe using threading.RLock().
"""

import logging
import threading
from typing import Optional

from brain.assistant.voice.interfaces import IWakeWordManager
from brain.assistant.voice.models import VoiceConfiguration

logger = logging.getLogger(__name__)


class WakeWordManager(IWakeWordManager):
    """Thread-safe wake word state manager orchestrating activation control."""

    def __init__(
        self,
        config: Optional[VoiceConfiguration] = None,
        lock: Optional[threading.RLock] = None,
    ) -> None:
        self._lock = lock or threading.RLock()
        self._config = config or VoiceConfiguration()

        self._enabled = self._config.wake_word_enabled
        self._paused = False
        self._trigger_count = 0

    @property
    def is_enabled(self) -> bool:
        with self._lock:
            return self._enabled and not self._paused

    @property
    def trigger_count(self) -> int:
        with self._lock:
            return self._trigger_count

    def enable(self) -> bool:
        """Enable wake word orchestration."""
        with self._lock:
            self._enabled = True
            self._paused = False
            logger.info("WakeWordManager enabled (phrase='%s')", self._config.wake_word_phrase)
            return True

    def disable(self) -> bool:
        """Disable wake word orchestration."""
        with self._lock:
            self._enabled = False
            self._paused = False
            logger.info("WakeWordManager disabled")
            return False

    def pause(self) -> bool:
        """Pause wake word orchestration."""
        with self._lock:
            if self._enabled:
                self._paused = True
                logger.info("WakeWordManager paused")
            return self.is_enabled

    def resume(self) -> bool:
        """Resume wake word orchestration."""
        with self._lock:
            if self._enabled:
                self._paused = False
                logger.info("WakeWordManager resumed")
            return self.is_enabled

    def record_trigger(self) -> None:
        """Record a wake word trigger event metric."""
        with self._lock:
            self._trigger_count += 1
            logger.debug("Wake word trigger recorded (total=%d)", self._trigger_count)

    def clear(self) -> None:
        """Reset wake word statistics."""
        with self._lock:
            self._trigger_count = 0
            self._enabled = self._config.wake_word_enabled
            self._paused = False
