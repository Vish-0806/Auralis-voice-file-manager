"""Voice Session Manager implementation for Auralis (Phase 13.7).

Manages VoiceSession lifecycles, active session registries, state transitions,
session timeouts, and metrics tracking. Thread-safe using threading.RLock().
"""

from datetime import datetime, timezone
import logging
import threading
import time
from typing import Dict, List, Optional

from brain.assistant.voice.exceptions import VoiceSessionException, VoiceValidationException
from brain.assistant.voice.interfaces import IVoiceSessionManager
from brain.assistant.voice.models import (
    ListeningMode,
    SpeechMode,
    VoiceSession,
    VoiceSessionState,
)

logger = logging.getLogger(__name__)


class VoiceSessionManager(IVoiceSessionManager):
    """Thread-safe manager for creating, transitioning, and tracking VoiceSession instances."""

    def __init__(
        self,
        session_timeout_seconds: float = 300.0,
        lock: Optional[threading.RLock] = None,
    ) -> None:
        self._lock = lock or threading.RLock()
        self._session_timeout = session_timeout_seconds
        self._sessions: Dict[str, VoiceSession] = {}

        # Statistics
        self._total_created = 0

    @property
    def total_sessions_created(self) -> int:
        with self._lock:
            return self._total_created

    def create_session(
        self,
        user_id: Optional[str] = None,
        listening_mode: ListeningMode = ListeningMode.PUSH_TO_TALK,
        speech_mode: SpeechMode = SpeechMode.SYNTHESIZED,
    ) -> VoiceSession:
        """Create and register a new active VoiceSession."""
        with self._lock:
            self._cleanup_expired_sessions_locked()

            session = VoiceSession(
                user_id=user_id,
                state=VoiceSessionState.ACTIVE,
                listening_mode=listening_mode,
                speech_mode=speech_mode,
                interaction_count=0,
                created_at=datetime.now(timezone.utc),
                last_active_at=datetime.now(timezone.utc),
            )

            self._sessions[session.session_id] = session
            self._total_created += 1

            logger.info("Created VoiceSession id=%s for user_id=%s", session.session_id, user_id)
            return session

    def get_session(self, session_id: str) -> Optional[VoiceSession]:
        """Retrieve a registered VoiceSession by ID, enforcing timeout expiration."""
        if not session_id:
            raise VoiceValidationException("session_id cannot be empty")

        with self._lock:
            self._cleanup_expired_sessions_locked()
            session = self._sessions.get(session_id)

            if session and session.state == VoiceSessionState.ACTIVE:
                # Update last active timestamp
                session = VoiceSession(
                    session_id=session.session_id,
                    user_id=session.user_id,
                    state=session.state,
                    listening_mode=session.listening_mode,
                    speech_mode=session.speech_mode,
                    interaction_count=session.interaction_count,
                    created_at=session.created_at,
                    last_active_at=datetime.now(timezone.utc),
                    metadata=session.metadata,
                )
                self._sessions[session_id] = session

            return session

    def pause_session(self, session_id: str) -> VoiceSession:
        """Transition an active session to PAUSED state."""
        with self._lock:
            session = self._require_session_locked(session_id)
            if session.state == VoiceSessionState.CLOSED:
                raise VoiceSessionException(f"Cannot pause closed session id={session_id}")

            paused = VoiceSession(
                session_id=session.session_id,
                user_id=session.user_id,
                state=VoiceSessionState.PAUSED,
                listening_mode=session.listening_mode,
                speech_mode=session.speech_mode,
                interaction_count=session.interaction_count,
                created_at=session.created_at,
                last_active_at=datetime.now(timezone.utc),
                metadata=session.metadata,
            )
            self._sessions[session_id] = paused
            logger.info("Paused VoiceSession id=%s", session_id)
            return paused

    def resume_session(self, session_id: str) -> VoiceSession:
        """Transition a paused session back to ACTIVE state."""
        with self._lock:
            session = self._require_session_locked(session_id)
            if session.state == VoiceSessionState.CLOSED:
                raise VoiceSessionException(f"Cannot resume closed session id={session_id}")

            resumed = VoiceSession(
                session_id=session.session_id,
                user_id=session.user_id,
                state=VoiceSessionState.ACTIVE,
                listening_mode=session.listening_mode,
                speech_mode=session.speech_mode,
                interaction_count=session.interaction_count,
                created_at=session.created_at,
                last_active_at=datetime.now(timezone.utc),
                metadata=session.metadata,
            )
            self._sessions[session_id] = resumed
            logger.info("Resumed VoiceSession id=%s", session_id)
            return resumed

    def close_session(self, session_id: str) -> VoiceSession:
        """Transition a session to CLOSED state and mark inactive."""
        with self._lock:
            session = self._require_session_locked(session_id)

            closed = VoiceSession(
                session_id=session.session_id,
                user_id=session.user_id,
                state=VoiceSessionState.CLOSED,
                listening_mode=session.listening_mode,
                speech_mode=session.speech_mode,
                interaction_count=session.interaction_count,
                created_at=session.created_at,
                last_active_at=datetime.now(timezone.utc),
                metadata=session.metadata,
            )
            self._sessions[session_id] = closed
            logger.info("Closed VoiceSession id=%s", session_id)
            return closed

    def list_active_sessions(self) -> List[VoiceSession]:
        """List all currently ACTIVE sessions."""
        with self._lock:
            self._cleanup_expired_sessions_locked()
            return [s for s in self._sessions.values() if s.state == VoiceSessionState.ACTIVE]

    def clear(self) -> None:
        """Reset session manager state."""
        with self._lock:
            self._sessions.clear()
            self._total_created = 0

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    def _require_session_locked(self, session_id: str) -> VoiceSession:
        if not session_id or session_id not in self._sessions:
            raise VoiceSessionException(f"VoiceSession id={session_id} not found")
        return self._sessions[session_id]

    def _cleanup_expired_sessions_locked(self) -> None:
        now = datetime.now(timezone.utc)
        expired_ids: List[str] = []

        for s_id, s in self._sessions.items():
            if s.state in (VoiceSessionState.ACTIVE, VoiceSessionState.PAUSED):
                elapsed = (now - s.last_active_at).total_seconds()
                if elapsed > self._session_timeout:
                    expired_ids.append(s_id)

        for s_id in expired_ids:
            s = self._sessions[s_id]
            self._sessions[s_id] = VoiceSession(
                session_id=s.session_id,
                user_id=s.user_id,
                state=VoiceSessionState.EXPIRED,
                listening_mode=s.listening_mode,
                speech_mode=s.speech_mode,
                interaction_count=s.interaction_count,
                created_at=s.created_at,
                last_active_at=now,
                metadata=s.metadata,
            )
            logger.info("VoiceSession id=%s expired after %.1fs timeout", s_id, self._session_timeout)
