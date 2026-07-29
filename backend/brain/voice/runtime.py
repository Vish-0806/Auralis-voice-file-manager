"""Voice Runtime Coordinator for the Auralis Voice Orchestration Engine (Phase 9.6).

Provides singleton lifecycle management, health monitoring, and statistics
aggregation for the Voice Orchestration Engine.
"""

import logging
import threading
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

from brain.voice.clarification_manager import ClarificationManager
from brain.voice.command_dispatcher import CommandDispatcher
from brain.voice.confirmation_manager import ConfirmationManager
from brain.voice.feedback_generator import FeedbackGenerator
from brain.voice.voice_models import (
    VoiceRuntimeHealth,
    VoiceRuntimeStatistics,
)
from brain.voice.voice_orchestrator import VoiceOrchestrator
from brain.voice.voice_session import VoiceSession

logger = logging.getLogger(__name__)


class VoiceRuntimeStatus(str, Enum):
    """Lifecycle states for the Voice Runtime Coordinator."""

    INITIALIZING = "INITIALIZING"
    READY = "READY"
    LISTENING = "LISTENING"
    PROCESSING = "PROCESSING"
    WAITING_CONFIRMATION = "WAITING_CONFIRMATION"
    WAITING_CLARIFICATION = "WAITING_CLARIFICATION"
    DEGRADED = "DEGRADED"
    ERROR = "ERROR"
    SHUTDOWN = "SHUTDOWN"


class _MutableStats:
    """Mutable internal statistics accumulator."""

    def __init__(self) -> None:
        self.commands_received: int = 0
        self.commands_completed: int = 0
        self.commands_failed: int = 0
        self.commands_cancelled: int = 0
        self.confirmations_requested: int = 0
        self.confirmations_accepted: int = 0
        self.confirmations_rejected: int = 0
        self.confirmations_timed_out: int = 0
        self.clarifications_requested: int = 0
        self.clarifications_received: int = 0
        self.clarifications_timed_out: int = 0
        self.sessions_started: int = 0
        self.sessions_ended: int = 0
        self._total_pipeline_ms: float = 0.0
        self._pipeline_count: int = 0
        self.peak_concurrent_sessions: int = 0
        self._current_sessions: int = 0

    def snapshot(self) -> VoiceRuntimeStatistics:
        avg = self._total_pipeline_ms / self._pipeline_count if self._pipeline_count > 0 else 0.0
        return VoiceRuntimeStatistics(
            commands_received=self.commands_received,
            commands_completed=self.commands_completed,
            commands_failed=self.commands_failed,
            commands_cancelled=self.commands_cancelled,
            confirmations_requested=self.confirmations_requested,
            confirmations_accepted=self.confirmations_accepted,
            confirmations_rejected=self.confirmations_rejected,
            confirmations_timed_out=self.confirmations_timed_out,
            clarifications_requested=self.clarifications_requested,
            clarifications_received=self.clarifications_received,
            clarifications_timed_out=self.clarifications_timed_out,
            sessions_started=self.sessions_started,
            sessions_ended=self.sessions_ended,
            average_pipeline_ms=round(avg, 3),
            peak_concurrent_sessions=self.peak_concurrent_sessions,
        )


_COMPONENTS = [
    "ConfirmationManager",
    "ClarificationManager",
    "FeedbackGenerator",
    "CommandDispatcher",
    "VoiceOrchestrator",
]


class VoiceRuntimeCoordinator:
    """Thread-safe singleton coordinator for the Voice Orchestration Engine.

    Manages lifecycle of all voice components and exposes health/statistics.
    """

    def __init__(
        self,
        orchestrator: Optional[VoiceOrchestrator] = None,
    ) -> None:
        """Initialises VoiceRuntimeCoordinator.

        Args:
            orchestrator: Optional pre-built orchestrator.  Created during
                          ``initialize()`` if not provided.
        """
        self._lock = threading.RLock()
        self._status: VoiceRuntimeStatus = VoiceRuntimeStatus.INITIALIZING
        self._orchestrator: Optional[VoiceOrchestrator] = orchestrator
        self._stats = _MutableStats()
        self._started_at: Optional[datetime] = None
        self._runtime_id: str = f"voice-rt-{uuid.uuid4().hex[:6]}"

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def initialize(self) -> bool:
        """Initialize all voice components and transition to READY.

        Returns:
            True if initialization succeeded, False on error.
        """
        with self._lock:
            try:
                self._status = VoiceRuntimeStatus.INITIALIZING
                if self._orchestrator is None:
                    self._orchestrator = VoiceOrchestrator(
                        confirmation_manager=ConfirmationManager(),
                        clarification_manager=ClarificationManager(),
                        feedback_generator=FeedbackGenerator(),
                        dispatcher=CommandDispatcher(),
                    )
                self._started_at = datetime.now(timezone.utc)
                self._status = VoiceRuntimeStatus.READY
                logger.info("Runtime Initialized: runtime_id=%s", self._runtime_id)
                return True
            except Exception as exc:
                self._status = VoiceRuntimeStatus.ERROR
                logger.error("VoiceRuntimeCoordinator.initialize failed: %s", exc)
                return False

    def shutdown(self) -> bool:
        """Shut down all voice components.

        Returns:
            True always (graceful shutdown).
        """
        with self._lock:
            self._status = VoiceRuntimeStatus.SHUTDOWN
            self._orchestrator = None
            logger.info("Runtime Shutdown: runtime_id=%s", self._runtime_id)
            return True

    # ------------------------------------------------------------------
    # Session Management
    # ------------------------------------------------------------------

    def start_session(
        self,
        session_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> VoiceSession:
        """Create and register a new voice session.

        Args:
            session_id: Optional explicit session ID.
            conversation_id: Optional conversation ID.

        Returns:
            New :class:`VoiceSession`.
        """
        with self._lock:
            orchestrator = self._get_orchestrator()
            session = orchestrator.create_session(session_id=session_id, conversation_id=conversation_id)
            self._stats.sessions_started += 1
            self._stats._current_sessions += 1
            if self._stats._current_sessions > self._stats.peak_concurrent_sessions:
                self._stats.peak_concurrent_sessions = self._stats._current_sessions
            logger.info("Voice Session Started: session_id=%s", session.session_id)
            return session

    def end_session(self, session_id: str) -> bool:
        """End a voice session.

        Args:
            session_id: Session to end.

        Returns:
            True if session was found and ended.
        """
        with self._lock:
            orchestrator = self._get_orchestrator()
            ended = orchestrator.end_session(session_id)
            if ended:
                self._stats.sessions_ended += 1
                self._stats._current_sessions = max(0, self._stats._current_sessions - 1)
                logger.info("Voice Session Ended: session_id=%s", session_id)
            return ended

    def list_sessions(self) -> List[str]:
        """Return all known session IDs.

        Returns:
            List of session ID strings.
        """
        with self._lock:
            if self._orchestrator is None:
                return []
            return self._orchestrator.list_sessions()

    # ------------------------------------------------------------------
    # Health & Statistics
    # ------------------------------------------------------------------

    def health_check(self) -> VoiceRuntimeHealth:
        """Return an immutable health snapshot.

        Returns:
            :class:`VoiceRuntimeHealth`.
        """
        with self._lock:
            healthy = self._status == VoiceRuntimeStatus.READY
            uptime = 0.0
            if self._started_at:
                uptime = (datetime.now(timezone.utc) - self._started_at).total_seconds()
            active = self._stats._current_sessions

            return VoiceRuntimeHealth(
                healthy=healthy,
                status=self._status.value,
                active_sessions=active,
                registered_components=_COMPONENTS,
                uptime_seconds=round(uptime, 2),
                checked_at=datetime.now(timezone.utc),
                metadata={"runtime_id": self._runtime_id},
            )

    def get_statistics(self) -> VoiceRuntimeStatistics:
        """Return an immutable statistics snapshot.

        Returns:
            :class:`VoiceRuntimeStatistics`.
        """
        with self._lock:
            return self._stats.snapshot()

    def clear(self) -> None:
        """Reset all statistics counters to zero."""
        with self._lock:
            self._stats = _MutableStats()
            logger.debug("VoiceRuntimeCoordinator statistics cleared")

    # ------------------------------------------------------------------
    # Orchestrator Access
    # ------------------------------------------------------------------

    def get_orchestrator(self) -> VoiceOrchestrator:
        """Return the active orchestrator.

        Auto-initializes if in SHUTDOWN state.

        Returns:
            Active :class:`VoiceOrchestrator`.

        Raises:
            RuntimeError: If initialization fails.
        """
        with self._lock:
            return self._get_orchestrator()

    @property
    def status(self) -> VoiceRuntimeStatus:
        """Current runtime status."""
        with self._lock:
            return self._status

    # ------------------------------------------------------------------
    # Statistics Helpers
    # ------------------------------------------------------------------

    def record_command_received(self) -> None:
        with self._lock:
            self._stats.commands_received += 1

    def record_command_completed(self, pipeline_ms: float = 0.0) -> None:
        with self._lock:
            self._stats.commands_completed += 1
            self._stats._total_pipeline_ms += pipeline_ms
            self._stats._pipeline_count += 1

    def record_command_failed(self) -> None:
        with self._lock:
            self._stats.commands_failed += 1

    def record_command_cancelled(self) -> None:
        with self._lock:
            self._stats.commands_cancelled += 1

    def record_confirmation_requested(self) -> None:
        with self._lock:
            self._stats.confirmations_requested += 1

    def record_confirmation_accepted(self) -> None:
        with self._lock:
            self._stats.confirmations_accepted += 1

    def record_confirmation_rejected(self) -> None:
        with self._lock:
            self._stats.confirmations_rejected += 1

    def record_confirmation_timed_out(self) -> None:
        with self._lock:
            self._stats.confirmations_timed_out += 1

    def record_clarification_requested(self) -> None:
        with self._lock:
            self._stats.clarifications_requested += 1

    def record_clarification_received(self) -> None:
        with self._lock:
            self._stats.clarifications_received += 1

    def record_clarification_timed_out(self) -> None:
        with self._lock:
            self._stats.clarifications_timed_out += 1

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    def _get_orchestrator(self) -> VoiceOrchestrator:
        if self._status == VoiceRuntimeStatus.SHUTDOWN or self._orchestrator is None:
            self.initialize()
        if self._orchestrator is None:
            raise RuntimeError("VoiceRuntimeCoordinator: orchestrator unavailable")
        return self._orchestrator


# ---------------------------------------------------------------------------
# Global Singleton Accessors
# ---------------------------------------------------------------------------

_global_voice_runtime: Optional[VoiceRuntimeCoordinator] = None
_global_voice_lock = threading.RLock()


def get_voice_runtime() -> VoiceRuntimeCoordinator:
    """Return (or create) the global Voice Runtime singleton.

    Thread-safe. Automatically initializes if it does not exist.

    Returns:
        :class:`VoiceRuntimeCoordinator` singleton instance.
    """
    global _global_voice_runtime
    with _global_voice_lock:
        if _global_voice_runtime is None:
            _global_voice_runtime = VoiceRuntimeCoordinator()
            _global_voice_runtime.initialize()
        return _global_voice_runtime


def reset_voice_runtime() -> None:
    """Reset the global Voice Runtime singleton.

    Thread-safe. Next call to ``get_voice_runtime()`` creates a fresh instance.
    """
    global _global_voice_runtime
    with _global_voice_lock:
        if _global_voice_runtime is not None:
            try:
                _global_voice_runtime.shutdown()
            except Exception:
                pass
            _global_voice_runtime = None
        logger.debug("Voice Runtime reset")
