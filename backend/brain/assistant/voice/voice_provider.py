"""Voice Provider implementation for Auralis (Phase 13.7).

Aggregates VoiceCoordinator, SpeechRouter, WakeWordManager, and VoiceSessionManager into a unified provider.
Exposes health diagnostics, performance statistics, capabilities, and diagnostics using constructor dependency injection only.
No mutable global singletons. Thread-safe using threading.RLock().
"""

from datetime import datetime, timezone
import logging
import threading
import time
from typing import List, Optional

from brain.assistant.voice.interfaces import (
    ISpeechRouter,
    IVoiceCoordinator,
    IVoiceProvider,
    IVoiceSessionManager,
    IWakeWordManager,
)
from brain.assistant.voice.models import (
    VoiceCapabilities,
    VoiceHealth,
    VoiceStatistics,
)
from brain.assistant.voice.session_manager import VoiceSessionManager
from brain.assistant.voice.speech_router import SpeechRouter
from brain.assistant.voice.voice_coordinator import VoiceCoordinator
from brain.assistant.voice.wake_word_manager import WakeWordManager

logger = logging.getLogger(__name__)


class VoiceProvider(IVoiceProvider):
    """Aggregating provider for top-level voice orchestration, session control, wake word management, and speech routing."""

    def __init__(
        self,
        coordinator: Optional[IVoiceCoordinator] = None,
        speech_router: Optional[ISpeechRouter] = None,
        wake_word_manager: Optional[IWakeWordManager] = None,
        session_manager: Optional[IVoiceSessionManager] = None,
    ) -> None:
        """Initializes VoiceProvider using constructor dependency injection only."""
        self._lock = threading.RLock()
        self._speech_router = speech_router or SpeechRouter(lock=self._lock)
        self._wake_word_manager = wake_word_manager or WakeWordManager(lock=self._lock)
        self._session_manager = session_manager or VoiceSessionManager(lock=self._lock)
        self._coordinator = coordinator or VoiceCoordinator(speech_router=self._speech_router, lock=self._lock)

        self._initialized = False
        self._start_time: Optional[float] = None

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def coordinator(self) -> IVoiceCoordinator:
        with self._lock:
            return self._coordinator

    @property
    def speech_router(self) -> ISpeechRouter:
        with self._lock:
            return self._speech_router

    @property
    def wake_word_manager(self) -> IWakeWordManager:
        with self._lock:
            return self._wake_word_manager

    @property
    def session_manager(self) -> IVoiceSessionManager:
        with self._lock:
            return self._session_manager

    @property
    def is_initialized(self) -> bool:
        with self._lock:
            return self._initialized

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def initialize(self) -> None:
        """Initialize provider resources."""
        with self._lock:
            if self._initialized:
                return

            self._initialized = True
            self._start_time = time.time()
            logger.info("VoiceProvider initialized successfully")

    def shutdown(self) -> None:
        """Gracefully shut down provider resources."""
        with self._lock:
            if not self._initialized:
                return

            self._initialized = False
            self._start_time = None
            logger.info("VoiceProvider shutdown complete")

    def clear(self) -> None:
        """Reset sub-managers and performance metrics."""
        with self._lock:
            if hasattr(self._session_manager, "clear"):
                self._session_manager.clear()  # type: ignore[union-attr]
            if hasattr(self._wake_word_manager, "clear"):
                self._wake_word_manager.clear()  # type: ignore[union-attr]
            if hasattr(self._speech_router, "clear"):
                self._speech_router.clear()  # type: ignore[union-attr]
            if hasattr(self._coordinator, "clear"):
                self._coordinator.clear()  # type: ignore[union-attr]

    # ------------------------------------------------------------------
    # Diagnostics & Status
    # ------------------------------------------------------------------

    def get_capabilities(self) -> VoiceCapabilities:
        """Expose voice orchestration capabilities specification."""
        return VoiceCapabilities()

    def get_health(self) -> VoiceHealth:
        """Expose real-time diagnostic health report."""
        with self._lock:
            subsystems = {
                "coordinator": self._coordinator is not None,
                "speech_router": self._speech_router is not None,
                "wake_word_manager": self._wake_word_manager is not None,
                "session_manager": self._session_manager is not None,
            }
            issues: List[str] = []
            if not self._initialized:
                issues.append("VoiceProvider is not initialized")

            healthy = self._initialized and len(issues) == 0

            return VoiceHealth(
                status="READY" if healthy else ("UNINITIALIZED" if not self._initialized else "DEGRADED"),
                healthy=healthy,
                subsystems=subsystems,
                statistics=self.get_statistics().model_dump(),
                detected_issues=issues,
                checked_at=datetime.now(timezone.utc),
                metadata={},
            )

    def get_statistics(self) -> VoiceStatistics:
        """Expose aggregated voice statistics metrics."""
        with self._lock:
            total_created = getattr(self._session_manager, "total_sessions_created", 0)
            active_cnt = len(self._session_manager.list_active_sessions())
            total_interactions = getattr(self._coordinator, "interaction_count", 0)
            stt_cnt = getattr(self._speech_router, "stt_routed_count", 0)
            tts_cnt = getattr(self._speech_router, "tts_routed_count", 0)
            ww_triggers = getattr(self._wake_word_manager, "trigger_count", 0)

            uptime = 0.0
            if self._start_time is not None and self._initialized:
                uptime = max(0.0, time.time() - self._start_time)

            return VoiceStatistics(
                total_sessions_created=total_created,
                active_sessions=active_cnt,
                total_interactions=total_interactions,
                speech_to_text_routed=stt_cnt,
                text_to_speech_routed=tts_cnt,
                wake_word_triggers=ww_triggers,
                average_pipeline_latency_ms=0.0,
                uptime_seconds=uptime,
                metadata={},
            )
