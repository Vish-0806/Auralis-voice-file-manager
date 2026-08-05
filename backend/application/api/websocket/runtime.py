"""API WebSocket Global Runtime Helpers (Phase 15.7).

Provides thread-safe, lazy-initialized singleton accessors for global WebSocketRuntime
and WebSocketProvider instances.
"""

from threading import RLock
from typing import Optional

from backend.application.api.websocket.interfaces import (
    IWebSocketProvider,
    IWebSocketRuntime,
)

_lock = RLock()
_global_websocket_runtime: Optional[IWebSocketRuntime] = None
_global_websocket_provider: Optional[IWebSocketProvider] = None


def get_websocket_runtime() -> IWebSocketRuntime:
    """Get or lazily initialize the global IWebSocketRuntime singleton instance.

    Returns:
        IWebSocketRuntime: Active global WebSocket runtime instance.
    """
    global _global_websocket_runtime
    with _lock:
        if _global_websocket_runtime is None:
            from backend.application.api.websocket.websocket_runtime import (
                WebSocketRuntime,
            )

            _global_websocket_runtime = WebSocketRuntime()
        return _global_websocket_runtime


def set_websocket_runtime(runtime: IWebSocketRuntime) -> None:
    """Set the global IWebSocketRuntime singleton instance.

    Args:
        runtime: Valid IWebSocketRuntime implementation instance.
    """
    global _global_websocket_runtime
    with _lock:
        _global_websocket_runtime = runtime


def reset_websocket_runtime() -> None:
    """Reset the global IWebSocketRuntime singleton instance to None."""
    global _global_websocket_runtime
    with _lock:
        _global_websocket_runtime = None


def get_websocket_provider() -> IWebSocketProvider:
    """Get or lazily initialize the global IWebSocketProvider singleton instance.

    Returns:
        IWebSocketProvider: Active global WebSocket provider instance.
    """
    global _global_websocket_provider
    with _lock:
        if _global_websocket_provider is None:
            from backend.application.api.websocket.websocket_provider import (
                WebSocketProvider,
            )

            _global_websocket_provider = WebSocketProvider()
        return _global_websocket_provider


def set_websocket_provider(provider: IWebSocketProvider) -> None:
    """Set the global IWebSocketProvider singleton instance.

    Args:
        provider: Valid IWebSocketProvider implementation instance.
    """
    global _global_websocket_provider
    with _lock:
        _global_websocket_provider = provider


def reset_websocket_provider() -> None:
    """Reset the global IWebSocketProvider singleton instance to None."""
    global _global_websocket_provider
    with _lock:
        _global_websocket_provider = None
