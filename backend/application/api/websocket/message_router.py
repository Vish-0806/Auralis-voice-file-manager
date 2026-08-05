"""API WebSocket Message Router Implementation (Phase 15.7).

Thread-safe message router evaluating direct message destinations and channel subscriptions
to produce deterministic BroadcastPlan models without networking or socket transport overhead.
"""

from datetime import datetime, timezone
import logging
from threading import RLock
from typing import Dict, Optional, Tuple
import uuid

from backend.application.api.websocket.interfaces import (
    IChannelManager,
    IMessageRouter,
    ISessionManager,
)
from backend.application.api.websocket.models import (
    BroadcastPlan,
    WebSocketMessage,
)

logger = logging.getLogger(__name__)


class MessageRouter(IMessageRouter):
    """Thread-safe deterministic message router constructing BroadcastPlan models."""

    def __init__(
        self,
        session_manager: Optional[ISessionManager] = None,
        channel_manager: Optional[IChannelManager] = None,
    ) -> None:
        """Initialize MessageRouter using Constructor Dependency Injection.

        Args:
            session_manager: Optional ISessionManager implementation instance.
            channel_manager: Optional IChannelManager implementation instance.
        """
        self._lock = RLock()
        self._session_manager = session_manager
        self._channel_manager = channel_manager

        self._total_routed_messages = 0
        self._total_broadcast_plans = 0

    def route_direct(self, message: WebSocketMessage) -> BroadcastPlan:
        """Create a BroadcastPlan for a direct point-to-point message.

        Args:
            message: WebSocketMessage containing target_connection_id.

        Returns:
            BroadcastPlan: Immutable routing plan.
        """
        with self._lock:
            self._total_routed_messages += 1
            self._total_broadcast_plans += 1

            target_id = message.target_connection_id
            targets: Tuple[str, ...] = ()
            if target_id is not None:
                targets = (target_id,)

            plan_id = f"plan_{uuid.uuid4().hex[:8]}"
            logger.info("Routed direct message '%s' to connection '%s'.", message.message_id, target_id)
            return BroadcastPlan(
                plan_id=plan_id,
                message=message,
                target_connection_ids=targets,
                recipient_count=len(targets),
                planned_at=datetime.now(timezone.utc),
            )

    def route_channel(self, message: WebSocketMessage) -> BroadcastPlan:
        """Create a BroadcastPlan for a channel broadcast message.

        Args:
            message: WebSocketMessage containing target_channel_id.

        Returns:
            BroadcastPlan: Immutable routing plan.
        """
        with self._lock:
            self._total_routed_messages += 1
            self._total_broadcast_plans += 1

            channel_id = message.target_channel_id
            subscribers: Tuple[str, ...] = ()

            if channel_id is not None and self._channel_manager is not None:
                subscribers = self._channel_manager.get_channel_subscribers(channel_id)

            plan_id = f"plan_{uuid.uuid4().hex[:8]}"
            logger.info(
                "Routed channel message '%s' to channel '%s' (%d subscribers).",
                message.message_id,
                channel_id,
                len(subscribers),
            )
            return BroadcastPlan(
                plan_id=plan_id,
                message=message,
                target_connection_ids=subscribers,
                recipient_count=len(subscribers),
                planned_at=datetime.now(timezone.utc),
            )

    def plan_broadcast(
        self, message: WebSocketMessage, target_connection_ids: Tuple[str, ...]
    ) -> BroadcastPlan:
        """Create an explicit BroadcastPlan targeting given connection IDs.

        Args:
            message: Target WebSocketMessage instance.
            target_connection_ids: Tuple of recipient connection IDs.

        Returns:
            BroadcastPlan: Immutable routing plan.
        """
        with self._lock:
            self._total_routed_messages += 1
            self._total_broadcast_plans += 1

            plan_id = f"plan_{uuid.uuid4().hex[:8]}"
            logger.info(
                "Planned explicit broadcast message '%s' to %d recipients.",
                message.message_id,
                len(target_connection_ids),
            )
            return BroadcastPlan(
                plan_id=plan_id,
                message=message,
                target_connection_ids=target_connection_ids,
                recipient_count=len(target_connection_ids),
                planned_at=datetime.now(timezone.utc),
            )

    def count_routed_messages(self) -> int:
        """Get total count of routed messages.

        Returns:
            int: Message count.
        """
        with self._lock:
            return self._total_routed_messages

    def get_router_telemetry(self) -> Dict[str, int]:
        """Get internal router telemetry counters under lock."""
        with self._lock:
            return {
                "total_routed_messages": self._total_routed_messages,
                "total_broadcast_plans": self._total_broadcast_plans,
            }
