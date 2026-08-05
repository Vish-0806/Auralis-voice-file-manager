"""API Session Manager Implementation (Phase 15.4).

Thread-safe session manager maintaining in-memory authentication sessions, ttl expiration,
and session revocations without cookies, JWTs, or network dependencies.
"""

from datetime import datetime, timedelta, timezone
import logging
from threading import RLock
from typing import Dict, Optional, Tuple
import uuid

from backend.application.api.auth.interfaces import ISessionManager
from backend.application.api.auth.models import (
    AuthenticationSession,
    AuthenticationState,
)

logger = logging.getLogger(__name__)


class SessionManager(ISessionManager):
    """Thread-safe in-memory session manager."""

    def __init__(self) -> None:
        """Initialize SessionManager using Constructor Dependency Injection."""
        self._lock = RLock()
        self._sessions: Dict[str, AuthenticationSession] = {}

    def create_session(
        self, identity_id: str, ttl_seconds: Optional[float] = 3600.0
    ) -> AuthenticationSession:
        """Create a new authentication session for an identity.

        Args:
            identity_id: Target identity ID.
            ttl_seconds: Optional session time-to-live in seconds.

        Returns:
            AuthenticationSession: Created session snapshot.
        """
        with self._lock:
            now = datetime.now(timezone.utc)
            expires_at = (
                now + timedelta(seconds=ttl_seconds) if ttl_seconds is not None else None
            )
            session_id = f"sess_{uuid.uuid4().hex[:12]}"

            session = AuthenticationSession(
                session_id=session_id,
                identity_id=identity_id,
                state=AuthenticationState.AUTHENTICATED,
                created_at=now,
                expires_at=expires_at,
                last_accessed_at=now,
            )

            self._sessions[session_id] = session
            logger.info("Created authentication session '%s' for identity ID '%s'.", session_id, identity_id)
            return session

    def get_session(self, session_id: str) -> Optional[AuthenticationSession]:
        """Get a session by session ID, automatically checking for expiration.

        Args:
            session_id: Unique session identifier.

        Returns:
            Optional[AuthenticationSession]: Session if found, else None.
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None

            now = datetime.now(timezone.utc)

            # Check expiration
            if (
                session.state == AuthenticationState.AUTHENTICATED
                and session.expires_at is not None
                and now > session.expires_at
            ):
                updated = session.model_copy(
                    update={"state": AuthenticationState.EXPIRED, "last_accessed_at": now}
                )
                self._sessions[session_id] = updated
                logger.info("Session '%s' marked as EXPIRED.", session_id)
                return updated

            # Touch last_accessed_at if active
            if session.state == AuthenticationState.AUTHENTICATED:
                updated = session.model_copy(update={"last_accessed_at": now})
                self._sessions[session_id] = updated
                return updated

            return session

    def revoke_session(self, session_id: str) -> Optional[AuthenticationSession]:
        """Revoke an active authentication session.

        Args:
            session_id: Target session ID.

        Returns:
            Optional[AuthenticationSession]: Updated session if found, else None.
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None

            if session.state == AuthenticationState.REVOKED:
                return session

            updated = session.model_copy(
                update={
                    "state": AuthenticationState.REVOKED,
                    "last_accessed_at": datetime.now(timezone.utc),
                }
            )
            self._sessions[session_id] = updated
            logger.info("Session '%s' REVOKED.", session_id)
            return updated

    def expire_session(self, session_id: str) -> Optional[AuthenticationSession]:
        """Expire an active authentication session explicitly.

        Args:
            session_id: Target session ID.

        Returns:
            Optional[AuthenticationSession]: Updated session if found, else None.
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None

            if session.state == AuthenticationState.EXPIRED:
                return session

            updated = session.model_copy(
                update={
                    "state": AuthenticationState.EXPIRED,
                    "last_accessed_at": datetime.now(timezone.utc),
                }
            )
            self._sessions[session_id] = updated
            logger.info("Session '%s' explicitly EXPIRED.", session_id)
            return updated

    def list_active_sessions(self) -> Tuple[AuthenticationSession, ...]:
        """List all currently active (unexpired, non-revoked) sessions.

        Returns:
            Tuple[AuthenticationSession, ...]: Immutable tuple of active sessions.
        """
        with self._lock:
            now = datetime.now(timezone.utc)
            active = []
            for s in list(self._sessions.values()):
                # Trigger internal expiration evaluation if needed
                checked = self.get_session(s.session_id)
                if checked and checked.state == AuthenticationState.AUTHENTICATED:
                    active.append(checked)
            return tuple(active)

    def count_sessions(self) -> int:
        """Get total count of all sessions stored.

        Returns:
            int: Number of sessions.
        """
        with self._lock:
            return len(self._sessions)

    def get_session_telemetry(self) -> Dict[str, int]:
        """Get session telemetry counters under lock."""
        with self._lock:
            active_count = 0
            expired_count = 0
            revoked_count = 0
            for s in self._sessions.values():
                if s.state == AuthenticationState.AUTHENTICATED:
                    active_count += 1
                elif s.state == AuthenticationState.EXPIRED:
                    expired_count += 1
                elif s.state == AuthenticationState.REVOKED:
                    revoked_count += 1

            return {
                "total_sessions": len(self._sessions),
                "active_sessions": active_count,
                "expired_sessions": expired_count,
                "revoked_sessions": revoked_count,
            }
