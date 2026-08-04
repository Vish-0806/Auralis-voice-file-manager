"""Dependency Injection Framework (Phase 14.2.5).

Package exports for models, exceptions, interfaces, service descriptor,
service collection, service provider, dependency graph analyzer, dependency container, and runtime accessors.
"""

from backend.application.di.dependency_container import DependencyContainer
from backend.application.di.dependency_graph_analyzer import DependencyGraphAnalyzer
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
    ContainerDiagnostics,
    ContainerHealth,
    ContainerState,
    ContainerStatistics,
    DependencyAnalysis,
    DependencyCertification,
    DependencyEdge,
    DependencyGraph,
    DependencyGraphNode,
    DependencyIssue,
    DependencyNode,
    GraphStatistics,
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
    "ServiceLifetime",
    "ContainerState",
    "ServiceDescriptorModel",
    "ServiceRegistration",
    "DependencyGraphNode",
    "DependencyNode",
    "DependencyEdge",
    "DependencyGraph",
    "DependencyIssue",
    "GraphStatistics",
    "DependencyAnalysis",
    "DependencyCertification",
    "ContainerCapabilities",
    "ContainerStatistics",
    "ContainerDiagnostics",
    "ContainerHealth",
    "ContainerConfiguration",
    "ContainerContext",
    "DependencyInjectionException",
    "ServiceRegistrationException",
    "ServiceResolutionException",
    "CircularDependencyException",
    "ServiceValidationException",
    "IServiceDescriptor",
    "IServiceCollection",
    "IServiceProvider",
    "IDependencyContainer",
    "ServiceDescriptor",
    "ServiceCollection",
    "ServiceProvider",
    "DependencyGraphAnalyzer",
    "DependencyContainer",
    "get_dependency_container",
    "set_dependency_container",
    "reset_dependency_container",
    "get_service_provider",
    "set_service_provider",
    "reset_service_provider",
]
