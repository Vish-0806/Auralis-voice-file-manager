"""Configuration Provider (Phase 14.3.5).

Thread-safe production configuration provider runtime coordinating configuration state,
sources, resolution, validation, profiles, feature flags, secret management, context, capabilities, health reporting, statistics, and diagnostics snapshots.
"""

from datetime import datetime, timezone
import logging
from threading import RLock
from typing import Any, Dict, Optional

from backend.application.config.configuration_source_manager import ConfigurationSourceManager
from backend.application.config.interfaces import IConfigurationProvider
from backend.application.config.models import (
    ConfigurationCapabilities,
    ConfigurationContext,
    ConfigurationDiagnostics,
    ConfigurationHealth,
    ConfigurationProfileDefinition,
    ConfigurationProfileType,
    ConfigurationResolutionResult,
    ConfigurationRuntimeState,
    ConfigurationSchema,
    ConfigurationStatistics,
    ConfigurationValidationResult,
    FeatureEvaluation,
    FeatureFlag,
    SecretPolicy,
    SecretSnapshot,
    SecretType,
)

logger = logging.getLogger(__name__)


class ConfigurationProvider(IConfigurationProvider):
    """Production ConfigurationProvider runtime executing configuration state, source, resolution, validation, profiles, feature flags, and secret management."""

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

    def register_secret(
        self,
        secret_name: str,
        raw_value: str,
        secret_type: SecretType = SecretType.PASSWORD,
        policy: Optional[SecretPolicy] = None,
    ) -> bool:
        """Register a secret configuration value safely."""
        with self._lock:
            return self._source_manager.register_secret(secret_name, raw_value, secret_type=secret_type, policy=policy)

    def get_secret(self, secret_name: str) -> Optional[str]:
        """Get raw secret value if allowed by policy."""
        with self._lock:
            return self._source_manager.get_secret(secret_name)

    def get_redacted_secret(self, secret_name: str) -> Optional[str]:
        """Get redacted/masked secret value for export or UI rendering."""
        with self._lock:
            return self._source_manager.get_redacted_secret(secret_name)

    def create_secret_snapshot(self) -> SecretSnapshot:
        """Create an immutable redacted secret snapshot."""
        with self._lock:
            return self._source_manager.create_secret_snapshot()

    def activate_profile(self, profile_name: str) -> bool:
        """Activate runtime configuration profile."""
        with self._lock:
            return self._source_manager.activate_profile(profile_name)

    def get_active_profile(self) -> ConfigurationProfileDefinition:
        """Get currently active profile definition."""
        with self._lock:
            return self._source_manager.get_active_profile()

    def register_profile(self, profile: ConfigurationProfileDefinition) -> bool:
        """Register a configuration profile."""
        with self._lock:
            return self._source_manager.register_profile(profile)

    def is_feature_enabled(self, feature_name: str) -> bool:
        """Evaluate if feature flag is enabled."""
        with self._lock:
            return self._source_manager.is_feature_enabled(feature_name)

    def evaluate_feature(self, feature_name: str) -> FeatureEvaluation:
        """Get detailed FeatureEvaluation report for feature flag."""
        with self._lock:
            return self._source_manager.evaluate_feature(feature_name)

    def register_feature(self, feature: FeatureFlag) -> bool:
        """Register a feature flag."""
        with self._lock:
            return self._source_manager.register_feature(feature)

    def register_schema(self, schema: ConfigurationSchema) -> bool:
        """Register a configuration schema."""
        with self._lock:
            return self._source_manager.register_schema(schema)

    def resolve(self, key: str, expected_type: Optional[Any] = None, default: Optional[Any] = None) -> Any:
        """Resolve a configuration property value with type conversion and default fallback."""
        with self._lock:
            return self._source_manager.resolve(key, expected_type=expected_type, default=default)

    def resolve_all(self) -> ConfigurationResolutionResult:
        """Resolve all properties against registered schemas."""
        with self._lock:
            return self._source_manager.resolve_all()

    def validate(self, schema: Optional[ConfigurationSchema] = None) -> ConfigurationValidationResult:
        """Validate configuration values against schemas."""
        with self._lock:
            return self._source_manager.validate(schema=schema)

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
                profiles_loaded_count=sm_stats.profiles_loaded_count,
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
                resolution_statistics=self._source_manager.resolver.statistics(),
                validation_statistics=self._source_manager.validator.statistics(),
                profile_statistics=self._source_manager.profile_manager.statistics(),
                feature_statistics=self._source_manager.feature_manager.statistics(),
                secret_statistics=self._source_manager.secret_manager.statistics(),
                active_profile_name=self.get_active_profile().profile_name,
                active_sources_count=stats.active_sources_count,
                metrics=stats.metrics,
                timestamp=datetime.now(timezone.utc),
            )

    def get_context(self) -> ConfigurationContext:
        """Get execution context snapshot."""
        with self._lock:
            return self._context
