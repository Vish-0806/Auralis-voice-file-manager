"""API Integration Runtime Coordinator Implementation (Phase 15.9).

Thread-safe, provider-independent API Integration Runtime coordinator managing lifecycle
operations and delegating queries to the underlying IntegrationProvider.
"""

import logging
from threading import RLock
from typing import Optional

from backend.application.api.integration.integration_provider import (
    IntegrationProvider,
)
from backend.application.api.integration.interfaces import (
    IIntegrationProvider,
    IIntegrationRuntime,
)
from backend.application.api.integration.models import (
    IntegrationCapabilities,
    IntegrationDiagnostics,
    IntegrationHealth,
    IntegrationStatistics,
)

logger = logging.getLogger(__name__)


class IntegrationRuntime(IIntegrationRuntime):
    """Production thread-safe integration runtime coordinator."""

    def __init__(self, provider: Optional[IIntegrationProvider] = None) -> None:
        """Initialize IntegrationRuntime using Constructor Dependency Injection.

        Args:
            provider: Optional IIntegrationProvider implementation instance.
        """
        self._lock = RLock()
        self._provider = provider or IntegrationProvider()

    def initialize(self) -> IntegrationHealth:
        """Initialize the integration runtime and underlying provider.

        Returns:
            IntegrationHealth: Health snapshot after initialization.
        """
        with self._lock:
            logger.info("Initializing IntegrationRuntime.")
            return self._provider.initialize()

    def shutdown(self) -> IntegrationHealth:
        """Shutdown the integration runtime and underlying provider safely.

        Returns:
            IntegrationHealth: Health snapshot after shutdown.
        """
        with self._lock:
            logger.info("Shutting down IntegrationRuntime.")
            return self._provider.shutdown()

    def restart(self) -> IntegrationHealth:
        """Restart the integration runtime and underlying provider.

        Returns:
            IntegrationHealth: Health snapshot after restart.
        """
        with self._lock:
            logger.info("Restarting IntegrationRuntime.")
            return self._provider.restart()

    def health(self) -> IntegrationHealth:
        """Get health evaluation snapshot from underlying provider.

        Returns:
            IntegrationHealth: Health snapshot.
        """
        with self._lock:
            return self._provider.health()

    def statistics(self) -> IntegrationStatistics:
        """Get aggregate statistics from underlying provider.

        Returns:
            IntegrationStatistics: Statistics snapshot.
        """
        with self._lock:
            return self._provider.statistics()

    def capabilities(self) -> IntegrationCapabilities:
        """Get capabilities from underlying provider.

        Returns:
            IntegrationCapabilities: Capabilities snapshot.
        """
        with self._lock:
            return self._provider.capabilities()

    def diagnostics(self) -> IntegrationDiagnostics:
        """Get diagnostic telemetry from underlying provider.

        Returns:
            IntegrationDiagnostics: Diagnostics snapshot.
        """
        with self._lock:
            return self._provider.diagnostics()

    def get_provider(self) -> IIntegrationProvider:
        """Get encapsulated IIntegrationProvider instance.

        Returns:
            IIntegrationProvider: Underlying integration provider.
        """
        with self._lock:
            return self._provider
