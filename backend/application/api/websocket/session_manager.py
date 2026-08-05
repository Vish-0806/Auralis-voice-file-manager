"""API WebSocket Session Manager Implementation (Phase 15.7).

Thread-safe session manager handling WebSocket logical user sessions,
connection registrations, disconnects, and session terminations without networking or socket dependencies.
"""

import logging
from threading import RLock
from typing import Dict, Optional, Tuple

from backend.application.api.websocket.exceptions import ConnectionException
from backend.application.api.websocket.interfaces import ISessionManager
from backend.application.api.websocket.models import (
    ConnectionState,
    WebSocketConnection,
    WebSocketSession,
)

logger = logging.getLogger(__name__)


class SessionManager(ISessionManager):
    """Thread-safe session manager managing user sessions and underlying active connections."""

    def __init__(self) -> None:
        """Initialize SessionManager using Constructor Dependency Injection."""
        self._lock = RLock()
        self._sessions: Dict[str, WebSocketSession] = {}
        self._connection_map: Dict[str, WebSocketConnection] = {}

        self._total_sessions_created = 0
        self._total_connections_registered = 0
        self._total_disconnects = 0
        self._total_session_closes = 0

    def create_session(
        self, session_id: str, user_id: Optional[str] = None
    ) -> WebSocketSession:
        """Create a new WebSocket user session.

        Args:
            session_id: Unique session identifier.
            user_id: Optional associated user identifier.

        Returns:
            WebSocketSession: Immutable session instance.

        Raises:
            ConnectionException: If session_id is already registered.
        """
        with self._lock:
            if session_id in self._sessions:
                raise ConnectionException(
                    f"WebSocket session with ID '{session_id}' already exists."
                )

            session = WebSocketSession(session_id=session_id, user_id=user_id)
            self._sessions[session_id] = session
            self._total_sessions_created += 1
            logger.info("Created WebSocket session ID '%s' for user '%s'.", session_id, user_id)
            return session

    def register_connection(
        self, session_id: str, connection: WebSocketConnection
    ) -> WebSocketConnection:
        """Register a new connection under an existing session.

        Args:
            session_id: Target session ID.
            connection: Immutable WebSocketConnection instance.

        Returns:
            WebSocketConnection: Registered connection instance.

        Raises:
            ConnectionException: If session is missing or connection_id already exists.
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise ConnectionException(
                    f"Target session ID '{session_id}' not found for connection registration."
                )

            if connection.connection_id in self._connection_map:
                raise ConnectionException(
                    f"WebSocket connection with ID '{connection.connection_id}' already exists."
                )

            self._connection_map[connection.connection_id] = connection
            updated_connections = session.connections + (connection,)
            updated_session = WebSocketSession(
                session_id=session.session_id,
                user_id=session.user_id,
                connections=updated_connections,
                is_active=session.is_active,
                created_at=session.created_at,
                metadata=session.metadata,
            )
            self._sessions[session_id] = updated_session
            self._total_connections_registered += 1
            logger.info(
                "Registered connection ID '%s' under session ID '%s'.",
                connection.connection_id,
                session_id,
            )
            return connection

    def lookup_connection(self, connection_id: str) -> Optional[WebSocketConnection]:
        """Look up a connection by connection ID.

        Args:
            connection_id: Unique connection identifier.

        Returns:
            Optional[WebSocketConnection]: Connection if found, else None.
        """
        with self._lock:
            return self._connection_map.get(connection_id)

    def lookup_session(self, session_id: str) -> Optional[WebSocketSession]:
        """Look up a session by session ID.

        Args:
            session_id: Unique session identifier.

        Returns:
            Optional[WebSocketSession]: Session if found, else None.
        """
        with self._lock:
            return self._sessions.get(session_id)

    def disconnect_connection(
        self, connection_id: str
    ) -> Optional[WebSocketConnection]:
        """Mark a connection state as DISCONNECTED.

        Args:
            connection_id: Unique connection identifier.

        Returns:
            Optional[WebSocketConnection]: Updated connection if found, else None.
        """
        with self._lock:
            conn = self._connection_map.get(connection_id)
            if conn is None:
                return None

            updated_conn = WebSocketConnection(
                connection_id=conn.connection_id,
                session_id=conn.session_id,
                state=ConnectionState.DISCONNECTED,
                client_ip=conn.client_ip,
                connected_at=conn.connected_at,
                metadata=conn.metadata,
            )
            self._connection_map[connection_id] = updated_conn

            # Update connection in session as well
            session = self._sessions.get(conn.session_id)
            if session is not None:
                new_conns = tuple(
                    updated_conn if c.connection_id == connection_id else c
                    for c in session.connections
                )
                self._sessions[conn.session_id] = WebSocketSession(
                    session_id=session.session_id,
                    user_id=session.user_id,
                    connections=new_conns,
                    is_active=session.is_active,
                    created_at=session.created_at,
                    metadata=session.metadata,
                )

            self._total_disconnects += 1
            logger.info("Disconnected connection ID '%s'.", connection_id)
            return updated_conn

    def close_session(self, session_id: str) -> Optional[WebSocketSession]:
        """Close a session and transition all associated connections to CLOSED.

        Args:
            session_id: Unique session identifier.

        Returns:
            Optional[WebSocketSession]: Updated session if found, else None.
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None

            closed_conns = []
            for conn in session.connections:
                closed = WebSocketConnection(
                    connection_id=conn.connection_id,
                    session_id=conn.session_id,
                    state=ConnectionState.CLOSED,
                    client_ip=conn.client_ip,
                    connected_at=conn.connected_at,
                    metadata=conn.metadata,
                )
                self._connection_map[conn.connection_id] = closed
                closed_conns.append(closed)

            updated_session = WebSocketSession(
                session_id=session.session_id,
                user_id=session.user_id,
                connections=tuple(closed_conns),
                is_active=False,
                created_at=session.created_at,
                metadata=session.metadata,
            )
            self._sessions[session_id] = updated_session
            self._total_session_closes += 1
            logger.info("Closed session ID '%s'.", session_id)
            return updated_session

    def list_active_connections(self) -> Tuple[WebSocketConnection, ...]:
        """List all active connections across sessions.

        Returns:
            Tuple[WebSocketConnection, ...]: Tuple of CONNECTED connections.
        """
        with self._lock:
            return tuple(
                c for c in self._connection_map.values() if c.state == ConnectionState.CONNECTED
            )

    def list_active_sessions(self) -> Tuple[WebSocketSession, ...]:
        """List all active sessions.

        Returns:
            Tuple[WebSocketSession, ...]: Tuple of active sessions.
        """
        with self._lock:
            return tuple(s for s in self._sessions.values() if s.is_active)

    def count_sessions(self) -> int:
        """Get total session count.

        Returns:
            int: Session count.
        """
        with self._lock:
            return len(self._sessions)

    def count_connections(self) -> int:
        """Get total active connection count.

        Returns:
            int: Active connection count.
        """
        with self._lock:
            return sum(
                1 for c in self._connection_map.values() if c.state == ConnectionState.CONNECTED
            )

    def clear(self) -> None:
        """Clear all sessions and connections from the manager."""
        with self._lock:
            self._sessions.clear()
            self._connection_map.clear()
            logger.info("SessionManager cleared.")

    def get_session_telemetry(self) -> Dict[str, int]:
        """Get internal session telemetry counters under lock."""
        with self._lock:
            return {
                "total_sessions_created": self._total_sessions_created,
                "total_connections_registered": self._total_connections_registered,
                "total_disconnects": self._total_disconnects,
                "total_session_closes": self._total_session_closes,
                "active_sessions_count": self.count_sessions(),
                "active_connections_count": self.count_connections(),
            }
