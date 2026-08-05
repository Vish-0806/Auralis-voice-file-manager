"""API Authentication Runtime Coordinator Implementation (Phase 15.4).

Thread-safe, provider-independent API Authentication Runtime coordinator managing lifecycle
operations and delegating queries to the underlying AuthenticationProvider.
"""

import logging
from threading import RLock
from typing import Optional

from backend.application.api.auth.authentication_provider import (
    AuthenticationProvider,
)
from backend.application.api.auth.interfaces import (
    IAuthenticationProvider,
    IAuthenticationRuntime,
)
from backend.application.api.auth.models import (
    AuthenticationCapabilities,
    AuthenticationDiagnostics,
    AuthenticationHealth,
    AuthenticationStatistics,
)

logger = logging.getLogger(__name__)


class AuthenticationRuntime(IAuthenticationRuntime):
    """Production thread-safe authentication runtime coordinator."""

    def __init__(
        self, provider: Optional[IAuthenticationProvider] = None
    ) -> None:
        """Initialize AuthenticationRuntime using Constructor Dependency Injection.

        Args:
            provider: Optional IAuthenticationProvider implementation instance.
        """
        self._lock = RLock()
        self._provider = provider or AuthenticationProvider()

    def initialize(self) -> AuthenticationHealth:
        """Initialize the authentication runtime and underlying provider.

        Returns:
            AuthenticationHealth: Health snapshot after initialization.
        """
        with self._lock:
            logger.info("Initializing AuthenticationRuntime.")
            return self._provider.initialize()

    def shutdown(self) -> AuthenticationHealth:
        """Shutdown the authentication runtime and underlying provider safely.

        Returns:
            AuthenticationHealth: Health snapshot after shutdown.
        """
        with self._lock:
            logger.info("Shutting down AuthenticationRuntime.")
            return self._provider.shutdown()

    def restart(self) -> AuthenticationHealth:
        """Restart the authentication runtime and underlying provider.

        Returns:
            AuthenticationHealth: Health snapshot after restart.
        """
        with self._lock:
            logger.info("Restarting AuthenticationRuntime.")
            return self._provider.restart()

    def health(self) -> AuthenticationHealth:
        """Get health snapshot from underlying provider.

        Returns:
            AuthenticationHealth: Health evaluation snapshot.
        """
        with self._lock:
            return self._provider.health()

    def statistics(self) -> AuthenticationStatistics:
        """Get aggregate statistics from underlying provider.

        Returns:
            AuthenticationStatistics: Statistics snapshot.
        """
        with self._lock:
            return self._provider.statistics()

    def capabilities(self) -> AuthenticationCapabilities:
        """Get capabilities from underlying provider.

        Returns:
            AuthenticationCapabilities: Capabilities snapshot.
        """
        with self._lock:
            return self._provider.capabilities()

    def diagnostics(self) -> AuthenticationDiagnostics:
        """Get diagnostic telemetry from underlying provider.

        Returns:
            AuthenticationDiagnostics: Diagnostics snapshot.
        """
        with self._lock:
            return self._provider.diagnostics()

    def get_provider(self) -> IAuthenticationProvider:
        """Get encapsulated IAuthenticationProvider instance.

        Returns:
            IAuthenticationProvider: Underlying authentication provider.
        """
        with self._lock:
            return self._provider
