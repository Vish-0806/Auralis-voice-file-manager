"""Dependency Injection Container (Phase 14.2.2).

Runtime container owning ServiceCollection and ServiceProvider, managing container state transitions,
capabilities, health checks, registration delegation, and statistics aggregation.
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
    """Production dependency injection container runtime executing registration delegation."""

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

    def register(self, descriptor: IServiceDescriptor) -> bool:
        """Register a ServiceDescriptor instance.

        Args:
            descriptor: ServiceDescriptor instance.

        Returns:
            bool: True if registration succeeded.
        """
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
        """Register a SINGLETON service descriptor.

        Returns:
            bool: True if registration succeeded.
        """
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
        """Register a TRANSIENT service descriptor.

        Returns:
            bool: True if registration succeeded.
        """
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
        """Register a SCOPED service descriptor.

        Returns:
            bool: True if registration succeeded.
        """
        with self._lock:
            return self._services.add_scoped(
                service_type=service_type,
                implementation_type=implementation_type,
                factory=factory,
                aliases=aliases,
                tags=tags,
            )

    def replace(self, descriptor: IServiceDescriptor) -> bool:
        """Replace an existing service registration.

        Args:
            descriptor: ServiceDescriptor instance.

        Returns:
            bool: True if replaced.
        """
        with self._lock:
            return self._services.replace(descriptor)

    def try_add(self, descriptor: IServiceDescriptor) -> bool:
        """Try adding a service descriptor if not already registered.

        Args:
            descriptor: ServiceDescriptor instance.

        Returns:
            bool: True if registered, False if existing.
        """
        with self._lock:
            return self._services.try_add(descriptor)

    def remove(self, service_type: Any) -> bool:
        """Remove a service registration by service_type.

        Args:
            service_type: Target service type to remove.

        Returns:
            bool: True if removed.
        """
        with self._lock:
            return self._services.remove(service_type)

    def remove_all(self) -> None:
        """Remove all service registrations from collection."""
        with self._lock:
            self._services.remove_all()

    def contains(self, service_type: Any) -> bool:
        """Check if service_type is registered.

        Args:
            service_type: Target service type.

        Returns:
            bool: True if registered.
        """
        with self._lock:
            return self._services.contains(service_type)

    def contains_alias(self, alias: str) -> bool:
        """Check if an alias is registered.

        Args:
            alias: Target alias string.

        Returns:
            bool: True if alias is present.
        """
        with self._lock:
            return self._services.contains_alias(alias)

    def get_descriptor(self, service_type: Any) -> Optional[IServiceDescriptor]:
        """Get descriptor by service_type.

        Args:
            service_type: Target service type.

        Returns:
            Optional[IServiceDescriptor]: Descriptor if registered.
        """
        with self._lock:
            return self._services.get_descriptor(service_type)

    def get_descriptor_by_alias(self, alias: str) -> Optional[IServiceDescriptor]:
        """Get descriptor by registered alias.

        Args:
            alias: Target alias string.

        Returns:
            Optional[IServiceDescriptor]: Descriptor if found.
        """
        with self._lock:
            return self._services.get_descriptor_by_alias(alias)

    def list_services(self) -> Tuple[ServiceDescriptorModel, ...]:
        """List all service descriptors in registration order.

        Returns:
            Tuple[ServiceDescriptorModel, ...]: Models tuple.
        """
        with self._lock:
            return self._services.list_services()

    def list_by_lifetime(self, lifetime: ServiceLifetime) -> Tuple[ServiceDescriptorModel, ...]:
        """List service descriptors filtered by lifetime scope.

        Args:
            lifetime: Lifetime enum filter.

        Returns:
            Tuple[ServiceDescriptorModel, ...]: Filtered models tuple.
        """
        with self._lock:
            return self._services.list_by_lifetime(lifetime)

    def list_aliases(self) -> Tuple[str, ...]:
        """List all registered service aliases.

        Returns:
            Tuple[str, ...]: Tuple of registered alias strings.
        """
        with self._lock:
            return self._services.list_aliases()

    def initialize(self) -> ContainerState:
        """Initialize the container and transition to READY state.

        Returns:
            ContainerState: Updated container state snapshot.
        """
        with self._lock:
            if self._state == ContainerState.READY:
                return self._state
            logger.info("Initializing DependencyContainer '%s'...", self._config.container_name)
            self._state = ContainerState.INITIALIZED
            self._state = ContainerState.READY
            logger.info("DependencyContainer initialized successfully. State -> READY.")
            return self._state

    def shutdown(self) -> ContainerState:
        """Shutdown the container and transition to STOPPED state.

        Returns:
            ContainerState: Updated container state snapshot.
        """
        with self._lock:
            if self._state == ContainerState.STOPPED:
                return self._state
            logger.info("Shutting down DependencyContainer...")
            self._state = ContainerState.STOPPING
            self._state = ContainerState.STOPPED
            logger.info("DependencyContainer shutdown complete. State -> STOPPED.")
            return self._state

    def restart(self) -> ContainerState:
        """Restart container operations.

        Returns:
            ContainerState: Updated container state snapshot.
        """
        with self._lock:
            logger.info("Restarting DependencyContainer...")
            self.shutdown()
            return self.initialize()

    def health(self) -> ContainerHealth:
        """Get current container health assessment.

        Returns:
            ContainerHealth: Health assessment snapshot.
        """
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
        """Get container statistics metrics aggregated across collection and provider.

        Returns:
            ContainerStatistics: Container statistics metrics.
        """
        with self._lock:
            provider_stats = self._provider.statistics()
            metrics: Dict[str, float] = {
                "registered_services_count": float(self._services.count()),
                "resolved_services_count": float(provider_stats.resolved_services_count),
                "active_scopes_count": float(provider_stats.active_scopes_count),
            }

            if isinstance(self._services, ServiceCollection):
                metrics.update(
                    {
                        "total_registrations": float(self._services.total_registrations),
                        "singleton_registrations": float(self._services.singleton_registrations),
                        "transient_registrations": float(self._services.transient_registrations),
                        "scoped_registrations": float(self._services.scoped_registrations),
                        "replacements": float(self._services.replacements),
                        "removals": float(self._services.removals),
                        "duplicates_rejected": float(self._services.duplicates_rejected),
                        "aliases_registered": float(self._services.aliases_registered),
                    }
                )

            return ContainerStatistics(
                registered_services_count=self._services.count(),
                resolved_services_count=provider_stats.resolved_services_count,
                active_scopes_count=provider_stats.active_scopes_count,
                metrics=metrics,
            )

    def capabilities(self) -> ContainerCapabilities:
        """Get container capability definitions.

        Returns:
            ContainerCapabilities: Immutable capabilities model.
        """
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
