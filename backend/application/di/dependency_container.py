"""Dependency Injection Container (Phase 14.2.3).

Runtime container owning ServiceCollection and ServiceProvider, managing container state transitions,
capabilities, health checks, registration delegation, resolution delegation, and diagnostics.
"""

from datetime import datetime, timezone
import logging
from threading import RLock
from typing import Any, Callable, Dict, Optional, Tuple

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
    ServiceDescriptorModel,
    ServiceLifetime,
)
from backend.application.di.service_collection import ServiceCollection
from backend.application.di.service_provider import ServiceProvider

logger = logging.getLogger(__name__)


class DependencyContainer(IDependencyContainer):
    """Production dependency injection container runtime executing registration & resolution delegation."""

    def __init__(
        self,
        services: Optional[IServiceCollection] = None,
        provider: Optional[IServiceProvider] = None,
        config: Optional[ContainerConfiguration] = None,
    ) -> None:
        """Initialize DependencyContainer using Constructor Dependency Injection.

        Args:
            services: Optional ServiceCollection instance.
            provider: Optional ServiceProvider instance.
            config: Optional container configuration.
        """
        self._lock = RLock()
        self._config = config or ContainerConfiguration()
        self._services = services or ServiceCollection()
        self._provider = provider or ServiceProvider(services=self._services)
        self._state: ContainerState = ContainerState.UNINITIALIZED
        self._context: ContainerContext = ContainerContext(
            container_id=self._config.container_name,
        )

    @property
    def services(self) -> IServiceCollection:
        """Get the underlying ServiceCollection instance."""
        with self._lock:
            return self._services

    @property
    def provider(self) -> IServiceProvider:
        """Get the underlying ServiceProvider instance."""
        with self._lock:
            return self._provider

    # =========================================================================
    # Resolution Delegation APIs
    # =========================================================================

    def resolve(self, service_type: Any) -> Any:
        """Resolve a service instance by service_type.

        Returns:
            Any: Resolved service instance.
        """
        with self._lock:
            return self._provider.resolve(service_type)

    def resolve_required(self, service_type: Any) -> Any:
        """Resolve a required service instance by service_type.

        Returns:
            Any: Resolved service instance.
        """
        with self._lock:
            return self._provider.resolve_required(service_type)

    def try_resolve(self, service_type: Any) -> Optional[Any]:
        """Try resolving a service instance by service_type.

        Returns:
            Optional[Any]: Resolved service instance or None.
        """
        with self._lock:
            return self._provider.try_resolve(service_type)

    def resolve_all(self, service_type: Any) -> Tuple[Any, ...]:
        """Resolve all registered instances for service_type.

        Returns:
            Tuple[Any, ...]: Tuple of resolved instances.
        """
        with self._lock:
            return self._provider.resolve_all(service_type)

    # =========================================================================
    # Registration Delegation APIs
    # =========================================================================

    def register(self, descriptor: IServiceDescriptor) -> bool:
        """Register a ServiceDescriptor instance."""
        with self._lock:
            return self._services.register(descriptor)

    def add_singleton(
        self,
        service_type: Any,
        implementation_type: Optional[Any] = None,
        factory: Optional[Callable[..., Any]] = None,
        instance: Optional[Any] = None,
        aliases: Optional[Tuple[str, ...]] = None,
        tags: Optional[Tuple[str, ...]] = None,
    ) -> bool:
        """Register a SINGLETON service descriptor."""
        with self._lock:
            return self._services.add_singleton(
                service_type=service_type,
                implementation_type=implementation_type,
                factory=factory,
                instance=instance,
                aliases=aliases,
                tags=tags,
            )

    def add_transient(
        self,
        service_type: Any,
        implementation_type: Optional[Any] = None,
        factory: Optional[Callable[..., Any]] = None,
        aliases: Optional[Tuple[str, ...]] = None,
        tags: Optional[Tuple[str, ...]] = None,
    ) -> bool:
        """Register a TRANSIENT service descriptor."""
        with self._lock:
            return self._services.add_transient(
                service_type=service_type,
                implementation_type=implementation_type,
                factory=factory,
                aliases=aliases,
                tags=tags,
            )

    def add_scoped(
        self,
        service_type: Any,
        implementation_type: Optional[Any] = None,
        factory: Optional[Callable[..., Any]] = None,
        aliases: Optional[Tuple[str, ...]] = None,
        tags: Optional[Tuple[str, ...]] = None,
    ) -> bool:
        """Register a SCOPED service descriptor."""
        with self._lock:
            return self._services.add_scoped(
                service_type=service_type,
                implementation_type=implementation_type,
                factory=factory,
                aliases=aliases,
                tags=tags,
            )

    def replace(self, descriptor: IServiceDescriptor) -> bool:
        """Replace an existing service registration."""
        with self._lock:
            return self._services.replace(descriptor)

    def try_add(self, descriptor: IServiceDescriptor) -> bool:
        """Try adding a service descriptor if not already registered."""
        with self._lock:
            return self._services.try_add(descriptor)

    def remove(self, service_type: Any) -> bool:
        """Remove a service registration by service_type."""
        with self._lock:
            return self._services.remove(service_type)

    def remove_all(self) -> None:
        """Remove all service registrations from collection."""
        with self._lock:
            self._services.remove_all()

    def contains(self, service_type: Any) -> bool:
        """Check if service_type is registered."""
        with self._lock:
            return self._services.contains(service_type)

    def contains_alias(self, alias: str) -> bool:
        """Check if an alias is registered."""
        with self._lock:
            return self._services.contains_alias(alias)

    def get_descriptor(self, service_type: Any) -> Optional[IServiceDescriptor]:
        """Get descriptor by service_type."""
        with self._lock:
            return self._services.get_descriptor(service_type)

    def get_descriptor_by_alias(self, alias: str) -> Optional[IServiceDescriptor]:
        """Get descriptor by registered alias."""
        with self._lock:
            return self._services.get_descriptor_by_alias(alias)

    def list_services(self) -> Tuple[ServiceDescriptorModel, ...]:
        """List all service descriptors in registration order."""
        with self._lock:
            return self._services.list_services()

    def list_by_lifetime(self, lifetime: ServiceLifetime) -> Tuple[ServiceDescriptorModel, ...]:
        """List service descriptors filtered by lifetime scope."""
        with self._lock:
            return self._services.list_by_lifetime(lifetime)

    def list_aliases(self) -> Tuple[str, ...]:
        """List all registered service aliases."""
        with self._lock:
            return self._services.list_aliases()

    # =========================================================================
    # Container Lifecycle & Monitoring APIs
    # =========================================================================

    def initialize(self) -> ContainerState:
        """Initialize the container and transition to READY state."""
        with self._lock:
            if self._state == ContainerState.READY:
                return self._state
            logger.info("Initializing DependencyContainer '%s'...", self._config.container_name)
            self._state = ContainerState.INITIALIZED
            self._state = ContainerState.READY
            logger.info("DependencyContainer initialized successfully. State -> READY.")
            return self._state

    def shutdown(self) -> ContainerState:
        """Shutdown the container and transition to STOPPED state."""
        with self._lock:
            if self._state == ContainerState.STOPPED:
                return self._state
            logger.info("Shutting down DependencyContainer...")
            self._state = ContainerState.STOPPING
            self._state = ContainerState.STOPPED
            logger.info("DependencyContainer shutdown complete. State -> STOPPED.")
            return self._state

    def restart(self) -> ContainerState:
        """Restart container operations."""
        with self._lock:
            logger.info("Restarting DependencyContainer...")
            self.shutdown()
            return self.initialize()

    def health(self) -> ContainerHealth:
        """Get current container health assessment."""
        with self._lock:
            is_healthy = self._state in (ContainerState.READY, ContainerState.INITIALIZED, ContainerState.UNINITIALIZED)
            issues = () if is_healthy else (f"Container state is {self._state.value}.",)
            return ContainerHealth(
                is_healthy=is_healthy,
                state=self._state,
                issues=issues,
                checked_at=datetime.now(timezone.utc),
            )

    def statistics(self) -> ContainerStatistics:
        """Get container statistics metrics aggregated across collection and provider."""
        with self._lock:
            provider_stats = self._provider.statistics()
            service_stats = self._services.statistics()
            metrics: Dict[str, float] = {
                "registered_services_count": float(self._services.count()),
                "resolved_services_count": float(provider_stats.resolved_services_count),
                "active_scopes_count": float(provider_stats.active_scopes_count),
            }

            metrics.update(service_stats)
            metrics.update(provider_stats.metrics)

            return ContainerStatistics(
                registered_services_count=self._services.count(),
                resolved_services_count=provider_stats.resolved_services_count,
                active_scopes_count=provider_stats.active_scopes_count,
                metrics=metrics,
            )

    def diagnostics(self) -> ContainerDiagnostics:
        """Get container diagnostics snapshot.

        Returns:
            ContainerDiagnostics: Diagnostics snapshot.
        """
        with self._lock:
            return self._provider.diagnostics()

    def capabilities(self) -> ContainerCapabilities:
        """Get container capability definitions."""
        return ContainerCapabilities(
            supports_singleton=True,
            supports_transient=True,
            supports_scoped=True,
            supports_factories=True,
            supports_instances=True,
            supports_aliases=True,
            supports_tags=True,
            supports_replacement=True,
        )
