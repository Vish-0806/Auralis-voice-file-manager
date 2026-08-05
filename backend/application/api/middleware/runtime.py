"""API Middleware Global Runtime Helpers (Phase 15.3).

Provides thread-safe, lazy-initialized singleton accessors for global MiddlewareRuntime
and MiddlewareProvider instances.
"""

from threading import RLock
from typing import Optional

from backend.application.api.middleware.interfaces import (
    IMiddlewareProvider,
    IMiddlewareRuntime,
)

_lock = RLock()
_global_middleware_runtime: Optional[IMiddlewareRuntime] = None
_global_middleware_provider: Optional[IMiddlewareProvider] = None


def get_middleware_runtime() -> IMiddlewareRuntime:
    """Get or lazily initialize the global IMiddlewareRuntime singleton instance.

    Returns:
        IMiddlewareRuntime: Active global middleware runtime instance.
    """
    global _global_middleware_runtime
    with _lock:
        if _global_middleware_runtime is None:
            from backend.application.api.middleware.middleware_runtime import (
                MiddlewareRuntime,
            )

            _global_middleware_runtime = MiddlewareRuntime()
        return _global_middleware_runtime


def set_middleware_runtime(runtime: IMiddlewareRuntime) -> None:
    """Set the global IMiddlewareRuntime singleton instance.

    Args:
        runtime: Valid IMiddlewareRuntime implementation instance.
    """
    global _global_middleware_runtime
    with _lock:
        _global_middleware_runtime = runtime


def reset_middleware_runtime() -> None:
    """Reset the global IMiddlewareRuntime singleton instance to None."""
    global _global_middleware_runtime
    with _lock:
        _global_middleware_runtime = None


def get_middleware_provider() -> IMiddlewareProvider:
    """Get or lazily initialize the global IMiddlewareProvider singleton instance.

    Returns:
        IMiddlewareProvider: Active global middleware provider instance.
    """
    global _global_middleware_provider
    with _lock:
        if _global_middleware_provider is None:
            from backend.application.api.middleware.middleware_provider import (
                MiddlewareProvider,
            )

            _global_middleware_provider = MiddlewareProvider()
        return _global_middleware_provider


def set_middleware_provider(provider: IMiddlewareProvider) -> None:
    """Set the global IMiddlewareProvider singleton instance.

    Args:
        provider: Valid IMiddlewareProvider implementation instance.
    """
    global _global_middleware_provider
    with _lock:
        _global_middleware_provider = provider


def reset_middleware_provider() -> None:
    """Reset the global IMiddlewareProvider singleton instance to None."""
    global _global_middleware_provider
    with _lock:
        _global_middleware_provider = None
