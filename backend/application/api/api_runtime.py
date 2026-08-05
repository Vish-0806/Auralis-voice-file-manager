"""API Runtime Coordinator Implementation (Phase 15.1).

Thread-safe, provider-independent API Runtime managing lifecycle transitions,
state validation, and delegation to the underlying ApiProvider.
"""

import logging
from threading import RLock
from typing import Optional

from backend.application.api.api_provider import ApiProvider
from backend.application.api.interfaces import IApiProvider, IApiRuntime
from backend.application.api.models import (
    ApiCapabilities,
    ApiConfiguration,
    ApiDiagnostics,
    ApiHealth,
    ApiState,
    ApiStatistics,
)

logger = logging.getLogger(__name__)


class ApiRuntime(IApiRuntime):
    """Production thread-safe API runtime coordinator."""

    def __init__(
        self,
        provider: Optional[IApiProvider] = None,
        config: Optional[ApiConfiguration] = None,
    ) -> None:
        """Initialize ApiRuntime using Constructor Dependency Injection.

        Args:
            provider: Optional IApiProvider implementation instance.
            config: Optional ApiConfiguration instance.
        """
        self._lock = RLock()
        self._provider = provider or ApiProvider(config=config)

    def initialize(
        self, config: Optional[ApiConfiguration] = None
    ) -> ApiState:
        """Initialize the API runtime and underlying provider.

        Args:
            config: Optional API configuration override.

        Returns:
            ApiState: Immutable state snapshot after initialization.
        """
        with self._lock:
            logger.info("Initializing ApiRuntime.")
            return self._provider.initialize(config=config)

    def shutdown(self) -> ApiState:
        """Shutdown the API runtime and underlying provider safely.

        Returns:
            ApiState: Immutable state snapshot after shutdown.
        """
        with self._lock:
            logger.info("Shutting down ApiRuntime.")
            return self._provider.shutdown()

    def restart(
        self, config: Optional[ApiConfiguration] = None
    ) -> ApiState:
        """Restart the API runtime and underlying provider.

        Args:
            config: Optional API configuration override.

        Returns:
            ApiState: Immutable state snapshot after restart.
        """
        with self._lock:
            logger.info("Restarting ApiRuntime.")
            return self._provider.restart(config=config)

    def health(self) -> ApiHealth:
        """Get health assessment snapshot from underlying provider.

        Returns:
            ApiHealth: Health snapshot.
        """
        with self._lock:
            return self._provider.health()

    def statistics(self) -> ApiStatistics:
        """Get runtime statistics snapshot from underlying provider.

        Returns:
            ApiStatistics: Statistics snapshot.
        """
        with self._lock:
            return self._provider.statistics()

    def capabilities(self) -> ApiCapabilities:
        """Get capability flags from underlying provider.

        Returns:
            ApiCapabilities: Capabilities snapshot.
        """
        with self._lock:
            return self._provider.capabilities()

    def diagnostics(self) -> ApiDiagnostics:
        """Get system diagnostics snapshot from underlying provider.

        Returns:
            ApiDiagnostics: Diagnostics snapshot.
        """
        with self._lock:
            return self._provider.diagnostics()

    def get_provider(self) -> IApiProvider:
        """Get the encapsulated IApiProvider instance.

        Returns:
            IApiProvider: Underlying API provider.
        """
        with self._lock:
            return self._provider
