"""API WebSocket Models (Phase 15.7).

Defines immutable Pydantic v2 domain models and enums for the provider-independent
API WebSocket Runtime, including sessions, connections, channels, subscriptions,
messages, broadcast plans, capabilities, health, statistics, and diagnostics.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional, Tuple

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


class ConnectionState(str, Enum):
    """Lifecycle states for a WebSocket connection."""

    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"
    CLOSED = "CLOSED"


class ChannelState(str, Enum):
    """Lifecycle states for a WebSocket channel."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ARCHIVED = "ARCHIVED"


class WebSocketRuntimeState(str, Enum):
    """Lifecycle states for the WebSocket runtime."""

    UNINITIALIZED = "UNINITIALIZED"
    INITIALIZING = "INITIALIZING"
    READY = "READY"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"


class WebSocketConnection(BaseModel):
    """Immutable representation of a single WebSocket connection."""

    model_config = ConfigDict(frozen=True)

    connection_id: str
    session_id: str
    state: ConnectionState = ConnectionState.CONNECTED
    client_ip: Optional[str] = None
    connected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WebSocketSession(BaseModel):
    """Immutable representation of a logical WebSocket user session holding connections."""

    model_config = ConfigDict(frozen=True)

    session_id: str
    user_id: Optional[str] = None
    connections: Tuple[WebSocketConnection, ...] = Field(default_factory=tuple)
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChannelSubscription(BaseModel):
    """Immutable record of a connection subscribing to a channel."""

    model_config = ConfigDict(frozen=True)

    subscription_id: str
    channel_id: str
    connection_id: str
    subscribed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WebSocketChannel(BaseModel):
    """Immutable representation of a publish-subscribe WebSocket channel."""

    model_config = ConfigDict(frozen=True)

    channel_id: str
    name: str
    state: ChannelState = ChannelState.ACTIVE
    subscriptions: Tuple[ChannelSubscription, ...] = Field(default_factory=tuple)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WebSocketMessage(BaseModel):
    """Immutable payload envelope for a WebSocket message."""

    model_config = ConfigDict(frozen=True)

    message_id: str
    sender_connection_id: Optional[str] = None
    target_channel_id: Optional[str] = None
    target_connection_id: Optional[str] = None
    event_type: str = "message"
    payload: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BroadcastPlan(BaseModel):
    """Immutable message routing execution plan declaring target recipient connections."""

    model_config = ConfigDict(frozen=True)

    plan_id: str
    message: WebSocketMessage
    target_connection_ids: Tuple[str, ...] = Field(default_factory=tuple)
    recipient_count: int = 0
    planned_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ConnectionContext(BaseModel):
    """Immutable context metadata for an active connection."""

    model_config = ConfigDict(frozen=True)

    context_id: str
    connection_id: str
    session_id: str
    attributes: Dict[str, Any] = Field(default_factory=dict)


class WebSocketCapabilities(BaseModel):
    """Immutable model declaring supported WebSocket runtime capabilities."""

    model_config = ConfigDict(frozen=True)

    supports_sessions: bool = True
    supports_channels: bool = True
    supports_channel_subscriptions: bool = True
    supports_broadcast_planning: bool = True
    supports_direct_routing: bool = True
    custom_capabilities: Dict[str, bool] = Field(default_factory=dict)


class WebSocketStatistics(BaseModel):
    """Immutable aggregate metrics and statistics for the WebSocket runtime."""

    model_config = ConfigDict(frozen=True)

    total_sessions: int = 0
    active_connections: int = 0
    total_channels: int = 0
    total_subscriptions: int = 0
    total_messages_routed: int = 0
    total_broadcast_plans: int = 0
    metrics: Dict[str, Any] = Field(default_factory=dict)


class WebSocketHealth(BaseModel):
    """Immutable health status evaluation of the WebSocket runtime."""

    model_config = ConfigDict(frozen=True)

    is_healthy: bool = True
    state: WebSocketRuntimeState = WebSocketRuntimeState.UNINITIALIZED
    details: Dict[str, Any] = Field(default_factory=dict)
    issues: Tuple[str, ...] = Field(default_factory=tuple)
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WebSocketDiagnostics(BaseModel):
    """Immutable diagnostic information for troubleshooting and telemetry."""

    model_config = ConfigDict(frozen=True)

    state: WebSocketRuntimeState = WebSocketRuntimeState.UNINITIALIZED
    active_sessions_count: int = 0
    active_connections_count: int = 0
    active_channels_count: int = 0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    thread_count: int = 0
    diagnostic_messages: Tuple[str, ...] = Field(default_factory=tuple)
    details: Dict[str, Any] = Field(default_factory=dict)
