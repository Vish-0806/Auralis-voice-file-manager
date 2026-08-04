"""Configuration Runtime (Phase 14.3.6).

Thread-safe production ConfigurationRuntime managing high-level provider lifecycle,
health assessment, statistics, capabilities, diagnostics, and certification.
"""

from datetime import datetime, timezone
import logging
from threading import RLock
from typing import Optional

from backend.application.config.configuration_provider import ConfigurationProvider
from backend.application.config.interfaces import IConfigurationProvider, IConfigurationRuntime
from backend.application.config.models import (
    ConfigurationCapabilities,
    ConfigurationCertificationResult,
    ConfigurationContext,
    ConfigurationDiagnostics,
    ConfigurationHealth,
    ConfigurationRuntimeState,
    ConfigurationStatistics,
)

logger = logging.getLogger(__name__)


class ConfigurationRuntime(IConfigurationRuntime):
    """Production ConfigurationRuntime executing lifecycle management and provider delegation."""

    def __init__(self, provider: Optional[IConfigurationProvider] = None) -> None:
        """Initialize ConfigurationRuntime using Constructor Dependency Injection.

        Args:
            provider: Optional IConfigurationProvider instance.
        """
        self._lock = RLock()
        self._provider = provider or ConfigurationProvider()

    @property
    def provider(self) -> IConfigurationProvider:
        """Get underlying IConfigurationProvider instance."""
        with self._lock:
            return self._provider

    def certify(self) -> ConfigurationCertificationResult:
        """Run production certification analysis."""
        with self._lock:
            return self._provider.certify()

    def validate_runtime(self) -> bool:
        """Validate configuration runtime readiness."""
        with self._lock:
            return self._provider.validate_runtime()

    def initialize(self) -> ConfigurationRuntimeState:
        """Initialize configuration runtime and provider."""
        with self._lock:
            logger.info("Initializing ConfigurationRuntime...")
            return self._provider.initialize()

    def shutdown(self) -> ConfigurationRuntimeState:
        """Shutdown configuration runtime and provider."""
        with self._lock:
            logger.info("Shutting down ConfigurationRuntime...")
            return self._provider.shutdown()

    def restart(self) -> ConfigurationRuntimeState:
        """Restart configuration runtime and provider."""
        with self._lock:
            logger.info("Restarting ConfigurationRuntime...")
            return self._provider.restart()

    def health(self) -> ConfigurationHealth:
        """Get health assessment snapshot of configuration runtime."""
        with self._lock:
            return self._provider.health()

    def statistics(self) -> ConfigurationStatistics:
        """Get statistics metrics snapshot of configuration runtime."""
        with self._lock:
            return self._provider.statistics()

    def capabilities(self) -> ConfigurationCapabilities:
        """Get capability definitions of configuration runtime."""
        with self._lock:
            return self._provider.capabilities()

    def diagnostics(self) -> ConfigurationDiagnostics:
        """Get diagnostics snapshot of configuration runtime."""
        with self._lock:
            return self._provider.diagnostics()

    def context(self) -> ConfigurationContext:
        """Get configuration execution context snapshot."""
        with self._lock:
            return self._provider.get_context()
