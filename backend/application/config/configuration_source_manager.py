"""Configuration Source Manager (Phase 14.3.3).

Coordinates registered configuration sources, resolves values based on deterministic source priority,
applies schema defaults and type conversions, performs constraint validations, and produces immutable reports.
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
from backend.application.config.interfaces import IConfigurationManager, IConfigurationSource
from backend.application.config.memory_source import MemoryConfigurationSource
from backend.application.config.models import (
    ConfigurationDiagnostics,
    ConfigurationEntry,
    ConfigurationHealth,
    ConfigurationResolutionResult,
    ConfigurationRuntimeState,
    ConfigurationSchema,
    ConfigurationSnapshot,
    ConfigurationStatistics,
    ConfigurationValidationResult,
)
from backend.application.config.source_registry import SourceRegistry

logger = logging.getLogger(__name__)


class ConfigurationSourceManager(IConfigurationManager):
    """Production priority-based configuration source resolution, conversion, and validation manager."""

    def __init__(
        self,
        registry: Optional[SourceRegistry] = None,
        schema_manager: Optional[ConfigurationSchemaManager] = None,
        resolver: Optional[ConfigurationResolver] = None,
        validator: Optional[ConfigurationValidator] = None,
    ) -> None:
        """Initialize ConfigurationSourceManager using Constructor Dependency Injection.

        Args:
            registry: Optional SourceRegistry instance.
            schema_manager: Optional ConfigurationSchemaManager instance.
            resolver: Optional ConfigurationResolver instance.
            validator: Optional ConfigurationValidator instance.
        """
        self._lock = RLock()
        self._registry = registry or SourceRegistry()
        self._schema_manager = schema_manager or ConfigurationSchemaManager()
        self._resolver = resolver or ConfigurationResolver(schema_manager=self._schema_manager)
        self._validator = validator or ConfigurationValidator(schema_manager=self._schema_manager)

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
        """Get detailed ConfigurationEntry with source metadata for the highest priority source matching key.

        Args:
            key: Configuration key string.

        Returns:
            Optional[ConfigurationEntry]: Resolved entry model or None if missing.
        """
        with self._lock:
            self._lookups_count += 1
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

            self._misses_count += 1
            return None

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get configuration value for key from the highest priority active source."""
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
        """Check if a configuration key exists in any active source."""
        with self._lock:
            for source in self._registry.sort_sources():
                if source.enabled and source.contains(key):
                    return True
            return False

    def get_all(self) -> Dict[str, Any]:
        """Get all merged configuration key-value pairs."""
        with self._lock:
            merged: Dict[str, Any] = {}
            sources = list(self._registry.sort_sources())
            sources.reverse()

            for source in sources:
                if source.enabled:
                    for k, v in source.items():
                        merged[k] = v

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
        """Get health assessment of the source manager and registered sources."""
        with self._lock:
            issues: List[str] = []
            all_healthy = True

            for source in self._registry.list_sources():
                s_health = source.health()
                if not s_health.is_healthy:
                    all_healthy = False
                    issues.extend(s_health.issues)

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

            metrics = {
                "total_properties_loaded": float(len(all_values)),
                "active_sources_count": float(self._registry.count()),
                "lookups_count": float(self._lookups_count),
                "hits_count": float(self._hits_count),
                "misses_count": float(self._misses_count),
                "conversions_count": float(res_stats.conversion_count),
                "defaults_count": float(res_stats.default_applications),
                "validations_count": float(val_stats.validation_count),
            }

            return ConfigurationStatistics(
                total_properties_loaded=len(all_values),
                active_sources_count=self._registry.count(),
                profiles_loaded_count=1,
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
                active_profile_name="development",
                active_sources_count=self._registry.count(),
                metrics={
                    "lookups": float(self._lookups_count),
                    "hits": float(self._hits_count),
                    "misses": float(self._misses_count),
                },
                timestamp=datetime.now(timezone.utc),
            )
