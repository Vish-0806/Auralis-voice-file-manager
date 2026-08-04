"""Configuration Source Manager (Phase 14.3.5).

Coordinates registered configuration sources, profile overrides, feature flag evaluation,
secret management, type conversions, constraint validations, and diagnostics reports.
"""

from datetime import datetime, timezone
import logging
from threading import RLock
from typing import Any, Dict, List, Optional, Tuple

from backend.application.config.configuration_resolver import ConfigurationResolver
from backend.application.config.configuration_schema import ConfigurationSchemaManager
from backend.application.config.configuration_validator import ConfigurationValidator
from backend.application.config.dotenv_source import DotEnvConfigurationSource
from backend.application.config.environment_source import EnvironmentConfigurationSource
from backend.application.config.feature_flag_manager import FeatureFlagManager
from backend.application.config.interfaces import IConfigurationManager, IConfigurationSource
from backend.application.config.memory_source import MemoryConfigurationSource
from backend.application.config.models import (
    ConfigurationDiagnostics,
    ConfigurationEntry,
    ConfigurationHealth,
    ConfigurationProfileDefinition,
    ConfigurationResolutionResult,
    ConfigurationRuntimeState,
    ConfigurationSchema,
    ConfigurationSnapshot,
    ConfigurationSourceType,
    ConfigurationStatistics,
    ConfigurationValidationResult,
    FeatureEvaluation,
    FeatureFlag,
    SecretPolicy,
    SecretSnapshot,
    SecretType,
)
from backend.application.config.profile_manager import ProfileManager
from backend.application.config.secret_manager import SecretManager
from backend.application.config.source_registry import SourceRegistry

logger = logging.getLogger(__name__)


class ConfigurationSourceManager(IConfigurationManager):
    """Production priority-based configuration source resolution, profiles, feature flags, secret management, conversion, and validation manager."""

    def __init__(
        self,
        registry: Optional[SourceRegistry] = None,
        schema_manager: Optional[ConfigurationSchemaManager] = None,
        resolver: Optional[ConfigurationResolver] = None,
        validator: Optional[ConfigurationValidator] = None,
        profile_manager: Optional[ProfileManager] = None,
        feature_manager: Optional[FeatureFlagManager] = None,
        secret_manager: Optional[SecretManager] = None,
    ) -> None:
        """Initialize ConfigurationSourceManager using Constructor Dependency Injection."""
        self._lock = RLock()
        self._registry = registry or SourceRegistry()
        self._schema_manager = schema_manager or ConfigurationSchemaManager()
        self._resolver = resolver or ConfigurationResolver(schema_manager=self._schema_manager)
        self._validator = validator or ConfigurationValidator(schema_manager=self._schema_manager)
        self._profile_manager = profile_manager or ProfileManager()
        self._feature_manager = feature_manager or FeatureFlagManager()
        self._secret_manager = secret_manager or SecretManager()

        # Register default sources if registry is empty
        if self._registry.count() == 0:
            self._registry.register_source(MemoryConfigurationSource())
            self._registry.register_source(EnvironmentConfigurationSource())
            self._registry.register_source(DotEnvConfigurationSource())

        self._lookups_count: int = 0
        self._hits_count: int = 0
        self._misses_count: int = 0

    @property
    def registry(self) -> SourceRegistry:
        """Get underlying SourceRegistry."""
        with self._lock:
            return self._registry

    @property
    def schema_manager(self) -> ConfigurationSchemaManager:
        """Get underlying ConfigurationSchemaManager."""
        with self._lock:
            return self._schema_manager

    @property
    def resolver(self) -> ConfigurationResolver:
        """Get underlying ConfigurationResolver."""
        with self._lock:
            return self._resolver

    @property
    def validator(self) -> ConfigurationValidator:
        """Get underlying ConfigurationValidator."""
        with self._lock:
            return self._validator

    @property
    def profile_manager(self) -> ProfileManager:
        """Get underlying ProfileManager."""
        with self._lock:
            return self._profile_manager

    @property
    def feature_manager(self) -> FeatureFlagManager:
        """Get underlying FeatureFlagManager."""
        with self._lock:
            return self._feature_manager

    @property
    def secret_manager(self) -> SecretManager:
        """Get underlying SecretManager."""
        with self._lock:
            return self._secret_manager

    def register_secret(
        self,
        secret_name: str,
        raw_value: str,
        secret_type: SecretType = SecretType.PASSWORD,
        policy: Optional[SecretPolicy] = None,
    ) -> bool:
        """Register a secret configuration value safely."""
        with self._lock:
            return self._secret_manager.register_secret(secret_name, raw_value, secret_type=secret_type, policy=policy)

    def get_secret(self, secret_name: str) -> Optional[str]:
        """Get raw secret value if allowed by policy."""
        with self._lock:
            return self._secret_manager.get_secret(secret_name)

    def get_redacted_secret(self, secret_name: str) -> Optional[str]:
        """Get redacted/masked secret value for export or UI rendering."""
        with self._lock:
            return self._secret_manager.get_redacted_secret(secret_name)

    def create_secret_snapshot(self) -> SecretSnapshot:
        """Create an immutable redacted secret snapshot."""
        with self._lock:
            return self._secret_manager.create_snapshot()

    def activate_profile(self, profile_name: str) -> bool:
        """Activate runtime configuration profile."""
        with self._lock:
            return self._profile_manager.activate_profile(profile_name)

    def get_active_profile(self) -> ConfigurationProfileDefinition:
        """Get currently active profile definition."""
        with self._lock:
            return self._profile_manager.get_active_profile()

    def register_profile(self, profile: ConfigurationProfileDefinition) -> bool:
        """Register a configuration profile."""
        with self._lock:
            return self._profile_manager.register_profile(profile)

    def is_feature_enabled(self, feature_name: str) -> bool:
        """Evaluate if feature flag is enabled."""
        with self._lock:
            active_p = self.get_active_profile().profile_name
            return self._feature_manager.is_enabled(feature_name, active_profile_name=active_p)

    def evaluate_feature(self, feature_name: str) -> FeatureEvaluation:
        """Get detailed FeatureEvaluation report for feature flag."""
        with self._lock:
            active_p = self.get_active_profile().profile_name
            return self._feature_manager.evaluate(feature_name, active_profile_name=active_p)

    def register_feature(self, feature: FeatureFlag) -> bool:
        """Register a feature flag."""
        with self._lock:
            return self._feature_manager.register_feature(feature)

    def register_schema(self, schema: ConfigurationSchema) -> bool:
        """Register a configuration schema."""
        with self._lock:
            return self._schema_manager.register_schema(schema)

    def register_source(self, source: IConfigurationSource) -> bool:
        """Register a configuration source."""
        with self._lock:
            return self._registry.register_source(source)

    def unregister_source(self, source_name: str) -> bool:
        """Unregister a configuration source by name."""
        with self._lock:
            return self._registry.unregister_source(source_name)

    def get_entry(self, key: str) -> Optional[ConfigurationEntry]:
        """Get detailed ConfigurationEntry with source metadata for the highest priority source matching key."""
        with self._lock:
            self._lookups_count += 1

            # Check registered secrets first (high security priority)
            redacted_sec = self._secret_manager.get_redacted_secret(key)
            if redacted_sec is not None:
                self._hits_count += 1
                return ConfigurationEntry(
                    key=key,
                    value=redacted_sec,
                    source_name="secret_manager",
                    source_type=ConfigurationSourceType.MEMORY,
                    priority=600,
                    loaded_at=datetime.now(timezone.utc),
                )

            # Check sources next
            sorted_sources = self._registry.sort_sources()
            for source in sorted_sources:
                if source.enabled and source.contains(key):
                    val = source.get(key)
                    self._hits_count += 1
                    return ConfigurationEntry(
                        key=key,
                        value=val,
                        source_name=source.source_name,
                        source_type=source.source_type,
                        priority=source.priority,
                        loaded_at=datetime.now(timezone.utc),
                    )

            # Check profile overrides next
            prof_overrides = self._profile_manager.resolve_profile()
            if key in prof_overrides:
                self._hits_count += 1
                active_p = self.get_active_profile().profile_name
                return ConfigurationEntry(
                    key=key,
                    value=prof_overrides[key],
                    source_name=f"profile:{active_p}",
                    source_type=ConfigurationSourceType.MEMORY,
                    priority=250,
                    loaded_at=datetime.now(timezone.utc),
                )

            self._misses_count += 1
            return None

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get configuration value for key from secrets, sources, or profile overrides."""
        entry = self.get_entry(key)
        return entry.value if entry is not None else default

    def resolve(self, key: str, expected_type: Optional[Any] = None, default: Optional[Any] = None) -> Any:
        """Resolve configuration value with type conversion and schema default fallback."""
        with self._lock:
            raw_val = self.get(key)
            return self._resolver.resolve_key(key, raw_val, expected_type=expected_type, default=default)

    def resolve_all(self) -> ConfigurationResolutionResult:
        """Resolve all properties against registered schemas with type conversion."""
        with self._lock:
            all_raw = self.get_all()
            return self._resolver.resolve_all(all_raw)

    def validate(self, schema: Optional[ConfigurationSchema] = None) -> ConfigurationValidationResult:
        """Validate current configuration values against registered schemas."""
        with self._lock:
            resolved_result = self.resolve_all()
            return self._validator.validate(resolved_result.resolved_values, schema=schema)

    def has(self, key: str) -> bool:
        """Check if a configuration key exists in secrets, sources, or profile overrides."""
        with self._lock:
            if self._secret_manager.store.contains(key):
                return True
            for source in self._registry.sort_sources():
                if source.enabled and source.contains(key):
                    return True
            prof_overrides = self._profile_manager.resolve_profile()
            return key in prof_overrides

    def get_all(self) -> Dict[str, Any]:
        """Get all merged configuration key-value pairs (redacted values for secrets)."""
        with self._lock:
            merged: Dict[str, Any] = {}

            # Apply profile overrides first
            prof_overrides = self._profile_manager.resolve_profile()
            merged.update(prof_overrides)

            # Apply sources from lowest to highest priority
            sources = list(self._registry.sort_sources())
            sources.reverse()

            for source in sources:
                if source.enabled:
                    for k, v in source.items():
                        merged[k] = v

            # Secrets override all values with redacted representation
            for sec_name in self._secret_manager.store.list_secret_names():
                redacted = self._secret_manager.get_redacted_secret(sec_name)
                if redacted is not None:
                    merged[sec_name] = redacted

            return merged

    def create_snapshot(self) -> ConfigurationSnapshot:
        """Create an immutable merged configuration snapshot."""
        with self._lock:
            merged_values = self.get_all()
            sources_meta: List[Dict[str, Any]] = []

            for source in self._registry.sort_sources():
                sources_meta.append(
                    {
                        "source_name": source.source_name,
                        "source_type": source.source_type.value,
                        "priority": source.priority,
                        "enabled": source.enabled,
                        "total_keys": len(source.keys()),
                    }
                )

            return ConfigurationSnapshot(
                values=merged_values,
                sources_metadata=tuple(sources_meta),
                created_at=datetime.now(timezone.utc),
            )

    def health(self) -> ConfigurationHealth:
        """Get health assessment of the source manager and registered components."""
        with self._lock:
            issues: List[str] = []
            all_healthy = True

            for source in self._registry.list_sources():
                s_health = source.health()
                if not s_health.is_healthy:
                    all_healthy = False
                    issues.extend(s_health.issues)

            prof_health = self._profile_manager.health()
            if not prof_health.is_healthy:
                all_healthy = False
                issues.extend(prof_health.issues)

            feat_health = self._feature_manager.health()
            if not feat_health.is_healthy:
                all_healthy = False
                issues.extend(feat_health.issues)

            sec_health = self._secret_manager.health()
            if not sec_health.is_healthy:
                all_healthy = False
                issues.extend(sec_health.issues)

            val_res = self.validate()
            if not val_res.is_valid:
                all_healthy = False
                for err in val_res.errors:
                    issues.append(f"Validation Error [{err.key}]: {err.message}")

            return ConfigurationHealth(
                is_healthy=all_healthy,
                state=ConfigurationRuntimeState.READY,
                issues=tuple(issues),
                checked_at=datetime.now(timezone.utc),
            )

    def statistics(self) -> ConfigurationStatistics:
        """Get aggregated configuration statistics."""
        with self._lock:
            all_values = self.get_all()
            res_stats = self._resolver.statistics()
            val_stats = self._validator.statistics()
            prof_stats = self._profile_manager.statistics()
            feat_stats = self._feature_manager.statistics()
            sec_stats = self._secret_manager.statistics()

            metrics = {
                "total_properties_loaded": float(len(all_values)),
                "active_sources_count": float(self._registry.count()),
                "lookups_count": float(self._lookups_count),
                "hits_count": float(self._hits_count),
                "misses_count": float(self._misses_count),
                "conversions_count": float(res_stats.conversion_count),
                "defaults_count": float(res_stats.default_applications),
                "validations_count": float(val_stats.validation_count),
                "profiles_count": float(prof_stats.registered_profiles_count),
                "features_count": float(feat_stats.total_features),
                "secrets_count": float(sec_stats.registered_secret_count),
            }

            return ConfigurationStatistics(
                total_properties_loaded=len(all_values),
                active_sources_count=self._registry.count(),
                profiles_loaded_count=prof_stats.registered_profiles_count,
                reload_count=0,
                metrics=metrics,
            )

    def diagnostics(self) -> ConfigurationDiagnostics:
        """Get detailed configuration source manager diagnostics."""
        with self._lock:
            return ConfigurationDiagnostics(
                state=ConfigurationRuntimeState.READY,
                health=self.health(),
                statistics=self.statistics(),
                resolution_statistics=self._resolver.statistics(),
                validation_statistics=self._validator.statistics(),
                profile_statistics=self._profile_manager.statistics(),
                feature_statistics=self._feature_manager.statistics(),
                secret_statistics=self._secret_manager.statistics(),
                active_profile_name=self.get_active_profile().profile_name,
                active_sources_count=self._registry.count(),
                metrics={
                    "lookups": float(self._lookups_count),
                    "hits": float(self._hits_count),
                    "misses": float(self._misses_count),
                },
                timestamp=datetime.now(timezone.utc),
            )
