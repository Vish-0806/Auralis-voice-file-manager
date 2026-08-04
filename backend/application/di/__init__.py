"""Dependency Injection Subsystem (Phase 14.2.1).

Package representing the Dependency Injection Container Foundation for the Auralis application.
Exposes domain models, exceptions, ABC interfaces, service descriptors, collections, providers,
containers, and global thread-safe accessors.
"""

from backend.application.di.dependency_container import DependencyContainer
from backend.application.di.exceptions import (
    CircularDependencyException,
    DependencyInjectionException,
    ServiceRegistrationException,
    ServiceResolutionException,
    ServiceValidationException,
)
from backend.application.di.interfaces import (
    IDependencyContainer,
    IServiceCollection,
    IServiceDescriptor,
    IServiceProvider,
)
from backend.application.di.models import (
    ContainerCapabilities,
    ContainerConfiguration,
    ContainerContext,
    ContainerHealth,
    ContainerState,
    ContainerStatistics,
    DependencyGraphNode,
    ServiceDescriptorModel,
    ServiceLifetime,
    ServiceRegistration,
)
from backend.application.di.runtime import (
    get_dependency_container,
    get_service_provider,
    reset_dependency_container,
    reset_service_provider,
    set_dependency_container,
    set_service_provider,
)
from backend.application.di.service_collection import ServiceCollection
from backend.application.di.service_descriptor import ServiceDescriptor
from backend.application.di.service_provider import ServiceProvider

__all__ = [
    # Models & Enums
    "ServiceLifetime",
    "ContainerState",
    "ServiceDescriptorModel",
    "ServiceRegistration",
    "DependencyGraphNode",
    "ContainerCapabilities",
    "ContainerStatistics",
    "ContainerHealth",
    "ContainerConfiguration",
    "ContainerContext",
    # Exceptions
    "DependencyInjectionException",
    "ServiceRegistrationException",
    "ServiceResolutionException",
    "CircularDependencyException",
    "ServiceValidationException",
    # Interfaces
    "IServiceDescriptor",
    "IServiceCollection",
    "IServiceProvider",
    "IDependencyContainer",
    # Implementations
    "ServiceDescriptor",
    "ServiceCollection",
    "ServiceProvider",
    "DependencyContainer",
    # Runtime Helpers
    "get_dependency_container",
    "set_dependency_container",
    "reset_dependency_container",
    "get_service_provider",
    "set_service_provider",
    "reset_service_provider",
]
