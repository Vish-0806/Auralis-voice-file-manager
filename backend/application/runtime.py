"""Application Global Runtime Helpers (Phase 14.1).

Provides thread-safe, lazy-initialized singleton accessors for global ApplicationRuntime
and ApplicationProvider instances.
"""

from threading import RLock
from typing import Optional

from backend.application.interfaces import IApplicationProvider, IApplicationRuntime

_lock = RLock()
_global_application_runtime: Optional[IApplicationRuntime] = None
_global_application_provider: Optional[IApplicationProvider] = None


def get_application_runtime() -> IApplicationRuntime:
    """Get or lazily initialize the global IApplicationRuntime singleton instance.

    Returns:
        IApplicationRuntime: Active global application runtime instance.
    """
    global _global_application_runtime
    with _lock:
        if _global_application_runtime is None:
            from backend.application.application_runtime import ApplicationRuntime

            _global_application_runtime = ApplicationRuntime()
        return _global_application_runtime


def set_application_runtime(runtime: IApplicationRuntime) -> None:
    """Set the global IApplicationRuntime singleton instance.

    Args:
        runtime: Valid IApplicationRuntime implementation instance.
    """
    global _global_application_runtime
    with _lock:
        _global_application_runtime = runtime


def reset_application_runtime() -> None:
    """Reset the global IApplicationRuntime singleton instance to None."""
    global _global_application_runtime
    with _lock:
        _global_application_runtime = None


def get_application_provider() -> IApplicationProvider:
    """Get or lazily initialize the global IApplicationProvider singleton instance.

    Returns:
        IApplicationProvider: Active global application provider instance.
    """
    global _global_application_provider
    with _lock:
        if _global_application_provider is None:
            from backend.application.application_provider import ApplicationProvider

            _global_application_provider = ApplicationProvider()
        return _global_application_provider


def set_application_provider(provider: IApplicationProvider) -> None:
    """Set the global IApplicationProvider singleton instance.

    Args:
        provider: Valid IApplicationProvider implementation instance.
    """
    global _global_application_provider
    with _lock:
        _global_application_provider = provider


def reset_application_provider() -> None:
    """Reset the global IApplicationProvider singleton instance to None."""
    global _global_application_provider
    with _lock:
        _global_application_provider = None
