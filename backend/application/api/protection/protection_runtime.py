"""API Protection Runtime Coordinator Implementation (Phase 15.8).

Thread-safe, provider-independent API Protection Runtime coordinator managing lifecycle
operations and delegating queries to the underlying ProtectionProvider.
"""

import logging
from threading import RLock
from typing import Optional

from backend.application.api.protection.interfaces import (
    IProtectionProvider,
    IProtectionRuntime,
)
from backend.application.api.protection.models import (
    ProtectionCapabilities,
    ProtectionDiagnostics,
    ProtectionHealth,
    ProtectionStatistics,
)
from backend.application.api.protection.protection_provider import (
    ProtectionProvider,
)

logger = logging.getLogger(__name__)


class ProtectionRuntime(IProtectionRuntime):
    """Production thread-safe protection runtime coordinator."""

    def __init__(self, provider: Optional[IProtectionProvider] = None) -> None:
        """Initialize ProtectionRuntime using Constructor Dependency Injection.

        Args:
            provider: Optional IProtectionProvider implementation instance.
        """
        self._lock = RLock()
        self._provider = provider or ProtectionProvider()

    def initialize(self) -> ProtectionHealth:
        """Initialize the protection runtime and underlying provider.

        Returns:
            ProtectionHealth: Health snapshot after initialization.
        """
        with self._lock:
            logger.info("Initializing ProtectionRuntime.")
            return self._provider.initialize()

    def shutdown(self) -> ProtectionHealth:
        """Shutdown the protection runtime and underlying provider safely.

        Returns:
            ProtectionHealth: Health snapshot after shutdown.
        """
        with self._lock:
            logger.info("Shutting down ProtectionRuntime.")
            return self._provider.shutdown()

    def restart(self) -> ProtectionHealth:
        """Restart the protection runtime and underlying provider.

        Returns:
            ProtectionHealth: Health snapshot after restart.
        """
        with self._lock:
            logger.info("Restarting ProtectionRuntime.")
            return self._provider.restart()

    def health(self) -> ProtectionHealth:
        """Get health evaluation snapshot from underlying provider.

        Returns:
            ProtectionHealth: Health snapshot.
        """
        with self._lock:
            return self._provider.health()

    def statistics(self) -> ProtectionStatistics:
        """Get aggregate statistics from underlying provider.

        Returns:
            ProtectionStatistics: Statistics snapshot.
        """
        with self._lock:
            return self._provider.statistics()

    def capabilities(self) -> ProtectionCapabilities:
        """Get capabilities from underlying provider.

        Returns:
            ProtectionCapabilities: Capabilities snapshot.
        """
        with self._lock:
            return self._provider.capabilities()

    def diagnostics(self) -> ProtectionDiagnostics:
        """Get diagnostic telemetry from underlying provider.

        Returns:
            ProtectionDiagnostics: Diagnostics snapshot.
        """
        with self._lock:
            return self._provider.diagnostics()

    def get_provider(self) -> IProtectionProvider:
        """Get encapsulated IProtectionProvider instance.

        Returns:
            IProtectionProvider: Underlying protection provider.
        """
        with self._lock:
            return self._provider
