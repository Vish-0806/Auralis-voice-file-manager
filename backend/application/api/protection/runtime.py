"""API Protection Global Runtime Helpers (Phase 15.8).

Provides thread-safe, lazy-initialized singleton accessors for global ProtectionRuntime
and ProtectionProvider instances.
"""

from threading import RLock
from typing import Optional

from backend.application.api.protection.interfaces import (
    IProtectionProvider,
    IProtectionRuntime,
)

_lock = RLock()
_global_protection_runtime: Optional[IProtectionRuntime] = None
_global_protection_provider: Optional[IProtectionProvider] = None


def get_protection_runtime() -> IProtectionRuntime:
    """Get or lazily initialize the global IProtectionRuntime singleton instance.

    Returns:
        IProtectionRuntime: Active global protection runtime instance.
    """
    global _global_protection_runtime
    with _lock:
        if _global_protection_runtime is None:
            from backend.application.api.protection.protection_runtime import (
                ProtectionRuntime,
            )

            _global_protection_runtime = ProtectionRuntime()
        return _global_protection_runtime


def set_protection_runtime(runtime: IProtectionRuntime) -> None:
    """Set the global IProtectionRuntime singleton instance.

    Args:
        runtime: Valid IProtectionRuntime implementation instance.
    """
    global _global_protection_runtime
    with _lock:
        _global_protection_runtime = runtime


def reset_protection_runtime() -> None:
    """Reset the global IProtectionRuntime singleton instance to None."""
    global _global_protection_runtime
    with _lock:
        _global_protection_runtime = None


def get_protection_provider() -> IProtectionProvider:
    """Get or lazily initialize the global IProtectionProvider singleton instance.

    Returns:
        IProtectionProvider: Active global protection provider instance.
    """
    global _global_protection_provider
    with _lock:
        if _global_protection_provider is None:
            from backend.application.api.protection.protection_provider import (
                ProtectionProvider,
            )

            _global_protection_provider = ProtectionProvider()
        return _global_protection_provider


def set_protection_provider(provider: IProtectionProvider) -> None:
    """Set the global IProtectionProvider singleton instance.

    Args:
        provider: Valid IProtectionProvider implementation instance.
    """
    global _global_protection_provider
    with _lock:
        _global_protection_provider = provider


def reset_protection_provider() -> None:
    """Reset the global IProtectionProvider singleton instance to None."""
    global _global_protection_provider
    with _lock:
        _global_protection_provider = None
