"""API WebSocket Interfaces (Phase 15.7).

Defines Abstract Base Classes (ABCs) establishing design contracts for the Session Manager,
Channel Manager, Message Router, WebSocket Provider, and WebSocket Runtime.
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple

from backend.application.api.websocket.models import (
    BroadcastPlan,
    ChannelSubscription,
    WebSocketCapabilities,
    WebSocketChannel,
    WebSocketConnection,
    WebSocketDiagnostics,
    WebSocketHealth,
    WebSocketMessage,
    WebSocketSession,
    WebSocketStatistics,
)


class ISessionManager(ABC):
    """Abstract interface for the WebSocket Session Manager."""

    @abstractmethod
    def create_session(
        self, session_id: str, user_id: Optional[str] = None
    ) -> WebSocketSession:
        """Create a new WebSocket user session.

        Args:
            session_id: Unique session identifier.
            user_id: Optional associated user ID.

        Returns:
            WebSocketSession: Created session model.
        """
        raise NotImplementedError

    @abstractmethod
    def register_connection(
        self, session_id: str, connection: WebSocketConnection
    ) -> WebSocketConnection:
        """Register a new connection under an existing session.

        Args:
            session_id: Target session ID.
            connection: Immutable WebSocketConnection instance.

        Returns:
            WebSocketConnection: Registered connection instance.
        """
        raise NotImplementedError

    @abstractmethod
    def lookup_connection(self, connection_id: str) -> Optional[WebSocketConnection]:
        """Look up a connection by connection ID.

        Args:
            connection_id: Unique connection identifier.

        Returns:
            Optional[WebSocketConnection]: Connection if found, else None.
        """
        raise NotImplementedError

    @abstractmethod
    def lookup_session(self, session_id: str) -> Optional[WebSocketSession]:
        """Look up a session by session ID.

        Args:
            session_id: Unique session identifier.

        Returns:
            Optional[WebSocketSession]: Session if found, else None.
        """
        raise NotImplementedError

    @abstractmethod
    def disconnect_connection(
        self, connection_id: str
    ) -> Optional[WebSocketConnection]:
        """Mark a connection state as DISCONNECTED.

        Args:
            connection_id: Unique connection identifier.

        Returns:
            Optional[WebSocketConnection]: Updated connection if found, else None.
        """
        raise NotImplementedError

    @abstractmethod
    def close_session(self, session_id: str) -> Optional[WebSocketSession]:
        """Close a session and disconnect all associated connections.

        Args:
            session_id: Unique session identifier.

        Returns:
            Optional[WebSocketSession]: Updated session if found, else None.
        """
        raise NotImplementedError

    @abstractmethod
    def list_active_connections(self) -> Tuple[WebSocketConnection, ...]:
        """List all active connections across all sessions.

        Returns:
            Tuple[WebSocketConnection, ...]: Immutable tuple of connections.
        """
        raise NotImplementedError

    @abstractmethod
    def list_active_sessions(self) -> Tuple[WebSocketSession, ...]:
        """List all active sessions.

        Returns:
            Tuple[WebSocketSession, ...]: Immutable tuple of sessions.
        """
        raise NotImplementedError

    @abstractmethod
    def count_sessions(self) -> int:
        """Get total session count.

        Returns:
            int: Session count.
        """
        raise NotImplementedError

    @abstractmethod
    def count_connections(self) -> int:
        """Get total active connection count.

        Returns:
            int: Connection count.
        """
        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        """Clear all sessions and connections from the manager."""
        raise NotImplementedError


class IChannelManager(ABC):
    """Abstract interface for the WebSocket Channel Manager."""

    @abstractmethod
    def register_channel(self, channel: WebSocketChannel) -> WebSocketChannel:
        """Register a new pub-sub WebSocket channel.

        Args:
            channel: Immutable WebSocketChannel instance.

        Returns:
            WebSocketChannel: Registered channel.
        """
        raise NotImplementedError

    @abstractmethod
    def unregister_channel(self, channel_id: str) -> Optional[WebSocketChannel]:
        """Unregister a channel by channel ID.

        Args:
            channel_id: Unique channel identifier.

        Returns:
            Optional[WebSocketChannel]: Removed channel if found, else None.
        """
        raise NotImplementedError

    @abstractmethod
    def lookup_channel(self, channel_id: str) -> Optional[WebSocketChannel]:
        """Look up a channel by channel ID.

        Args:
            channel_id: Unique channel identifier.

        Returns:
            Optional[WebSocketChannel]: Channel if found, else None.
        """
        raise NotImplementedError

    @abstractmethod
    def subscribe(self, channel_id: str, connection_id: str) -> ChannelSubscription:
        """Subscribe a connection to a channel.

        Args:
            channel_id: Target channel ID.
            connection_id: Target connection ID.

        Returns:
            ChannelSubscription: Created subscription record.
        """
        raise NotImplementedError

    @abstractmethod
    def unsubscribe(
        self, channel_id: str, connection_id: str
    ) -> Optional[ChannelSubscription]:
        """Unsubscribe a connection from a channel.

        Args:
            channel_id: Target channel ID.
            connection_id: Target connection ID.

        Returns:
            Optional[ChannelSubscription]: Removed subscription if present, else None.
        """
        raise NotImplementedError

    @abstractmethod
    def get_channel_subscribers(self, channel_id: str) -> Tuple[str, ...]:
        """Get all connection IDs subscribed to a channel.

        Args:
            channel_id: Unique channel identifier.

        Returns:
            Tuple[str, ...]: Tuple of subscribed connection IDs.
        """
        raise NotImplementedError

    @abstractmethod
    def list_channels(self) -> Tuple[WebSocketChannel, ...]:
        """List all registered channels.

        Returns:
            Tuple[WebSocketChannel, ...]: Tuple of channels.
        """
        raise NotImplementedError

    @abstractmethod
    def count_channels(self) -> int:
        """Get total count of registered channels.

        Returns:
            int: Channel count.
        """
        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        """Clear all channels and subscriptions from the manager."""
        raise NotImplementedError


class IMessageRouter(ABC):
    """Abstract interface for the WebSocket Message Router."""

    @abstractmethod
    def route_direct(self, message: WebSocketMessage) -> BroadcastPlan:
        """Create a BroadcastPlan for a direct point-to-point message.

        Args:
            message: WebSocketMessage containing target_connection_id.

        Returns:
            BroadcastPlan: Generated routing plan.
        """
        raise NotImplementedError

    @abstractmethod
    def route_channel(self, message: WebSocketMessage) -> BroadcastPlan:
        """Create a BroadcastPlan for a channel broadcast message.

        Args:
            message: WebSocketMessage containing target_channel_id.

        Returns:
            BroadcastPlan: Generated routing plan.
        """
        raise NotImplementedError

    @abstractmethod
    def plan_broadcast(
        self, message: WebSocketMessage, target_connection_ids: Tuple[str, ...]
    ) -> BroadcastPlan:
        """Create an explicit BroadcastPlan targeting given connection IDs.

        Args:
            message: Target WebSocketMessage instance.
            target_connection_ids: Tuple of recipient connection IDs.

        Returns:
            BroadcastPlan: Generated routing plan.
        """
        raise NotImplementedError

    @abstractmethod
    def count_routed_messages(self) -> int:
        """Get total count of routed messages.

        Returns:
            int: Total routed messages count.
        """
        raise NotImplementedError


class IWebSocketProvider(ABC):
    """Abstract interface for the WebSocket Provider."""

    @abstractmethod
    def initialize(self) -> WebSocketHealth:
        """Initialize the WebSocket provider.

        Returns:
            WebSocketHealth: Health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def shutdown(self) -> WebSocketHealth:
        """Shutdown the WebSocket provider safely.

        Returns:
            WebSocketHealth: Health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def restart(self) -> WebSocketHealth:
        """Restart the WebSocket provider.

        Returns:
            WebSocketHealth: Health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def health(self) -> WebSocketHealth:
        """Get health evaluation snapshot.

        Returns:
            WebSocketHealth: Health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def statistics(self) -> WebSocketStatistics:
        """Get aggregate statistics.

        Returns:
            WebSocketStatistics: Statistics snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def capabilities(self) -> WebSocketCapabilities:
        """Get declared capabilities.

        Returns:
            WebSocketCapabilities: Capabilities snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def diagnostics(self) -> WebSocketDiagnostics:
        """Get diagnostic telemetry.

        Returns:
            WebSocketDiagnostics: Diagnostics snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def get_session_manager(self) -> ISessionManager:
        """Get encapsulated session manager.

        Returns:
            ISessionManager: Session manager.
        """
        raise NotImplementedError

    @abstractmethod
    def get_channel_manager(self) -> IChannelManager:
        """Get encapsulated channel manager.

        Returns:
            IChannelManager: Channel manager.
        """
        raise NotImplementedError

    @abstractmethod
    def get_message_router(self) -> IMessageRouter:
        """Get encapsulated message router.

        Returns:
            IMessageRouter: Message router.
        """
        raise NotImplementedError


class IWebSocketRuntime(ABC):
    """Abstract interface for the WebSocket Runtime."""

    @abstractmethod
    def initialize(self) -> WebSocketHealth:
        """Initialize the WebSocket runtime.

        Returns:
            WebSocketHealth: Health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def shutdown(self) -> WebSocketHealth:
        """Shutdown the WebSocket runtime safely.

        Returns:
            WebSocketHealth: Health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def restart(self) -> WebSocketHealth:
        """Restart the WebSocket runtime.

        Returns:
            WebSocketHealth: Health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def health(self) -> WebSocketHealth:
        """Get health evaluation snapshot.

        Returns:
            WebSocketHealth: Health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def statistics(self) -> WebSocketStatistics:
        """Get aggregate statistics.

        Returns:
            WebSocketStatistics: Statistics snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def capabilities(self) -> WebSocketCapabilities:
        """Get declared capabilities.

        Returns:
            WebSocketCapabilities: Capabilities snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def diagnostics(self) -> WebSocketDiagnostics:
        """Get diagnostic telemetry.

        Returns:
            WebSocketDiagnostics: Diagnostics snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def get_provider(self) -> IWebSocketProvider:
        """Get encapsulated WebSocket provider.

        Returns:
            IWebSocketProvider: WebSocket provider.
        """
        raise NotImplementedError
