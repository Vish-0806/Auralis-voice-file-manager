"""API WebSocket Channel Manager Implementation (Phase 15.7).

Thread-safe channel manager managing publish-subscribe channels and connection subscriptions
without network or socket dependencies.
"""

import logging
from threading import RLock
from typing import Dict, Optional, Tuple
import uuid

from backend.application.api.websocket.exceptions import ChannelException
from backend.application.api.websocket.interfaces import IChannelManager
from backend.application.api.websocket.models import (
    ChannelSubscription,
    WebSocketChannel,
)

logger = logging.getLogger(__name__)


class ChannelManager(IChannelManager):
    """Thread-safe channel manager managing pub-sub channels and connection subscriptions."""

    def __init__(self) -> None:
        """Initialize ChannelManager using Constructor Dependency Injection."""
        self._lock = RLock()
        self._channels: Dict[str, WebSocketChannel] = {}

        self._total_channels_registered = 0
        self._total_subscriptions = 0
        self._total_unsubscriptions = 0

    def register_channel(self, channel: WebSocketChannel) -> WebSocketChannel:
        """Register a new publish-subscribe WebSocket channel.

        Args:
            channel: Immutable WebSocketChannel instance.

        Returns:
            WebSocketChannel: Registered channel model.

        Raises:
            ChannelException: If channel_id is already registered.
        """
        with self._lock:
            if channel.channel_id in self._channels:
                raise ChannelException(
                    f"WebSocket channel with ID '{channel.channel_id}' is already registered."
                )

            self._channels[channel.channel_id] = channel
            self._total_channels_registered += 1
            logger.info("Registered WebSocket channel ID '%s' (%s).", channel.channel_id, channel.name)
            return channel

    def unregister_channel(self, channel_id: str) -> Optional[WebSocketChannel]:
        """Unregister a channel by channel ID.

        Args:
            channel_id: Unique channel identifier.

        Returns:
            Optional[WebSocketChannel]: Removed channel if found, else None.
        """
        with self._lock:
            channel = self._channels.pop(channel_id, None)
            if channel is not None:
                logger.info("Unregistered WebSocket channel ID '%s'.", channel_id)
            return channel

    def lookup_channel(self, channel_id: str) -> Optional[WebSocketChannel]:
        """Look up a channel by channel ID.

        Args:
            channel_id: Unique channel identifier.

        Returns:
            Optional[WebSocketChannel]: Channel if found, else None.
        """
        with self._lock:
            return self._channels.get(channel_id)

    def subscribe(self, channel_id: str, connection_id: str) -> ChannelSubscription:
        """Subscribe a connection to a channel.

        Args:
            channel_id: Target channel ID.
            connection_id: Target connection ID.

        Returns:
            ChannelSubscription: Created subscription record.

        Raises:
            ChannelException: If channel_id is not registered.
        """
        with self._lock:
            channel = self._channels.get(channel_id)
            if channel is None:
                raise ChannelException(
                    f"Target channel ID '{channel_id}' not found for subscription."
                )

            # Check existing subscription
            for sub in channel.subscriptions:
                if sub.connection_id == connection_id:
                    return sub

            sub_id = f"sub_{uuid.uuid4().hex[:8]}"
            subscription = ChannelSubscription(
                subscription_id=sub_id,
                channel_id=channel_id,
                connection_id=connection_id,
            )

            updated_subs = channel.subscriptions + (subscription,)
            self._channels[channel_id] = WebSocketChannel(
                channel_id=channel.channel_id,
                name=channel.name,
                state=channel.state,
                subscriptions=updated_subs,
                metadata=channel.metadata,
            )
            self._total_subscriptions += 1
            logger.info("Subscribed connection ID '%s' to channel ID '%s'.", connection_id, channel_id)
            return subscription

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
        with self._lock:
            channel = self._channels.get(channel_id)
            if channel is None:
                return None

            target_sub: Optional[ChannelSubscription] = None
            remaining_subs = []
            for sub in channel.subscriptions:
                if sub.connection_id == connection_id:
                    target_sub = sub
                else:
                    remaining_subs.append(sub)

            if target_sub is not None:
                self._channels[channel_id] = WebSocketChannel(
                    channel_id=channel.channel_id,
                    name=channel.name,
                    state=channel.state,
                    subscriptions=tuple(remaining_subs),
                    metadata=channel.metadata,
                )
                self._total_unsubscriptions += 1
                logger.info("Unsubscribed connection ID '%s' from channel ID '%s'.", connection_id, channel_id)

            return target_sub

    def get_channel_subscribers(self, channel_id: str) -> Tuple[str, ...]:
        """Get connection IDs subscribed to a channel.

        Args:
            channel_id: Unique channel identifier.

        Returns:
            Tuple[str, ...]: Immutable tuple of subscribed connection IDs.
        """
        with self._lock:
            channel = self._channels.get(channel_id)
            if channel is None:
                return ()
            return tuple(sub.connection_id for sub in channel.subscriptions)

    def list_channels(self) -> Tuple[WebSocketChannel, ...]:
        """List all registered channels.

        Returns:
            Tuple[WebSocketChannel, ...]: Immutable tuple of channels.
        """
        with self._lock:
            return tuple(self._channels.values())

    def count_channels(self) -> int:
        """Get total count of registered channels.

        Returns:
            int: Channel count.
        """
        with self._lock:
            return len(self._channels)

    def clear(self) -> None:
        """Clear all channels and subscriptions from the manager."""
        with self._lock:
            self._channels.clear()
            logger.info("ChannelManager cleared.")

    def get_channel_telemetry(self) -> Dict[str, int]:
        """Get internal channel telemetry counters under lock."""
        with self._lock:
            total_subs_current = sum(len(c.subscriptions) for c in self._channels.values())
            return {
                "total_channels_registered": self._total_channels_registered,
                "total_subscriptions": self._total_subscriptions,
                "total_unsubscriptions": self._total_unsubscriptions,
                "active_channels_count": len(self._channels),
                "current_subscriptions_count": total_subs_current,
            }
