"""Dependency Injection Interfaces (Phase 14.2.5).

Defines Abstract Base Classes (ABCs) establishing explicit design contracts for
ServiceDescriptor, ServiceCollection, ServiceProvider, and DependencyContainer.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional, Tuple

from backend.application.di.models import (
    ContainerDiagnostics,
    ContainerHealth,
    ContainerState,
    ContainerStatistics,
    DependencyAnalysis,
    DependencyCertification,
    DependencyIssue,
    ServiceDescriptorModel,
    ServiceLifetime,
)


class IServiceDescriptor(ABC):
    """Abstract interface for a Service Descriptor metadata container."""

    @property
    @abstractmethod
    def descriptor_id(self) -> str:
        """Get unique descriptor identifier."""
        raise NotImplementedError

    @property
    @abstractmethod
    def service_type(self) -> Any:
        """Get target service type or interface."""
        raise NotImplementedError

    @property
    @abstractmethod
    def implementation_type(self) -> Optional[Any]:
        """Get implementation class type if specified."""
        raise NotImplementedError

    @property
    @abstractmethod
    def lifetime(self) -> ServiceLifetime:
        """Get service lifetime scope."""
        raise NotImplementedError

    @property
    @abstractmethod
    def tags(self) -> Tuple[str, ...]:
        """Get descriptor tag labels."""
        raise NotImplementedError

    @property
    @abstractmethod
    def aliases(self) -> Tuple[str, ...]:
        """Get descriptor registered aliases."""
        raise NotImplementedError

    @abstractmethod
    def to_model(self) -> ServiceDescriptorModel:
        """Export descriptor metadata as an immutable Pydantic model.

        Returns:
            ServiceDescriptorModel: Descriptor metadata snapshot.
        """
        raise NotImplementedError


class IServiceCollection(ABC):
    """Abstract interface for Service Collection builder."""

    @abstractmethod
    def add_singleton(
        self,
        service_type: Any,
        implementation_type: Optional[Any] = None,
        factory: Optional[Callable[..., Any]] = None,
        instance: Optional[Any] = None,
        aliases: Optional[Tuple[str, ...]] = None,
        tags: Optional[Tuple[str, ...]] = None,
    ) -> bool:
        """Register a SINGLETON lifetime service.

        Returns:
            bool: True if registration succeeded.
        """
        raise NotImplementedError

    @abstractmethod
    def add_transient(
        self,
        service_type: Any,
        implementation_type: Optional[Any] = None,
        factory: Optional[Callable[..., Any]] = None,
        aliases: Optional[Tuple[str, ...]] = None,
        tags: Optional[Tuple[str, ...]] = None,
    ) -> bool:
        """Register a TRANSIENT lifetime service.

        Returns:
            bool: True if registration succeeded.
        """
        raise NotImplementedError

    @abstractmethod
    def add_scoped(
        self,
        service_type: Any,
        implementation_type: Optional[Any] = None,
        factory: Optional[Callable[..., Any]] = None,
        aliases: Optional[Tuple[str, ...]] = None,
        tags: Optional[Tuple[str, ...]] = None,
    ) -> bool:
        """Register a SCOPED lifetime service.

        Returns:
            bool: True if registration succeeded.
        """
        raise NotImplementedError

    @abstractmethod
    def register(self, descriptor: IServiceDescriptor) -> bool:
        """Register a ServiceDescriptor instance.

        Returns:
            bool: True if registration succeeded.
        """
        raise NotImplementedError

    @abstractmethod
    def replace(self, descriptor: IServiceDescriptor) -> bool:
        """Replace existing descriptor for service_type with new descriptor.

        Returns:
            bool: True if replaced.
        """
        raise NotImplementedError

    @abstractmethod
    def try_add(self, descriptor: IServiceDescriptor) -> bool:
        """Add descriptor only if service_type is not already registered.

        Returns:
            bool: True if added, False if already present.
        """
        raise NotImplementedError

    @abstractmethod
    def remove(self, service_type: Any) -> bool:
        """Remove a service registration by service type.

        Returns:
            bool: True if removed.
        """
        raise NotImplementedError

    @abstractmethod
    def remove_all(self) -> None:
        """Remove all registered services from collection."""
        raise NotImplementedError

    @abstractmethod
    def contains(self, service_type: Any) -> bool:
        """Check if service type is registered in the collection.

        Returns:
            bool: True if present.
        """
        raise NotImplementedError

    @abstractmethod
    def contains_alias(self, alias: str) -> bool:
        """Check if an alias is registered.

        Returns:
            bool: True if present.
        """
        raise NotImplementedError

    @abstractmethod
    def get_descriptor(self, service_type: Any) -> Optional[IServiceDescriptor]:
        """Get descriptor by service_type.

        Returns:
            Optional[IServiceDescriptor]: Descriptor if registered.
        """
        raise NotImplementedError

    @abstractmethod
    def get_descriptor_by_alias(self, alias: str) -> Optional[IServiceDescriptor]:
        """Get descriptor by registered alias.

        Returns:
            Optional[IServiceDescriptor]: Descriptor if found.
        """
        raise NotImplementedError

    @abstractmethod
    def count(self) -> int:
        """Get count of registered service descriptors.

        Returns:
            int: Number of registered services.
        """
        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        """Clear all registered services from collection."""
        raise NotImplementedError

    @abstractmethod
    def list_services(self) -> Tuple[ServiceDescriptorModel, ...]:
        """List all service descriptors in registration order.

        Returns:
            Tuple[ServiceDescriptorModel, ...]: Immutable tuple of models.
        """
        raise NotImplementedError

    @abstractmethod
    def list_by_lifetime(self, lifetime: ServiceLifetime) -> Tuple[ServiceDescriptorModel, ...]:
        """List service descriptors filtered by lifetime.

        Returns:
            Tuple[ServiceDescriptorModel, ...]: Filtered tuple of models.
        """
        raise NotImplementedError

    @abstractmethod
    def list_aliases(self) -> Tuple[str, ...]:
        """List all registered service aliases.

        Returns:
            Tuple[str, ...]: Immutable tuple of registered alias strings.
        """
        raise NotImplementedError

    @abstractmethod
    def statistics(self) -> Dict[str, float]:
        """Get registration statistics metrics.

        Returns:
            Dict[str, float]: Registration metrics dictionary.
        """
        raise NotImplementedError


class IServiceProvider(ABC):
    """Abstract interface for Service Provider resolution engine."""

    @property
    @abstractmethod
    def scope_id(self) -> str:
        """Get scope identifier string."""
        raise NotImplementedError

    @property
    @abstractmethod
    def depth(self) -> int:
        """Get depth of the scope hierarchy (0 for root)."""
        raise NotImplementedError

    @property
    @abstractmethod
    def is_disposed(self) -> bool:
        """Check if the scope has been disposed."""
        raise NotImplementedError

    @abstractmethod
    def resolve(self, service_type: Any) -> Any:
        """Resolve a service instance by service type.

        Args:
            service_type: Registered target service type.

        Returns:
            Any: Resolved service instance.
        """
        raise NotImplementedError

    @abstractmethod
    def resolve_required(self, service_type: Any) -> Any:
        """Resolve a required service instance, raising exception if missing.

        Args:
            service_type: Target service type.

        Returns:
            Any: Resolved service instance.
        """
        raise NotImplementedError

    @abstractmethod
    def try_resolve(self, service_type: Any) -> Optional[Any]:
        """Try resolving a service instance, returning None if missing.

        Args:
            service_type: Target service type.

        Returns:
            Optional[Any]: Resolved instance or None.
        """
        raise NotImplementedError

    @abstractmethod
    def resolve_all(self, service_type: Any) -> Tuple[Any, ...]:
        """Resolve all registered instances for a service type.

        Args:
            service_type: Target service type.

        Returns:
            Tuple[Any, ...]: Tuple of resolved instances.
        """
        raise NotImplementedError

    @abstractmethod
    def create_instance(self, implementation_type: Any) -> Any:
        """Construct an instance using constructor dependency injection.

        Args:
            implementation_type: Target class type to instantiate.

        Returns:
            Any: Instantiated object.
        """
        raise NotImplementedError

    @abstractmethod
    def create_scope(self) -> "IServiceProvider":
        """Create a new scoped child ServiceProvider instance.

        Returns:
            IServiceProvider: Scoped provider instance.
        """
        raise NotImplementedError

    @abstractmethod
    def dispose(self) -> None:
        """Dispose service provider and scoped instances."""
        raise NotImplementedError

    @abstractmethod
    def health(self) -> ContainerHealth:
        """Get health assessment of the provider.

        Returns:
            ContainerHealth: Provider health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def statistics(self) -> ContainerStatistics:
        """Get resolution statistics of the provider.

        Returns:
            ContainerStatistics: Provider statistics metrics.
        """
        raise NotImplementedError

    @abstractmethod
    def diagnostics(self) -> ContainerDiagnostics:
        """Get resolution diagnostics snapshot.

        Returns:
            ContainerDiagnostics: Provider diagnostics model.
        """
        raise NotImplementedError


class IDependencyContainer(ABC):
    """Abstract interface for Dependency Injection Container."""

    @abstractmethod
    def resolve(self, service_type: Any) -> Any:
        """Resolve a service instance by service_type."""
        raise NotImplementedError

    @abstractmethod
    def resolve_required(self, service_type: Any) -> Any:
        """Resolve a required service instance by service_type."""
        raise NotImplementedError

    @abstractmethod
    def try_resolve(self, service_type: Any) -> Optional[Any]:
        """Try resolving a service instance by service_type."""
        raise NotImplementedError

    @abstractmethod
    def resolve_all(self, service_type: Any) -> Tuple[Any, ...]:
        """Resolve all instances for a service_type."""
        raise NotImplementedError

    @abstractmethod
    def create_scope(self) -> IServiceProvider:
        """Create a new child scope ServiceProvider instance."""
        raise NotImplementedError

    @abstractmethod
    def dispose_scope(self, scope_id: str) -> bool:
        """Dispose a child scope by scope_id string."""
        raise NotImplementedError

    @abstractmethod
    def active_scopes(self) -> Tuple[str, ...]:
        """List all active scope_ids."""
        raise NotImplementedError

    @abstractmethod
    def scope_statistics(self) -> Dict[str, float]:
        """Get scope statistics metrics."""
        raise NotImplementedError

    @abstractmethod
    def analyze_graph(self) -> DependencyAnalysis:
        """Analyze complete dependency graph.

        Returns:
            DependencyAnalysis: Graph analysis snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def validate_graph(self) -> Tuple[DependencyIssue, ...]:
        """Validate dependency graph for cycles, missing dependencies, and lifetime errors.

        Returns:
            Tuple[DependencyIssue, ...]: Tuple of identified issues.
        """
        raise NotImplementedError

    @abstractmethod
    def certify(self) -> DependencyCertification:
        """Certify container for production deployment.

        Returns:
            DependencyCertification: Enterprise certification report.
        """
        raise NotImplementedError

    @abstractmethod
    def export_graph(self, format_type: str = "mermaid") -> str:
        """Export graph visualization format (mermaid, dot, adjacency_list, adjacency_map).

        Args:
            format_type: Output format string.

        Returns:
            str: Formatted graph representation string.
        """
        raise NotImplementedError

    @abstractmethod
    def initialize(self) -> ContainerState:
        """Initialize the dependency container and provider."""
        raise NotImplementedError

    @abstractmethod
    def shutdown(self) -> ContainerState:
        """Shutdown the container and dispose service providers."""
        raise NotImplementedError

    @abstractmethod
    def restart(self) -> ContainerState:
        """Restart container operations."""
        raise NotImplementedError

    @abstractmethod
    def health(self) -> ContainerHealth:
        """Get container health snapshot."""
        raise NotImplementedError

    @abstractmethod
    def statistics(self) -> ContainerStatistics:
        """Get container statistics."""
        raise NotImplementedError

    @abstractmethod
    def diagnostics(self) -> ContainerDiagnostics:
        """Get container diagnostics snapshot."""
        raise NotImplementedError
