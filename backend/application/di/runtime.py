"""Dependency Injection Global Runtime Helpers (Phase 14.2.1).

Provides thread-safe, lazy-initialized singleton accessors for global DependencyContainer
and ServiceProvider instances.
"""

from threading import RLock
from typing import Optional

from backend.application.di.interfaces import IDependencyContainer, IServiceProvider

_lock = RLock()
_global_dependency_container: Optional[IDependencyContainer] = None
_global_service_provider: Optional[IServiceProvider] = None


def get_dependency_container() -> IDependencyContainer:
    """Get or lazily initialize the global IDependencyContainer singleton instance.

    Returns:
        IDependencyContainer: Active global dependency container instance.
    """
    global _global_dependency_container
    with _lock:
        if _global_dependency_container is None:
            from backend.application.di.dependency_container import DependencyContainer

            _global_dependency_container = DependencyContainer()
        return _global_dependency_container


def set_dependency_container(container: IDependencyContainer) -> None:
    """Set the global IDependencyContainer singleton instance.

    Args:
        container: Valid IDependencyContainer instance.
    """
    global _global_dependency_container
    with _lock:
        _global_dependency_container = container


def reset_dependency_container() -> None:
    """Reset the global IDependencyContainer singleton instance to None."""
    global _global_dependency_container
    with _lock:
        _global_dependency_container = None


def get_service_provider() -> IServiceProvider:
    """Get or lazily initialize the global IServiceProvider singleton instance.

    Returns:
        IServiceProvider: Active global service provider instance.
    """
    global _global_service_provider
    with _lock:
        if _global_service_provider is None:
            container = get_dependency_container()
            if hasattr(container, "provider"):
                _global_service_provider = container.provider  # type: ignore[attr-defined]
            else:
                from backend.application.di.service_provider import ServiceProvider

                _global_service_provider = ServiceProvider()
        return _global_service_provider


def set_service_provider(provider: IServiceProvider) -> None:
    """Set the global IServiceProvider singleton instance.

    Args:
        provider: Valid IServiceProvider instance.
    """
    global _global_service_provider
    with _lock:
        _global_service_provider = provider


def reset_service_provider() -> None:
    """Reset the global IServiceProvider singleton instance to None."""
    global _global_service_provider
    with _lock:
        _global_service_provider = None
