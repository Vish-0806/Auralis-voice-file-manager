"""Configuration Runtime (Phase 14.3.1).

Thread-safe production configuration runtime managing lifecycle state transitions,
provider coordination, monitoring, capabilities, health, statistics, and diagnostics.
"""

from datetime import datetime, timezone
import logging
from threading import RLock
from typing import Optional

from backend.application.config.configuration_provider import ConfigurationProvider
from backend.application.config.interfaces import IConfigurationProvider, IConfigurationRuntime
from backend.application.config.models import (
    ConfigurationCapabilities,
    ConfigurationContext,
    ConfigurationDiagnostics,
    ConfigurationHealth,
    ConfigurationRuntimeState,
    ConfigurationStatistics,
)

logger = logging.getLogger(__name__)


class ConfigurationRuntime(IConfigurationRuntime):
    """Production ConfigurationRuntime managing lifecycle transitions and provider delegation."""

    def __init__(self, provider: Optional[IConfigurationProvider] = None) -> None:
        """Initialize ConfigurationRuntime using Constructor Dependency Injection.

        Args:
            provider: Optional IConfigurationProvider instance.
        """
        self._lock = RLock()
        self._provider = provider or ConfigurationProvider()
        self._state: ConfigurationRuntimeState = ConfigurationRuntimeState.UNINITIALIZED

    @property
    def provider(self) -> IConfigurationProvider:
        """Get the underlying IConfigurationProvider instance."""
        with self._lock:
            return self._provider

    def initialize(self) -> ConfigurationRuntimeState:
        """Initialize configuration runtime and provider transition to READY state.

        Returns:
            ConfigurationRuntimeState: Updated state snapshot.
        """
        with self._lock:
            if self._state == ConfigurationRuntimeState.READY:
                return self._state
            logger.info("Initializing ConfigurationRuntime...")
            self._state = ConfigurationRuntimeState.INITIALIZING
            self._provider.initialize()
            self._state = ConfigurationRuntimeState.READY
            logger.info("ConfigurationRuntime initialized successfully. State -> READY.")
            return self._state

    def shutdown(self) -> ConfigurationRuntimeState:
        """Shutdown configuration runtime and provider transition to STOPPED state.

        Returns:
            ConfigurationRuntimeState: Updated state snapshot.
        """
        with self._lock:
            if self._state == ConfigurationRuntimeState.STOPPED:
                return self._state
            logger.info("Shutting down ConfigurationRuntime...")
            self._state = ConfigurationRuntimeState.STOPPING
            self._provider.shutdown()
            self._state = ConfigurationRuntimeState.STOPPED
            logger.info("ConfigurationRuntime shutdown complete. State -> STOPPED.")
            return self._state

    def restart(self) -> ConfigurationRuntimeState:
        """Restart configuration runtime operations.

        Returns:
            ConfigurationRuntimeState: Updated state snapshot.
        """
        with self._lock:
            logger.info("Restarting ConfigurationRuntime...")
            self.shutdown()
            return self.initialize()

    def health(self) -> ConfigurationHealth:
        """Get current configuration health assessment snapshot.

        Returns:
            ConfigurationHealth: Provider health snapshot model.
        """
        with self._lock:
            is_healthy = self._state in (
                ConfigurationRuntimeState.READY,
                ConfigurationRuntimeState.INITIALIZING,
                ConfigurationRuntimeState.UNINITIALIZED,
            )
            issues = () if is_healthy else (f"ConfigurationRuntime state is {self._state.value}.",)
            return ConfigurationHealth(
                is_healthy=is_healthy and self._provider.health().is_healthy,
                state=self._state,
                issues=issues,
                checked_at=datetime.now(timezone.utc),
            )

    def statistics(self) -> ConfigurationStatistics:
        """Get aggregated configuration statistics.

        Returns:
            ConfigurationStatistics: Metrics snapshot model.
        """
        with self._lock:
            return self._provider.statistics()

    def capabilities(self) -> ConfigurationCapabilities:
        """Get configuration runtime capabilities.

        Returns:
            ConfigurationCapabilities: Capabilities declaration model.
        """
        with self._lock:
            return self._provider.capabilities()

    def diagnostics(self) -> ConfigurationDiagnostics:
        """Get detailed configuration runtime diagnostics.

        Returns:
            ConfigurationDiagnostics: Diagnostics snapshot model.
        """
        with self._lock:
            return self._provider.diagnostics()

    def context(self) -> ConfigurationContext:
        """Get configuration execution context snapshot.

        Returns:
            ConfigurationContext: Context model snapshot.
        """
        with self._lock:
            return self._provider.get_context()
