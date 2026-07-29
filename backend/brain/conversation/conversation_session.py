"""Conversation Session Manager for managing conversational session lifecycle and state.

This module provides thread-safe session state management without performing reasoning,
LLM calls, conversation summarization, or reference resolution.
"""

from datetime import datetime, timezone
from enum import Enum
import logging
import threading
from typing import Any, Dict, List, Optional
import uuid

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class ConversationSessionStatus(str, Enum):
    """Enumeration representing the possible states of a conversation session."""

    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    WAITING_FOR_USER = "WAITING_FOR_USER"
    COMPLETED = "COMPLETED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class ConversationTurn(BaseModel):
    """Immutable model representing a single message/turn in a conversation session."""

    model_config = ConfigDict(frozen=True)

    turn_id: str
    role: str
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationSession(BaseModel):
    """Model representing an active or historical conversation session."""

    session_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    last_activity: datetime
    status: ConversationSessionStatus = ConversationSessionStatus.ACTIVE
    title: Optional[str] = None
    conversation_turns: List[ConversationTurn] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationSessionConfig(BaseModel):
    """Configuration options for ConversationSessionManager limits and timeouts."""

    maximum_sessions: int = 500
    maximum_turns_per_session: int = 1000
    session_timeout_seconds: int = 3600
    history_limit: int = 5000


class ConversationSessionManager:
    """Thread-safe manager responsible for the lifecycle of conversation sessions.

    Internal storage uses RLock protection for all read, write, history transition,
    and cleanup operations.
    """

    def __init__(self, config: Optional[ConversationSessionConfig] = None) -> None:
        """Initializes the manager with optional configuration and thread lock."""
        self.config = config or ConversationSessionConfig()
        self._active_sessions: Dict[str, ConversationSession] = {}
        self._completed_sessions: Dict[str, ConversationSession] = {}
        self._lock = threading.RLock()

    def create_session(
        self,
        user_id: str,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> ConversationSession:
        """Creates and registers a new active conversation session."""
        with self._lock:
            # Enforce active session capacity limit by expiring or purging oldest active session
            if len(self._active_sessions) >= self.config.maximum_sessions:
                self._expire_sessions_locked()
                if len(self._active_sessions) >= self.config.maximum_sessions:
                    # Remove oldest active session if capacity is still exceeded
                    oldest_id = next(iter(self._active_sessions))
                    oldest = self._active_sessions.pop(oldest_id)
                    oldest.status = ConversationSessionStatus.EXPIRED
                    oldest.updated_at = datetime.now(timezone.utc)
                    self._completed_sessions[oldest_id] = oldest
                    self._enforce_history_limit()

            sid = session_id or f"session_{uuid.uuid4().hex[:12]}"
            now = datetime.now(timezone.utc)
            session = ConversationSession(
                session_id=sid,
                user_id=user_id,
                created_at=now,
                updated_at=now,
                last_activity=now,
                status=ConversationSessionStatus.ACTIVE,
                title=title,
                conversation_turns=[],
                metadata=metadata or {},
            )
            self._active_sessions[sid] = session
            logger.info("Conversation Session Created: session_id=%s, user_id=%s", sid, user_id)
            return session

    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Retrieves a session by ID from active or completed stores without throwing exceptions."""
        with self._lock:
            session = self._active_sessions.get(session_id)
            if session is not None:
                # Check for expiration on active session lookup
                elapsed = (datetime.now(timezone.utc) - session.last_activity).total_seconds()
                if elapsed > self.config.session_timeout_seconds:
                    self._active_sessions.pop(session_id)
                    session.status = ConversationSessionStatus.EXPIRED
                    session.updated_at = datetime.now(timezone.utc)
                    self._completed_sessions[session_id] = session
                    self._enforce_history_limit()
                    logger.info("Conversation Session Expired: session_id=%s", session_id)
                return session

            return self._completed_sessions.get(session_id)

    def list_sessions(self, user_id: Optional[str] = None) -> List[ConversationSession]:
        """Lists all active and completed sessions, optionally filtered by user_id."""
        with self._lock:
            all_sessions = list(self._active_sessions.values()) + list(self._completed_sessions.values())
            if user_id is not None:
                return [s for s in all_sessions if s.user_id == user_id]
            return all_sessions

    def list_active_sessions(self, user_id: Optional[str] = None) -> List[ConversationSession]:
        """Lists currently active sessions after running expiration check, optionally filtered by user_id."""
        with self._lock:
            self._expire_sessions_locked()
            active_list = list(self._active_sessions.values())
            if user_id is not None:
                return [s for s in active_list if s.user_id == user_id]
            return active_list

    def add_turn(
        self,
        session_id: str,
        role: str,
        content: str,
        turn_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[ConversationTurn]:
        """Appends a new turn to an active session, updating session timestamps."""
        with self._lock:
            session = self._active_sessions.get(session_id)
            if session is None:
                return None

            # Check if session has expired
            now = datetime.now(timezone.utc)
            if (now - session.last_activity).total_seconds() > self.config.session_timeout_seconds:
                self._active_sessions.pop(session_id)
                session.status = ConversationSessionStatus.EXPIRED
                session.updated_at = now
                self._completed_sessions[session_id] = session
                self._enforce_history_limit()
                logger.info("Conversation Session Expired: session_id=%s", session_id)
                return None

            if len(session.conversation_turns) >= self.config.maximum_turns_per_session:
                return None

            tid = turn_id or f"turn_{uuid.uuid4().hex[:12]}"
            turn = ConversationTurn(
                turn_id=tid,
                role=role,
                content=content,
                timestamp=now,
                metadata=metadata or {},
            )
            session.conversation_turns.append(turn)
            session.updated_at = now
            session.last_activity = now
            logger.info("Conversation Turn Added: session_id=%s, turn_id=%s", session_id, tid)
            return turn

    def get_turns(self, session_id: str) -> List[ConversationTurn]:
        """Returns all turns for a session in chronological order, or empty list if session not found."""
        with self._lock:
            session = self.get_session(session_id)
            if session is None:
                return []
            return list(session.conversation_turns)

    def pause_session(self, session_id: str) -> bool:
        """Transitions an active or waiting session to PAUSED status."""
        with self._lock:
            session = self._active_sessions.get(session_id)
            if session is None:
                return False

            if session.status in (ConversationSessionStatus.ACTIVE, ConversationSessionStatus.WAITING_FOR_USER):
                session.status = ConversationSessionStatus.PAUSED
                session.updated_at = datetime.now(timezone.utc)
                logger.info("Conversation Session Paused: session_id=%s", session_id)
                return True

            return False

    def resume_session(self, session_id: str) -> bool:
        """Resumes a PAUSED session back to ACTIVE status."""
        with self._lock:
            session = self._active_sessions.get(session_id)
            if session is None:
                return False

            if session.status == ConversationSessionStatus.PAUSED:
                now = datetime.now(timezone.utc)
                session.status = ConversationSessionStatus.ACTIVE
                session.updated_at = now
                session.last_activity = now
                logger.info("Conversation Session Resumed: session_id=%s", session_id)
                return True

            return False

    def complete_session(self, session_id: str) -> bool:
        """Marks an active session as COMPLETED and moves it to history."""
        with self._lock:
            if session_id not in self._active_sessions:
                return False

            session = self._active_sessions.pop(session_id)
            now = datetime.now(timezone.utc)
            session.status = ConversationSessionStatus.COMPLETED
            session.updated_at = now
            self._completed_sessions[session_id] = session
            self._enforce_history_limit()
            logger.info("Conversation Session Completed: session_id=%s", session_id)
            return True

    def cancel_session(self, session_id: str) -> bool:
        """Marks an active session as CANCELLED and moves it to history."""
        with self._lock:
            if session_id not in self._active_sessions:
                return False

            session = self._active_sessions.pop(session_id)
            now = datetime.now(timezone.utc)
            session.status = ConversationSessionStatus.CANCELLED
            session.updated_at = now
            self._completed_sessions[session_id] = session
            self._enforce_history_limit()
            logger.info("Conversation Session Cancelled: session_id=%s", session_id)
            return True

    def expire_sessions(self, timeout_seconds: Optional[int] = None) -> List[str]:
        """Scans active sessions and transitions inactive sessions to EXPIRED history."""
        with self._lock:
            return self._expire_sessions_locked(timeout_seconds)

    def remove_session(self, session_id: str) -> bool:
        """Removes a session completely from active or completed stores."""
        with self._lock:
            if session_id in self._active_sessions:
                del self._active_sessions[session_id]
                logger.info("Conversation Session Removed: session_id=%s", session_id)
                return True

            if session_id in self._completed_sessions:
                del self._completed_sessions[session_id]
                logger.info("Conversation Session Removed: session_id=%s", session_id)
                return True

            return False

    def clear(self) -> None:
        """Clears all active and completed sessions."""
        with self._lock:
            self._active_sessions.clear()
            self._completed_sessions.clear()
            logger.info("Conversation Manager Cleared")

    def _expire_sessions_locked(self, timeout_seconds: Optional[int] = None) -> List[str]:
        """Internal helper to expire inactive sessions under lock."""
        timeout = timeout_seconds if timeout_seconds is not None else self.config.session_timeout_seconds
        now = datetime.now(timezone.utc)
        expired_ids: List[str] = []
        active_keys = list(self._active_sessions.keys())

        for sid in active_keys:
            session = self._active_sessions[sid]
            elapsed = (now - session.last_activity).total_seconds()
            if elapsed > timeout:
                self._active_sessions.pop(sid)
                session.status = ConversationSessionStatus.EXPIRED
                session.updated_at = now
                self._completed_sessions[sid] = session
                self._enforce_history_limit()
                logger.info("Conversation Session Expired: session_id=%s", sid)
                expired_ids.append(sid)

        return expired_ids

    def _enforce_history_limit(self) -> None:
        """Internal helper to enforce maximum history limit on completed sessions."""
        while len(self._completed_sessions) > self.config.history_limit:
            oldest_key = next(iter(self._completed_sessions))
            del self._completed_sessions[oldest_key]
