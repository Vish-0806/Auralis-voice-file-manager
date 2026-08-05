"""API WebSocket Provider Implementation (Phase 15.7).

Thread-safe WebSocket provider aggregating SessionManager, ChannelManager,
and MessageRouter with full lifecycle management, health monitoring,
statistics tracking, and diagnostic telemetry.
"""

from datetime import datetime, timezone
import logging
from threading import RLock
import threading
from typing import Optional, Tuple

from backend.application.api.websocket.channel_manager import ChannelManager
from backend.application.api.websocket.interfaces import (
    IChannelManager,
    IMessageRouter,
    ISessionManager,
    IWebSocketProvider,
)
from backend.application.api.websocket.message_router import MessageRouter
from backend.application.api.websocket.models import (
    WebSocketCapabilities,
    WebSocketDiagnostics,
    WebSocketHealth,
    WebSocketRuntimeState,
    WebSocketStatistics,
)
from backend.application.api.websocket.session_manager import SessionManager

logger = logging.getLogger(__name__)


class WebSocketProvider(IWebSocketProvider):
    """Production thread-safe WebSocket provider aggregating websocket management components."""

    def __init__(
        self,
        session_manager: Optional[ISessionManager] = None,
        channel_manager: Optional[IChannelManager] = None,
        message_router: Optional[IMessageRouter] = None,
        capabilities: Optional[WebSocketCapabilities] = None,
    ) -> None:
        """Initialize WebSocketProvider using Constructor Dependency Injection.

        Args:
            session_manager: Optional ISessionManager implementation instance.
            channel_manager: Optional IChannelManager implementation instance.
            message_router: Optional IMessageRouter implementation instance.
            capabilities: Optional WebSocketCapabilities instance.
        """
        self._lock = RLock()
        self._session_manager = session_manager or SessionManager()
        self._channel_manager = channel_manager or ChannelManager()
        self._message_router = message_router or MessageRouter(
            session_manager=self._session_manager,
            channel_manager=self._channel_manager,
        )
        self._capabilities = capabilities or WebSocketCapabilities()

        self._status = WebSocketRuntimeState.UNINITIALIZED
        self._total_initializations = 0
        self._total_restarts = 0
        self._total_shutdowns = 0

    def initialize(self) -> WebSocketHealth:
        """Initialize the WebSocket provider and transition state to READY.

        Returns:
            WebSocketHealth: Updated health snapshot.
        """
        with self._lock:
            if self._status in (
                WebSocketRuntimeState.INITIALIZING,
                WebSocketRuntimeState.READY,
            ):
                return self.health()

            self._status = WebSocketRuntimeState.INITIALIZING
            logger.info("WebSocketProvider transitioning to INITIALIZING state.")

            self._status = WebSocketRuntimeState.READY
            self._total_initializations += 1
            logger.info("WebSocketProvider successfully initialized and READY.")
            return self.health()

    def shutdown(self) -> WebSocketHealth:
        """Shutdown the WebSocket provider safely and transition state to STOPPED.

        Returns:
            WebSocketHealth: Updated health snapshot.
        """
        with self._lock:
            if self._status == WebSocketRuntimeState.STOPPED:
                return self.health()

            self._status = WebSocketRuntimeState.STOPPING
            logger.info("WebSocketProvider transitioning to STOPPING state.")

            self._status = WebSocketRuntimeState.STOPPED
            self._total_shutdowns += 1
            logger.info("WebSocketProvider successfully stopped.")
            return self.health()

    def restart(self) -> WebSocketHealth:
        """Restart the WebSocket provider by shutting down if active, then initializing.

        Returns:
            WebSocketHealth: Updated health snapshot.
        """
        with self._lock:
            logger.info("WebSocketProvider restarting...")
            if self._status != WebSocketRuntimeState.STOPPED:
                self.shutdown()

            health = self.initialize()
            self._total_restarts += 1
            return health

    def health(self) -> WebSocketHealth:
        """Get health status evaluation snapshot.

        Returns:
            WebSocketHealth: Immutable health snapshot.
        """
        with self._lock:
            is_healthy = self._status in (
                WebSocketRuntimeState.READY,
                WebSocketRuntimeState.UNINITIALIZED,
            )
            issues: Tuple[str, ...] = ()
            if not is_healthy:
                issues = (f"WebSocket provider is in state: {self._status.value}",)

            return WebSocketHealth(
                is_healthy=is_healthy,
                state=self._status,
                details={
                    "status": self._status.value,
                    "sessions_count": self._session_manager.count_sessions(),
                    "connections_count": self._session_manager.count_connections(),
                    "channels_count": self._channel_manager.count_channels(),
                },
                issues=issues,
                checked_at=datetime.now(timezone.utc),
            )

    def statistics(self) -> WebSocketStatistics:
        """Get aggregate metrics and statistics.

        Returns:
            WebSocketStatistics: Immutable statistics snapshot.
        """
        with self._lock:
            total_sessions = self._session_manager.count_sessions()
            active_connections = self._session_manager.count_connections()
            total_channels = self._channel_manager.count_channels()

            channel_telemetry = {}
            if hasattr(self._channel_manager, "get_channel_telemetry"):
                channel_telemetry = getattr(
                    self._channel_manager, "get_channel_telemetry"
                )()

            total_subs = channel_telemetry.get("current_subscriptions_count", 0)

            router_telemetry = {}
            if hasattr(self._message_router, "get_router_telemetry"):
                router_telemetry = getattr(
                    self._message_router, "get_router_telemetry"
                )()

            return WebSocketStatistics(
                total_sessions=total_sessions,
                active_connections=active_connections,
                total_channels=total_channels,
                total_subscriptions=total_subs,
                total_messages_routed=router_telemetry.get("total_routed_messages", 0),
                total_broadcast_plans=router_telemetry.get("total_broadcast_plans", 0),
                metrics={
                    "total_initializations": float(self._total_initializations),
                    "total_restarts": float(self._total_restarts),
                    "total_shutdowns": float(self._total_shutdowns),
                },
            )

    def capabilities(self) -> WebSocketCapabilities:
        """Get declared capabilities snapshot.

        Returns:
            WebSocketCapabilities: Immutable capabilities.
        """
        with self._lock:
            return self._capabilities

    def diagnostics(self) -> WebSocketDiagnostics:
        """Get diagnostic telemetry snapshot.

        Returns:
            WebSocketDiagnostics: Immutable diagnostics.
        """
        with self._lock:
            total_sessions = self._session_manager.count_sessions()
            total_conns = self._session_manager.count_connections()
            total_channels = self._channel_manager.count_channels()
            messages: Tuple[str, ...] = (
                f"Status: {self._status.value}",
                f"Active Sessions: {total_sessions}",
                f"Active Connections: {total_conns}",
                f"Active Channels: {total_channels}",
                f"Initializations: {self._total_initializations}",
                f"Restarts: {self._total_restarts}",
            )
            return WebSocketDiagnostics(
                state=self._status,
                active_sessions_count=total_sessions,
                active_connections_count=total_conns,
                active_channels_count=total_channels,
                timestamp=datetime.now(timezone.utc),
                thread_count=threading.active_count(),
                diagnostic_messages=messages,
                details={
                    "status": self._status.value,
                    "total_shutdowns": self._total_shutdowns,
                },
            )

    def get_session_manager(self) -> ISessionManager:
        """Get encapsulated session manager.

        Returns:
            ISessionManager: Session manager.
        """
        with self._lock:
            return self._session_manager

    def get_channel_manager(self) -> IChannelManager:
        """Get encapsulated channel manager.

        Returns:
            IChannelManager: Channel manager.
        """
        with self._lock:
            return self._channel_manager

    def get_message_router(self) -> IMessageRouter:
        """Get encapsulated message router.

        Returns:
            IMessageRouter: Message router.
        """
        with self._lock:
            return self._message_router
