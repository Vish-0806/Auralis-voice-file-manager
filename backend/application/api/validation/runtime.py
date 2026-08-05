"""API Validation Global Runtime Helpers (Phase 15.5).

Provides thread-safe, lazy-initialized singleton accessors for global ValidationRuntime
and ValidationProvider instances.
"""

from threading import RLock
from typing import Optional

from backend.application.api.validation.interfaces import (
    IValidationProvider,
    IValidationRuntime,
)

_lock = RLock()
_global_validation_runtime: Optional[IValidationRuntime] = None
_global_validation_provider: Optional[IValidationProvider] = None


def get_validation_runtime() -> IValidationRuntime:
    """Get or lazily initialize the global IValidationRuntime singleton instance.

    Returns:
        IValidationRuntime: Active global validation runtime instance.
    """
    global _global_validation_runtime
    with _lock:
        if _global_validation_runtime is None:
            from backend.application.api.validation.validation_runtime import (
                ValidationRuntime,
            )

            _global_validation_runtime = ValidationRuntime()
        return _global_validation_runtime


def set_validation_runtime(runtime: IValidationRuntime) -> None:
    """Set the global IValidationRuntime singleton instance.

    Args:
        runtime: Valid IValidationRuntime implementation instance.
    """
    global _global_validation_runtime
    with _lock:
        _global_validation_runtime = runtime


def reset_validation_runtime() -> None:
    """Reset the global IValidationRuntime singleton instance to None."""
    global _global_validation_runtime
    with _lock:
        _global_validation_runtime = None


def get_validation_provider() -> IValidationProvider:
    """Get or lazily initialize the global IValidationProvider singleton instance.

    Returns:
        IValidationProvider: Active global validation provider instance.
    """
    global _global_validation_provider
    with _lock:
        if _global_validation_provider is None:
            from backend.application.api.validation.validation_provider import (
                ValidationProvider,
            )

            _global_validation_provider = ValidationProvider()
        return _global_validation_provider


def set_validation_provider(provider: IValidationProvider) -> None:
    """Set the global IValidationProvider singleton instance.

    Args:
        provider: Valid IValidationProvider implementation instance.
    """
    global _global_validation_provider
    with _lock:
        _global_validation_provider = provider


def reset_validation_provider() -> None:
    """Reset the global IValidationProvider singleton instance to None."""
    global _global_validation_provider
    with _lock:
        _global_validation_provider = None
