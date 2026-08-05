"""API Global Runtime Helpers (Phase 15.1).

Provides thread-safe, lazy-initialized singleton accessors for global ApiRuntime
and ApiProvider instances.
"""

from threading import RLock
from typing import Optional

from backend.application.api.interfaces import IApiProvider, IApiRuntime

_lock = RLock()
_global_api_runtime: Optional[IApiRuntime] = None
_global_api_provider: Optional[IApiProvider] = None


def get_api_runtime() -> IApiRuntime:
    """Get or lazily initialize the global IApiRuntime singleton instance.

    Returns:
        IApiRuntime: Active global API runtime instance.
    """
    global _global_api_runtime
    with _lock:
        if _global_api_runtime is None:
            from backend.application.api.api_runtime import ApiRuntime

            _global_api_runtime = ApiRuntime()
        return _global_api_runtime


def set_api_runtime(runtime: IApiRuntime) -> None:
    """Set the global IApiRuntime singleton instance.

    Args:
        runtime: Valid IApiRuntime implementation instance.
    """
    global _global_api_runtime
    with _lock:
        _global_api_runtime = runtime


def reset_api_runtime() -> None:
    """Reset the global IApiRuntime singleton instance to None."""
    global _global_api_runtime
    with _lock:
        _global_api_runtime = None


def get_api_provider() -> IApiProvider:
    """Get or lazily initialize the global IApiProvider singleton instance.

    Returns:
        IApiProvider: Active global API provider instance.
    """
    global _global_api_provider
    with _lock:
        if _global_api_provider is None:
            from backend.application.api.api_provider import ApiProvider

            _global_api_provider = ApiProvider()
        return _global_api_provider


def set_api_provider(provider: IApiProvider) -> None:
    """Set the global IApiProvider singleton instance.

    Args:
        provider: Valid IApiProvider implementation instance.
    """
    global _global_api_provider
    with _lock:
        _global_api_provider = provider


def reset_api_provider() -> None:
    """Reset the global IApiProvider singleton instance to None."""
    global _global_api_provider
    with _lock:
        _global_api_provider = None
