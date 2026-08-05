"""API Validation Runtime Coordinator Implementation (Phase 15.5).

Thread-safe, provider-independent API Validation Runtime coordinator managing lifecycle
operations and delegating queries to the underlying ValidationProvider.
"""

import logging
from threading import RLock
from typing import Optional

from backend.application.api.validation.interfaces import (
    IValidationProvider,
    IValidationRuntime,
)
from backend.application.api.validation.models import (
    ValidationCapabilities,
    ValidationDiagnostics,
    ValidationHealth,
    ValidationStatistics,
)
from backend.application.api.validation.validation_provider import (
    ValidationProvider,
)

logger = logging.getLogger(__name__)


class ValidationRuntime(IValidationRuntime):
    """Production thread-safe validation runtime coordinator."""

    def __init__(self, provider: Optional[IValidationProvider] = None) -> None:
        """Initialize ValidationRuntime using Constructor Dependency Injection.

        Args:
            provider: Optional IValidationProvider implementation instance.
        """
        self._lock = RLock()
        self._provider = provider or ValidationProvider()

    def initialize(self) -> ValidationHealth:
        """Initialize the validation runtime and underlying provider.

        Returns:
            ValidationHealth: Health snapshot after initialization.
        """
        with self._lock:
            logger.info("Initializing ValidationRuntime.")
            return self._provider.initialize()

    def shutdown(self) -> ValidationHealth:
        """Shutdown the validation runtime and underlying provider safely.

        Returns:
            ValidationHealth: Health snapshot after shutdown.
        """
        with self._lock:
            logger.info("Shutting down ValidationRuntime.")
            return self._provider.shutdown()

    def restart(self) -> ValidationHealth:
        """Restart the validation runtime and underlying provider.

        Returns:
            ValidationHealth: Health snapshot after restart.
        """
        with self._lock:
            logger.info("Restarting ValidationRuntime.")
            return self._provider.restart()

    def health(self) -> ValidationHealth:
        """Get health evaluation snapshot from underlying provider.

        Returns:
            ValidationHealth: Health snapshot.
        """
        with self._lock:
            return self._provider.health()

    def statistics(self) -> ValidationStatistics:
        """Get aggregate statistics from underlying provider.

        Returns:
            ValidationStatistics: Statistics snapshot.
        """
        with self._lock:
            return self._provider.statistics()

    def capabilities(self) -> ValidationCapabilities:
        """Get capabilities from underlying provider.

        Returns:
            ValidationCapabilities: Capabilities snapshot.
        """
        with self._lock:
            return self._provider.capabilities()

    def diagnostics(self) -> ValidationDiagnostics:
        """Get diagnostic telemetry from underlying provider.

        Returns:
            ValidationDiagnostics: Diagnostics snapshot.
        """
        with self._lock:
            return self._provider.diagnostics()

    def get_provider(self) -> IValidationProvider:
        """Get encapsulated IValidationProvider instance.

        Returns:
            IValidationProvider: Underlying validation provider.
        """
        with self._lock:
            return self._provider
