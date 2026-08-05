"""API Authentication Global Runtime Helpers (Phase 15.4).

Provides thread-safe, lazy-initialized singleton accessors for global AuthenticationRuntime
and AuthenticationProvider instances.
"""

from threading import RLock
from typing import Optional

from backend.application.api.auth.interfaces import (
    IAuthenticationProvider,
    IAuthenticationRuntime,
)

_lock = RLock()
_global_authentication_runtime: Optional[IAuthenticationRuntime] = None
_global_authentication_provider: Optional[IAuthenticationProvider] = None


def get_authentication_runtime() -> IAuthenticationRuntime:
    """Get or lazily initialize the global IAuthenticationRuntime singleton instance.

    Returns:
        IAuthenticationRuntime: Active global authentication runtime instance.
    """
    global _global_authentication_runtime
    with _lock:
        if _global_authentication_runtime is None:
            from backend.application.api.auth.authentication_runtime import (
                AuthenticationRuntime,
            )

            _global_authentication_runtime = AuthenticationRuntime()
        return _global_authentication_runtime


def set_authentication_runtime(runtime: IAuthenticationRuntime) -> None:
    """Set the global IAuthenticationRuntime singleton instance.

    Args:
        runtime: Valid IAuthenticationRuntime implementation instance.
    """
    global _global_authentication_runtime
    with _lock:
        _global_authentication_runtime = runtime


def reset_authentication_runtime() -> None:
    """Reset the global IAuthenticationRuntime singleton instance to None."""
    global _global_authentication_runtime
    with _lock:
        _global_authentication_runtime = None


def get_authentication_provider() -> IAuthenticationProvider:
    """Get or lazily initialize the global IAuthenticationProvider singleton instance.

    Returns:
        IAuthenticationProvider: Active global authentication provider instance.
    """
    global _global_authentication_provider
    with _lock:
        if _global_authentication_provider is None:
            from backend.application.api.auth.authentication_provider import (
                AuthenticationProvider,
            )

            _global_authentication_provider = AuthenticationProvider()
        return _global_authentication_provider


def set_authentication_provider(provider: IAuthenticationProvider) -> None:
    """Set the global IAuthenticationProvider singleton instance.

    Args:
        provider: Valid IAuthenticationProvider implementation instance.
    """
    global _global_authentication_provider
    with _lock:
        _global_authentication_provider = provider


def reset_authentication_provider() -> None:
    """Reset the global IAuthenticationProvider singleton instance to None."""
    global _global_authentication_provider
    with _lock:
        _global_authentication_provider = None
