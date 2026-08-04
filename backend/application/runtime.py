"""Application Global Runtime Helpers (Phase 14.1).

Provides thread-safe accessors for global ApplicationRuntime and ApplicationProvider
instances. Ensures controlled singleton access without Service Locator or global state side-effects.
"""

from threading import RLock
from typing import Optional

from backend.application.exceptions import ApplicationBootstrapError
from backend.application.interfaces import IApplicationProvider, IApplicationRuntime

_lock = RLock()
_global_application_runtime: Optional[IApplicationRuntime] = None
_global_application_provider: Optional[IApplicationProvider] = None


def get_application_runtime() -> IApplicationRuntime:
    """Get the global IApplicationRuntime singleton instance.

    Returns:
        IApplicationRuntime: Active global application runtime instance.

    Raises:
        ApplicationBootstrapError: If global runtime instance has not been configured.
    """
    with _lock:
        if _global_application_runtime is None:
            raise ApplicationBootstrapError(
                "Global ApplicationRuntime has not been set. "
                "Initialize and set runtime via set_application_runtime() first."
            )
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
    """Get the global IApplicationProvider singleton instance.

    Returns:
        IApplicationProvider: Active global application provider instance.

    Raises:
        ApplicationBootstrapError: If global provider instance has not been configured.
    """
    with _lock:
        if _global_application_provider is None:
            raise ApplicationBootstrapError(
                "Global ApplicationProvider has not been set. "
                "Initialize and set provider via set_application_provider() first."
            )
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
