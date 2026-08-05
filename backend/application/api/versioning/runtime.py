"""API Versioning Global Runtime Helpers (Phase 15.6).

Provides thread-safe, lazy-initialized singleton accessors for global VersioningRuntime
and VersioningProvider instances.
"""

from threading import RLock
from typing import Optional

from backend.application.api.versioning.interfaces import (
    IVersioningProvider,
    IVersioningRuntime,
)

_lock = RLock()
_global_versioning_runtime: Optional[IVersioningRuntime] = None
_global_versioning_provider: Optional[IVersioningProvider] = None


def get_versioning_runtime() -> IVersioningRuntime:
    """Get or lazily initialize the global IVersioningRuntime singleton instance.

    Returns:
        IVersioningRuntime: Active global versioning runtime instance.
    """
    global _global_versioning_runtime
    with _lock:
        if _global_versioning_runtime is None:
            from backend.application.api.versioning.versioning_runtime import (
                VersioningRuntime,
            )

            _global_versioning_runtime = VersioningRuntime()
        return _global_versioning_runtime


def set_versioning_runtime(runtime: IVersioningRuntime) -> None:
    """Set the global IVersioningRuntime singleton instance.

    Args:
        runtime: Valid IVersioningRuntime implementation instance.
    """
    global _global_versioning_runtime
    with _lock:
        _global_versioning_runtime = runtime


def reset_versioning_runtime() -> None:
    """Reset the global IVersioningRuntime singleton instance to None."""
    global _global_versioning_runtime
    with _lock:
        _global_versioning_runtime = None


def get_versioning_provider() -> IVersioningProvider:
    """Get or lazily initialize the global IVersioningProvider singleton instance.

    Returns:
        IVersioningProvider: Active global versioning provider instance.
    """
    global _global_versioning_provider
    with _lock:
        if _global_versioning_provider is None:
            from backend.application.api.versioning.versioning_provider import (
                VersioningProvider,
            )

            _global_versioning_provider = VersioningProvider()
        return _global_versioning_provider


def set_versioning_provider(provider: IVersioningProvider) -> None:
    """Set the global IVersioningProvider singleton instance.

    Args:
        provider: Valid IVersioningProvider implementation instance.
    """
    global _global_versioning_provider
    with _lock:
        _global_versioning_provider = provider


def reset_versioning_provider() -> None:
    """Reset the global IVersioningProvider singleton instance to None."""
    global _global_versioning_provider
    with _lock:
        _global_versioning_provider = None
