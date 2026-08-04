"""Configuration Provider (Phase 14.3.2).

Thread-safe production configuration provider runtime coordinating configuration state,
sources, context, capabilities, health reporting, statistics, and diagnostics snapshots.
"""

from datetime import datetime, timezone
import logging
from threading import RLock
from typing import Dict, Optional

from backend.application.config.configuration_source_manager import ConfigurationSourceManager
from backend.application.config.interfaces import IConfigurationProvider
from backend.application.config.models import (
    ConfigurationCapabilities,
    ConfigurationContext,
    ConfigurationDiagnostics,
    ConfigurationHealth,
    ConfigurationProfileType,
    ConfigurationRuntimeState,
    ConfigurationStatistics,
)

logger = logging.getLogger(__name__)


class ConfigurationProvider(IConfigurationProvider):
    """Production ConfigurationProvider runtime executing configuration state & source management."""

    def __init__(
        self,
        source_manager: Optional[ConfigurationSourceManager] = None,
        config_context: Optional[ConfigurationContext] = None,
    ) -> None:
        """Initialize ConfigurationProvider using Constructor Dependency Injection.

        Args:
            source_manager: Optional ConfigurationSourceManager instance.
            config_context: Optional ConfigurationContext snapshot.
        """
        self._lock = RLock()
        self._context = config_context or ConfigurationContext()
        self._source_manager = source_manager or ConfigurationSourceManager()
        self._state: ConfigurationRuntimeState = ConfigurationRuntimeState.UNINITIALIZED
        self._reload_count: int = 0

    @property
    def source_manager(self) -> ConfigurationSourceManager:
        """Get the underlying ConfigurationSourceManager instance."""
        with self._lock:
            return self._source_manager

    def initialize(self) -> ConfigurationRuntimeState:
        """Initialize provider runtime state to READY."""
        with self._lock:
            if self._state == ConfigurationRuntimeState.READY:
                return self._state
            logger.info("Initializing ConfigurationProvider for environment '%s'...", self._context.environment.value)
            self._state = ConfigurationRuntimeState.INITIALIZING
            self._state = ConfigurationRuntimeState.READY
            logger.info("ConfigurationProvider initialized successfully. State -> READY.")
            return self._state

    def shutdown(self) -> ConfigurationRuntimeState:
        """Shutdown provider runtime operations to STOPPED."""
        with self._lock:
            if self._state == ConfigurationRuntimeState.STOPPED:
                return self._state
            logger.info("Shutting down ConfigurationProvider...")
            self._state = ConfigurationRuntimeState.STOPPING
            self._state = ConfigurationRuntimeState.STOPPED
            logger.info("ConfigurationProvider shutdown complete. State -> STOPPED.")
            return self._state

    def restart(self) -> ConfigurationRuntimeState:
        """Restart provider runtime operations."""
        with self._lock:
            logger.info("Restarting ConfigurationProvider...")
            self.shutdown()
            return self.initialize()

    def health(self) -> ConfigurationHealth:
        """Get health assessment snapshot of the provider and source manager."""
        with self._lock:
            sm_health = self._source_manager.health()
            is_healthy = self._state in (
                ConfigurationRuntimeState.READY,
                ConfigurationRuntimeState.INITIALIZING,
                ConfigurationRuntimeState.UNINITIALIZED,
            ) and sm_health.is_healthy
            issues = sm_health.issues if is_healthy else (f"ConfigurationProvider state is {self._state.value}.",) + sm_health.issues
            return ConfigurationHealth(
                is_healthy=is_healthy,
                state=self._state,
                issues=issues,
                checked_at=datetime.now(timezone.utc),
            )

    def statistics(self) -> ConfigurationStatistics:
        """Get statistics metrics snapshot of the provider and sources."""
        with self._lock:
            sm_stats = self._source_manager.statistics()
            metrics = {
                "reload_count": float(self._reload_count),
            }
            metrics.update(sm_stats.metrics)
            return ConfigurationStatistics(
                total_properties_loaded=sm_stats.total_properties_loaded,
                active_sources_count=sm_stats.active_sources_count,
                profiles_loaded_count=1,
                reload_count=self._reload_count,
                metrics=metrics,
            )

    def capabilities(self) -> ConfigurationCapabilities:
        """Get capability definitions of the provider."""
        return ConfigurationCapabilities(
            supports_dotenv=True,
            supports_json=True,
            supports_yaml=True,
            supports_environment_override=True,
            supports_remote_sources=True,
            supports_hot_reload=True,
            supports_secret_masking=True,
            supports_type_casting=True,
        )

    def diagnostics(self) -> ConfigurationDiagnostics:
        """Get resolution diagnostics snapshot."""
        with self._lock:
            stats = self.statistics()
            return ConfigurationDiagnostics(
                state=self._state,
                health=self.health(),
                statistics=stats,
                active_profile_name=self._context.environment.value.lower(),
                active_sources_count=stats.active_sources_count,
                metrics=stats.metrics,
                timestamp=datetime.now(timezone.utc),
            )

    def get_context(self) -> ConfigurationContext:
        """Get execution context snapshot."""
        with self._lock:
            return self._context
