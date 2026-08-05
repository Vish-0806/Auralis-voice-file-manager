"""API WebSocket Exceptions (Phase 15.7).

Defines the exception hierarchy for WebSocket session management, connections,
channels, subscriptions, and message routing operations.
"""


class WebSocketException(Exception):
    """Base exception for all WebSocket runtime errors."""

    pass


class ConnectionException(WebSocketException):
    """Raised when connection lookup, registration, or state modification fails."""

    pass


class ChannelException(WebSocketException):
    """Raised when channel registration, lookup, or state modification fails."""

    pass


class SubscriptionException(WebSocketException):
    """Raised when subscribing or unsubscribing from a channel fails."""

    pass


class MessageRoutingException(WebSocketException):
    """Raised when message routing or broadcast planning fails."""

    pass
