"""Configuration Provider (Phase 14.3.1).

Thread-safe production configuration provider runtime coordinating configuration state,
context, capabilities, health reporting, statistics, and diagnostics snapshots.
"""

from datetime import datetime, timezone
import logging
from threading import RLock
from typing import Dict, Optional

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
    """Production ConfigurationProvider runtime executing configuration state & health reporting."""

    def __init__(self, config_context: Optional[ConfigurationContext] = None) -> None:
        """Initialize ConfigurationProvider using Constructor Dependency Injection.

        Args:
            config_context: Optional ConfigurationContext snapshot.
        """
        self._lock = RLock()
        self._context = config_context or ConfigurationContext()
        self._state: ConfigurationRuntimeState = ConfigurationRuntimeState.UNINITIALIZED
        self._reload_count: int = 0
        self._total_properties_loaded: int = 0
        self._active_sources_count: int = 0
        self._profiles_loaded_count: int = 1

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
        """Get health assessment snapshot of the provider."""
        with self._lock:
            is_healthy = self._state in (
                ConfigurationRuntimeState.READY,
                ConfigurationRuntimeState.INITIALIZING,
                ConfigurationRuntimeState.UNINITIALIZED,
            )
            issues = () if is_healthy else (f"ConfigurationProvider state is {self._state.value}.",)
            return ConfigurationHealth(
                is_healthy=is_healthy,
                state=self._state,
                issues=issues,
                checked_at=datetime.now(timezone.utc),
            )

    def statistics(self) -> ConfigurationStatistics:
        """Get statistics metrics snapshot of the provider."""
        with self._lock:
            return ConfigurationStatistics(
                total_properties_loaded=self._total_properties_loaded,
                active_sources_count=self._active_sources_count,
                profiles_loaded_count=self._profiles_loaded_count,
                reload_count=self._reload_count,
                metrics={
                    "total_properties_loaded": float(self._total_properties_loaded),
                    "active_sources_count": float(self._active_sources_count),
                    "reload_count": float(self._reload_count),
                },
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
            return ConfigurationDiagnostics(
                state=self._state,
                health=self.health(),
                statistics=self.statistics(),
                active_profile_name=self._context.environment.value.lower(),
                active_sources_count=self._active_sources_count,
                metrics={
                    "reload_count": float(self._reload_count),
                    "active_sources": float(self._active_sources_count),
                },
                timestamp=datetime.now(timezone.utc),
            )

    def get_context(self) -> ConfigurationContext:
        """Get execution context snapshot."""
        with self._lock:
            return self._context
