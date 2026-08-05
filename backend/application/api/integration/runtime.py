"""API Integration Global Runtime Helpers (Phase 15.9).

Provides thread-safe, lazy-initialized singleton accessors for global IntegrationRuntime
and IntegrationProvider instances.
"""

from threading import RLock
from typing import Optional

from backend.application.api.integration.interfaces import (
    IIntegrationProvider,
    IIntegrationRuntime,
)

_lock = RLock()
_global_integration_runtime: Optional[IIntegrationRuntime] = None
_global_integration_provider: Optional[IIntegrationProvider] = None


def get_integration_runtime() -> IIntegrationRuntime:
    """Get or lazily initialize the global IIntegrationRuntime singleton instance.

    Returns:
        IIntegrationRuntime: Active global integration runtime instance.
    """
    global _global_integration_runtime
    with _lock:
        if _global_integration_runtime is None:
            from backend.application.api.integration.integration_runtime import (
                IntegrationRuntime,
            )

            _global_integration_runtime = IntegrationRuntime()
        return _global_integration_runtime


def set_integration_runtime(runtime: IIntegrationRuntime) -> None:
    """Set the global IIntegrationRuntime singleton instance.

    Args:
        runtime: Valid IIntegrationRuntime implementation instance.
    """
    global _global_integration_runtime
    with _lock:
        _global_integration_runtime = runtime


def reset_integration_runtime() -> None:
    """Reset the global IIntegrationRuntime singleton instance to None."""
    global _global_integration_runtime
    with _lock:
        _global_integration_runtime = None


def get_integration_provider() -> IIntegrationProvider:
    """Get or lazily initialize the global IIntegrationProvider singleton instance.

    Returns:
        IIntegrationProvider: Active global integration provider instance.
    """
    global _global_integration_provider
    with _lock:
        if _global_integration_provider is None:
            from backend.application.api.integration.integration_provider import (
                IntegrationProvider,
            )

            _global_integration_provider = IntegrationProvider()
        return _global_integration_provider


def set_integration_provider(provider: IIntegrationProvider) -> None:
    """Set the global IIntegrationProvider singleton instance.

    Args:
        provider: Valid IIntegrationProvider implementation instance.
    """
    global _global_integration_provider
    with _lock:
        _global_integration_provider = provider


def reset_integration_provider() -> None:
    """Reset the global IIntegrationProvider singleton instance to None."""
    global _global_integration_provider
    with _lock:
        _global_integration_provider = None
