"""API Middleware Runtime Coordinator Implementation (Phase 15.3).

Thread-safe, provider-independent API Middleware Runtime coordinator managing lifecycle operations
and delegating state queries to the underlying MiddlewareProvider.
"""

import logging
from threading import RLock
from typing import Optional

from backend.application.api.middleware.interfaces import (
    IMiddlewareProvider,
    IMiddlewareRuntime,
)
from backend.application.api.middleware.middleware_provider import (
    MiddlewareProvider,
)
from backend.application.api.middleware.models import (
    MiddlewareCapabilities,
    MiddlewareDiagnostics,
    MiddlewareHealth,
    MiddlewareStatistics,
)

logger = logging.getLogger(__name__)


class MiddlewareRuntime(IMiddlewareRuntime):
    """Production thread-safe middleware runtime coordinator."""

    def __init__(self, provider: Optional[IMiddlewareProvider] = None) -> None:
        """Initialize MiddlewareRuntime using Constructor Dependency Injection.

        Args:
            provider: Optional IMiddlewareProvider implementation instance.
        """
        self._lock = RLock()
        self._provider = provider or MiddlewareProvider()

    def initialize(self) -> MiddlewareHealth:
        """Initialize the middleware runtime and underlying provider.

        Returns:
            MiddlewareHealth: Health evaluation snapshot after initialization.
        """
        with self._lock:
            logger.info("Initializing MiddlewareRuntime.")
            return self._provider.initialize()

    def shutdown(self) -> MiddlewareHealth:
        """Shutdown the middleware runtime and underlying provider safely.

        Returns:
            MiddlewareHealth: Health evaluation snapshot after shutdown.
        """
        with self._lock:
            logger.info("Shutting down MiddlewareRuntime.")
            return self._provider.shutdown()

    def restart(self) -> MiddlewareHealth:
        """Restart the middleware runtime and underlying provider.

        Returns:
            MiddlewareHealth: Health evaluation snapshot after restart.
        """
        with self._lock:
            logger.info("Restarting MiddlewareRuntime.")
            return self._provider.restart()

    def health(self) -> MiddlewareHealth:
        """Get health evaluation snapshot from underlying provider.

        Returns:
            MiddlewareHealth: Health evaluation snapshot.
        """
        with self._lock:
            return self._provider.health()

    def statistics(self) -> MiddlewareStatistics:
        """Get aggregate statistics from underlying provider.

        Returns:
            MiddlewareStatistics: Statistics snapshot.
        """
        with self._lock:
            return self._provider.statistics()

    def capabilities(self) -> MiddlewareCapabilities:
        """Get middleware capabilities from underlying provider.

        Returns:
            MiddlewareCapabilities: Capabilities snapshot.
        """
        with self._lock:
            return self._provider.capabilities()

    def diagnostics(self) -> MiddlewareDiagnostics:
        """Get diagnostic telemetry from underlying provider.

        Returns:
            MiddlewareDiagnostics: Diagnostics snapshot.
        """
        with self._lock:
            return self._provider.diagnostics()

    def get_provider(self) -> IMiddlewareProvider:
        """Get encapsulated IMiddlewareProvider instance.

        Returns:
            IMiddlewareProvider: Underlying middleware provider.
        """
        with self._lock:
            return self._provider
