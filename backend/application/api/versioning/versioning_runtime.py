"""API Versioning Runtime Coordinator Implementation (Phase 15.6).

Thread-safe, provider-independent API Versioning Runtime coordinator managing lifecycle
operations and delegating queries to the underlying VersioningProvider.
"""

import logging
from threading import RLock
from typing import Optional

from backend.application.api.versioning.interfaces import (
    IVersioningProvider,
    IVersioningRuntime,
)
from backend.application.api.versioning.models import (
    VersionCapabilities,
    VersionDiagnostics,
    VersionHealth,
    VersionStatistics,
)
from backend.application.api.versioning.versioning_provider import (
    VersioningProvider,
)

logger = logging.getLogger(__name__)


class VersioningRuntime(IVersioningRuntime):
    """Production thread-safe versioning runtime coordinator."""

    def __init__(self, provider: Optional[IVersioningProvider] = None) -> None:
        """Initialize VersioningRuntime using Constructor Dependency Injection.

        Args:
            provider: Optional IVersioningProvider implementation instance.
        """
        self._lock = RLock()
        self._provider = provider or VersioningProvider()

    def initialize(self) -> VersionHealth:
        """Initialize the versioning runtime and underlying provider.

        Returns:
            VersionHealth: Health snapshot after initialization.
        """
        with self._lock:
            logger.info("Initializing VersioningRuntime.")
            return self._provider.initialize()

    def shutdown(self) -> VersionHealth:
        """Shutdown the versioning runtime and underlying provider safely.

        Returns:
            VersionHealth: Health snapshot after shutdown.
        """
        with self._lock:
            logger.info("Shutting down VersioningRuntime.")
            return self._provider.shutdown()

    def restart(self) -> VersionHealth:
        """Restart the versioning runtime and underlying provider.

        Returns:
            VersionHealth: Health snapshot after restart.
        """
        with self._lock:
            logger.info("Restarting VersioningRuntime.")
            return self._provider.restart()

    def health(self) -> VersionHealth:
        """Get health evaluation snapshot from underlying provider.

        Returns:
            VersionHealth: Health snapshot.
        """
        with self._lock:
            return self._provider.health()

    def statistics(self) -> VersionStatistics:
        """Get aggregate statistics from underlying provider.

        Returns:
            VersionStatistics: Statistics snapshot.
        """
        with self._lock:
            return self._provider.statistics()

    def capabilities(self) -> VersionCapabilities:
        """Get capabilities from underlying provider.

        Returns:
            VersionCapabilities: Capabilities snapshot.
        """
        with self._lock:
            return self._provider.capabilities()

    def diagnostics(self) -> VersionDiagnostics:
        """Get diagnostic telemetry from underlying provider.

        Returns:
            VersionDiagnostics: Diagnostics snapshot.
        """
        with self._lock:
            return self._provider.diagnostics()

    def get_provider(self) -> IVersioningProvider:
        """Get encapsulated IVersioningProvider instance.

        Returns:
            IVersioningProvider: Underlying versioning provider.
        """
        with self._lock:
            return self._provider
