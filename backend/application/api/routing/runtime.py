"""API Request Routing Global Runtime Helpers (Phase 15.2).

Provides thread-safe, lazy-initialized singleton accessors for global RoutingRuntime
and RoutingProvider instances.
"""

from threading import RLock
from typing import Optional

from backend.application.api.routing.interfaces import (
    IRoutingProvider,
    IRoutingRuntime,
)

_lock = RLock()
_global_routing_runtime: Optional[IRoutingRuntime] = None
_global_routing_provider: Optional[IRoutingProvider] = None


def get_routing_runtime() -> IRoutingRuntime:
    """Get or lazily initialize the global IRoutingRuntime singleton instance.

    Returns:
        IRoutingRuntime: Active global routing runtime instance.
    """
    global _global_routing_runtime
    with _lock:
        if _global_routing_runtime is None:
            from backend.application.api.routing.routing_runtime import RoutingRuntime

            _global_routing_runtime = RoutingRuntime()
        return _global_routing_runtime


def set_routing_runtime(runtime: IRoutingRuntime) -> None:
    """Set the global IRoutingRuntime singleton instance.

    Args:
        runtime: Valid IRoutingRuntime implementation instance.
    """
    global _global_routing_runtime
    with _lock:
        _global_routing_runtime = runtime


def reset_routing_runtime() -> None:
    """Reset the global IRoutingRuntime singleton instance to None."""
    global _global_routing_runtime
    with _lock:
        _global_routing_runtime = None


def get_routing_provider() -> IRoutingProvider:
    """Get or lazily initialize the global IRoutingProvider singleton instance.

    Returns:
        IRoutingProvider: Active global routing provider instance.
    """
    global _global_routing_provider
    with _lock:
        if _global_routing_provider is None:
            from backend.application.api.routing.routing_provider import (
                RoutingProvider,
            )

            _global_routing_provider = RoutingProvider()
        return _global_routing_provider


def set_routing_provider(provider: IRoutingProvider) -> None:
    """Set the global IRoutingProvider singleton instance.

    Args:
        provider: Valid IRoutingProvider implementation instance.
    """
    global _global_routing_provider
    with _lock:
        _global_routing_provider = provider


def reset_routing_provider() -> None:
    """Reset the global IRoutingProvider singleton instance to None."""
    global _global_routing_provider
    with _lock:
        _global_routing_provider = None
