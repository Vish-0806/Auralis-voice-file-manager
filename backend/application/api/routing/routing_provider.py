"""API Routing Provider Implementation (Phase 15.2).

Thread-safe routing provider aggregating RouteRegistry, RouteResolver, and RequestDispatcher
with complete lifecycle, health, statistics, capabilities, and diagnostic capabilities.
"""

from datetime import datetime, timezone
import logging
from threading import RLock
import threading
from typing import Optional, Tuple

from backend.application.api.routing.interfaces import (
    IRequestDispatcher,
    IRouteRegistry,
    IRouteResolver,
    IRoutingProvider,
)
from backend.application.api.routing.models import (
    RouteCapabilities,
    RouteDiagnostics,
    RouteHealth,
    RouteState,
    RouteStatistics,
    RoutingRuntimeState,
)
from backend.application.api.routing.request_dispatcher import RequestDispatcher
from backend.application.api.routing.route_registry import RouteRegistry
from backend.application.api.routing.route_resolver import RouteResolver

logger = logging.getLogger(__name__)


class RoutingProvider(IRoutingProvider):
    """Production thread-safe routing provider aggregating routing components."""

    def __init__(
        self,
        registry: Optional[IRouteRegistry] = None,
        resolver: Optional[IRouteResolver] = None,
        dispatcher: Optional[IRequestDispatcher] = None,
        capabilities: Optional[RouteCapabilities] = None,
    ) -> None:
        """Initialize RoutingProvider using Constructor Dependency Injection.

        Args:
            registry: Optional IRouteRegistry implementation instance.
            resolver: Optional IRouteResolver implementation instance.
            dispatcher: Optional IRequestDispatcher implementation instance.
            capabilities: Optional RouteCapabilities instance.
        """
        self._lock = RLock()
        self._registry = registry or RouteRegistry()
        self._resolver = resolver or RouteResolver(registry=self._registry)
        self._dispatcher = dispatcher or RequestDispatcher(resolver=self._resolver)
        self._capabilities = capabilities or RouteCapabilities()

        self._status = RoutingRuntimeState.UNINITIALIZED
        self._total_initializations = 0
        self._total_restarts = 0
        self._total_shutdowns = 0

    def initialize(self) -> RouteHealth:
        """Initialize the routing provider and transition to READY state.

        Returns:
            RouteHealth: Health evaluation snapshot after initialization.
        """
        with self._lock:
            if self._status in (RoutingRuntimeState.INITIALIZING, RoutingRuntimeState.READY):
                return self.health()

            self._status = RoutingRuntimeState.INITIALIZING
            logger.info("RoutingProvider transitioning to INITIALIZING state.")

            self._status = RoutingRuntimeState.READY
            self._total_initializations += 1
            logger.info("RoutingProvider successfully initialized and READY.")
            return self.health()

    def shutdown(self) -> RouteHealth:
        """Shutdown the routing provider safely and transition to STOPPED state.

        Returns:
            RouteHealth: Health evaluation snapshot after shutdown.
        """
        with self._lock:
            if self._status == RoutingRuntimeState.STOPPED:
                return self.health()

            self._status = RoutingRuntimeState.STOPPING
            logger.info("RoutingProvider transitioning to STOPPING state.")

            self._status = RoutingRuntimeState.STOPPED
            self._total_shutdowns += 1
            logger.info("RoutingProvider successfully stopped.")
            return self.health()

    def restart(self) -> RouteHealth:
        """Restart the routing provider by shutting down if active, then initializing.

        Returns:
            RouteHealth: Health evaluation snapshot after restart.
        """
        with self._lock:
            logger.info("RoutingProvider restarting...")
            if self._status != RoutingRuntimeState.STOPPED:
                self.shutdown()

            health = self.initialize()
            self._total_restarts += 1
            return health

    def health(self) -> RouteHealth:
        """Get health evaluation snapshot.

        Returns:
            RouteHealth: Immutable health snapshot.
        """
        with self._lock:
            is_healthy = self._status in (
                RoutingRuntimeState.READY,
                RoutingRuntimeState.UNINITIALIZED,
            )
            issues: Tuple[str, ...] = ()
            if not is_healthy:
                issues = (f"Routing provider is in state: {self._status.value}",)

            return RouteHealth(
                is_healthy=is_healthy,
                state=self._status,
                details={
                    "status": self._status.value,
                    "registered_routes": self._registry.count(),
                    "groups_count": len(self._registry.list_groups()),
                },
                issues=issues,
                checked_at=datetime.now(timezone.utc),
            )

    def statistics(self) -> RouteStatistics:
        """Get aggregate routing metrics and statistics.

        Returns:
            RouteStatistics: Immutable statistics snapshot.
        """
        with self._lock:
            all_routes = self._registry.list_routes()
            total_routes = len(all_routes)
            active_routes = sum(1 for r in all_routes if r.state == RouteState.ACTIVE)
            disabled_routes = sum(1 for r in all_routes if r.state == RouteState.DISABLED)
            total_groups = len(self._registry.list_groups())

            dispatch_stats = {}
            if hasattr(self._dispatcher, "get_dispatch_statistics"):
                dispatch_stats = getattr(self._dispatcher, "get_dispatch_statistics")()

            return RouteStatistics(
                total_routes=total_routes,
                active_routes=active_routes,
                disabled_routes=disabled_routes,
                total_groups=total_groups,
                total_dispatches=dispatch_stats.get("total_dispatches", 0),
                failed_dispatches=dispatch_stats.get("failed_dispatches", 0),
                metrics={
                    "total_initializations": float(self._total_initializations),
                    "total_restarts": float(self._total_restarts),
                    "total_shutdowns": float(self._total_shutdowns),
                },
            )

    def capabilities(self) -> RouteCapabilities:
        """Get declared routing capabilities.

        Returns:
            RouteCapabilities: Immutable capabilities snapshot.
        """
        with self._lock:
            return self._capabilities

    def diagnostics(self) -> RouteDiagnostics:
        """Get diagnostic telemetry for the routing provider.

        Returns:
            RouteDiagnostics: Immutable diagnostic snapshot.
        """
        with self._lock:
            messages: Tuple[str, ...] = (
                f"Status: {self._status.value}",
                f"Total Routes: {self._registry.count()}",
                f"Total Groups: {len(self._registry.list_groups())}",
                f"Initializations: {self._total_initializations}",
                f"Restarts: {self._total_restarts}",
            )
            return RouteDiagnostics(
                state=self._status,
                registered_routes_count=self._registry.count(),
                groups_count=len(self._registry.list_groups()),
                timestamp=datetime.now(timezone.utc),
                thread_count=threading.active_count(),
                diagnostic_messages=messages,
                details={
                    "status": self._status.value,
                    "total_shutdowns": self._total_shutdowns,
                },
            )

    def get_registry(self) -> IRouteRegistry:
        """Get encapsulated route registry instance.

        Returns:
            IRouteRegistry: Encapsulated registry.
        """
        with self._lock:
            return self._registry

    def get_resolver(self) -> IRouteResolver:
        """Get encapsulated route resolver instance.

        Returns:
            IRouteResolver: Encapsulated resolver.
        """
        with self._lock:
            return self._resolver

    def get_dispatcher(self) -> IRequestDispatcher:
        """Get encapsulated request dispatcher instance.

        Returns:
            IRequestDispatcher: Encapsulated dispatcher.
        """
        with self._lock:
            return self._dispatcher
