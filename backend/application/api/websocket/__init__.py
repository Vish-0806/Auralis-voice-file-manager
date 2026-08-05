"""API WebSocket Runtime Package (Phase 15.7).

Provider-independent WebSocket Runtime establishing models, exceptions, ABC interfaces,
session manager, channel manager, message router, websocket provider, runtime coordinator,
and singleton accessors.
"""

from backend.application.api.websocket.channel_manager import ChannelManager
from backend.application.api.websocket.exceptions import (
    ChannelException,
    ConnectionException,
    MessageRoutingException,
    SubscriptionException,
    WebSocketException,
)
from backend.application.api.websocket.interfaces import (
    IChannelManager,
    IMessageRouter,
    ISessionManager,
    IWebSocketProvider,
    IWebSocketRuntime,
)
from backend.application.api.websocket.message_router import MessageRouter
from backend.application.api.websocket.models import (
    BroadcastPlan,
    ChannelState,
    ChannelSubscription,
    ConnectionContext,
    ConnectionState,
    WebSocketCapabilities,
    WebSocketChannel,
    WebSocketConnection,
    WebSocketDiagnostics,
    WebSocketHealth,
    WebSocketMessage,
    WebSocketRuntimeState,
    WebSocketSession,
    WebSocketStatistics,
)
from backend.application.api.websocket.runtime import (
    get_websocket_provider,
    get_websocket_runtime,
    reset_websocket_provider,
    reset_websocket_runtime,
    set_websocket_provider,
    set_websocket_runtime,
)
from backend.application.api.websocket.session_manager import SessionManager
from backend.application.api.websocket.websocket_provider import (
    WebSocketProvider,
)
from backend.application.api.websocket.websocket_runtime import (
    WebSocketRuntime,
)

__all__ = [
    # Models & Enums
    "ConnectionState",
    "ChannelState",
    "WebSocketRuntimeState",
    "WebSocketConnection",
    "WebSocketSession",
    "ChannelSubscription",
    "WebSocketChannel",
    "WebSocketMessage",
    "BroadcastPlan",
    "ConnectionContext",
    "WebSocketCapabilities",
    "WebSocketStatistics",
    "WebSocketHealth",
    "WebSocketDiagnostics",
    # Exceptions
    "WebSocketException",
    "ConnectionException",
    "ChannelException",
    "SubscriptionException",
    "MessageRoutingException",
    # Interfaces
    "ISessionManager",
    "IChannelManager",
    "IMessageRouter",
    "IWebSocketProvider",
    "IWebSocketRuntime",
    # Implementations
    "SessionManager",
    "ChannelManager",
    "MessageRouter",
    "WebSocketProvider",
    "WebSocketRuntime",
    # Runtime Helpers
    "get_websocket_runtime",
    "set_websocket_runtime",
    "reset_websocket_runtime",
    "get_websocket_provider",
    "set_websocket_provider",
    "reset_websocket_provider",
]
