"""Service Provider (Phase 14.2.1).

Thread-safe skeleton service resolution engine implementing IServiceProvider.
All resolution methods raise NotImplementedError for Phase 14.2.1.
"""

from datetime import datetime, timezone
import logging
from threading import RLock
from typing import Any, Optional, Tuple

from backend.application.di.interfaces import IServiceCollection, IServiceProvider
from backend.application.di.models import (
    ContainerHealth,
    ContainerState,
    ContainerStatistics,
)

logger = logging.getLogger(__name__)


class ServiceProvider(IServiceProvider):
    """Thread-safe skeleton service provider for dependency resolution."""

    def __init__(self, services: Optional[IServiceCollection] = None) -> None:
        """Initialize ServiceProvider using Constructor Dependency Injection.

        Args:
            services: Optional ServiceCollection containing service descriptors.
        """
        self._lock = RLock()
        self._services = services
        self._resolved_count: int = 0
        self._active_scopes_count: int = 0

    def resolve(self, service_type: Any) -> Any:
        """Resolve a service instance by service type.

        Args:
            service_type: Registered target service type.

        Raises:
            NotImplementedError: Resolution logic belongs to a later phase.
        """
        raise NotImplementedError("Dependency resolution is not implemented in Phase 14.2.1.")

    def resolve_all(self, service_type: Any) -> Tuple[Any, ...]:
        """Resolve all registered instances for a service type.

        Args:
            service_type: Target service type.

        Raises:
            NotImplementedError: Resolution logic belongs to a later phase.
        """
        raise NotImplementedError("Dependency resolution is not implemented in Phase 14.2.1.")

    def create_scope(self) -> IServiceProvider:
        """Create a new scoped child ServiceProvider instance.

        Raises:
            NotImplementedError: Scope creation belongs to a later phase.
        """
        raise NotImplementedError("Scope creation is not implemented in Phase 14.2.1.")

    def dispose(self) -> None:
        """Dispose service provider and scoped instances.

        Raises:
            NotImplementedError: Disposal logic belongs to a later phase.
        """
        raise NotImplementedError("ServiceProvider disposal is not implemented in Phase 14.2.1.")

    def health(self) -> ContainerHealth:
        """Get health assessment of the provider.

        Returns:
            ContainerHealth: Provider health snapshot.
        """
        with self._lock:
            return ContainerHealth(
                is_healthy=True,
                state=ContainerState.READY,
                checked_at=datetime.now(timezone.utc),
            )

    def statistics(self) -> ContainerStatistics:
        """Get resolution statistics of the provider.

        Returns:
            ContainerStatistics: Provider statistics metrics.
        """
        with self._lock:
            registered = self._services.count() if self._services else 0
            return ContainerStatistics(
                registered_services_count=registered,
                resolved_services_count=self._resolved_count,
                active_scopes_count=self._active_scopes_count,
                metrics={
                    "resolved_services_count": float(self._resolved_count),
                    "active_scopes_count": float(self._active_scopes_count),
                },
            )
