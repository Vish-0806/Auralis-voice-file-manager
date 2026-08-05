"""API Routing Runtime Coordinator Implementation (Phase 15.2).

Thread-safe, provider-independent API Routing Runtime managing lifecycle operations
and delegating state queries to the underlying RoutingProvider.
"""

import logging
from threading import RLock
from typing import Optional

from backend.application.api.routing.interfaces import (
    IRoutingProvider,
    IRoutingRuntime,
)
from backend.application.api.routing.models import (
    RouteCapabilities,
    RouteDiagnostics,
    RouteHealth,
    RouteStatistics,
)
from backend.application.api.routing.routing_provider import RoutingProvider

logger = logging.getLogger(__name__)


class RoutingRuntime(IRoutingRuntime):
    """Production thread-safe routing runtime coordinator."""

    def __init__(self, provider: Optional[IRoutingProvider] = None) -> None:
        """Initialize RoutingRuntime using Constructor Dependency Injection.

        Args:
            provider: Optional IRoutingProvider implementation instance.
        """
        self._lock = RLock()
        self._provider = provider or RoutingProvider()

    def initialize(self) -> RouteHealth:
        """Initialize the routing runtime and underlying provider.

        Returns:
            RouteHealth: Health evaluation snapshot after initialization.
        """
        with self._lock:
            logger.info("Initializing RoutingRuntime.")
            return self._provider.initialize()

    def shutdown(self) -> RouteHealth:
        """Shutdown the routing runtime and underlying provider safely.

        Returns:
            RouteHealth: Health evaluation snapshot after shutdown.
        """
        with self._lock:
            logger.info("Shutting down RoutingRuntime.")
            return self._provider.shutdown()

    def restart(self) -> RouteHealth:
        """Restart the routing runtime and underlying provider.

        Returns:
            RouteHealth: Health evaluation snapshot after restart.
        """
        with self._lock:
            logger.info("Restarting RoutingRuntime.")
            return self._provider.restart()

    def health(self) -> RouteHealth:
        """Get health evaluation snapshot from underlying provider.

        Returns:
            RouteHealth: Health evaluation snapshot.
        """
        with self._lock:
            return self._provider.health()

    def statistics(self) -> RouteStatistics:
        """Get aggregate statistics from underlying provider.

        Returns:
            RouteStatistics: Statistics snapshot.
        """
        with self._lock:
            return self._provider.statistics()

    def capabilities(self) -> RouteCapabilities:
        """Get routing capabilities from underlying provider.

        Returns:
            RouteCapabilities: Capabilities snapshot.
        """
        with self._lock:
            return self._provider.capabilities()

    def diagnostics(self) -> RouteDiagnostics:
        """Get diagnostic telemetry from underlying provider.

        Returns:
            RouteDiagnostics: Diagnostics snapshot.
        """
        with self._lock:
            return self._provider.diagnostics()

    def get_provider(self) -> IRoutingProvider:
        """Get encapsulated IRoutingProvider instance.

        Returns:
            IRoutingProvider: Underlying routing provider.
        """
        with self._lock:
            return self._provider
