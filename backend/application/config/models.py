"""Configuration Runtime Domain Models (Phase 14.3.4).

Defines immutable Pydantic v2 domain models and enums representing configuration runtime states,
source types, profile types, capabilities, health metrics, statistics, configuration context,
profiles, sources, entries, snapshots, definitions, constraints, schemas, validation results,
resolution results, feature flags, evaluations, profile definitions, and diagnostics snapshots.
"""

from datetime import datetime, timezone
from enum import Enum, IntEnum
from typing import Any, Callable, Dict, Optional, Tuple
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


class ConfigurationRuntimeState(str, Enum):
    """Lifecycle states for the configuration runtime."""

    UNINITIALIZED = "UNINITIALIZED"
    INITIALIZING = "INITIALIZING"
    READY = "READY"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"


class ConfigurationSourceType(str, Enum):
    """Configuration source provider types."""

    ENVIRONMENT = "ENVIRONMENT"
    DOTENV = "DOTENV"
    JSON = "JSON"
    YAML = "YAML"
    MEMORY = "MEMORY"
    REMOTE = "REMOTE"


class ConfigurationProfileType(str, Enum):
    """Deployment profile types."""

    DEVELOPMENT = "DEVELOPMENT"
    TESTING = "TESTING"
    STAGING = "STAGING"
    PRODUCTION = "PRODUCTION"


class SourcePriority(IntEnum):
    """Default numerical priority levels for configuration sources (higher overrides lower)."""

    MEMORY = 500
    ENVIRONMENT = 400
    DOTENV = 300
    JSON = 200
    YAML = 100
    REMOTE = 50
    DEFAULT = 0


class ConfigurationState(BaseModel):
    """Immutable model representing current configuration runtime state."""

    model_config = ConfigDict(frozen=True)

    state: ConfigurationRuntimeState = ConfigurationRuntimeState.UNINITIALIZED
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ConfigurationCapabilities(BaseModel):
    """Immutable model declaring supported configuration capabilities."""

    model_config = ConfigDict(frozen=True)

    supports_dotenv: bool = True
    supports_json: bool = True
    supports_yaml: bool = True
    supports_environment_override: bool = True
    supports_remote_sources: bool = True
    supports_hot_reload: bool = True
    supports_secret_masking: bool = True
    supports_type_casting: bool = True
    custom_capabilities: Dict[str, bool] = Field(default_factory=dict)


class ConfigurationHealth(BaseModel):
    """Immutable model representing configuration runtime health assessment."""

    model_config = ConfigDict(frozen=True)

    is_healthy: bool = True
    state: ConfigurationRuntimeState = ConfigurationRuntimeState.UNINITIALIZED
    issues: Tuple[str, ...] = Field(default_factory=tuple)
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ConfigurationStatistics(BaseModel):
    """Immutable model containing configuration runtime statistics and metrics."""

    model_config = ConfigDict(frozen=True)

    total_properties_loaded: int = 0
    active_sources_count: int = 0
    profiles_loaded_count: int = 0
    reload_count: int = 0
    metrics: Dict[str, float] = Field(default_factory=dict)


class ResolutionStatistics(BaseModel):
    """Immutable metrics model for configuration resolution engine."""

    model_config = ConfigDict(frozen=True)

    resolution_count: int = 0
    conversion_count: int = 0
    default_applications: int = 0
    type_mismatches: int = 0


class ValidationStatistics(BaseModel):
    """Immutable metrics model for configuration validation engine."""

    model_config = ConfigDict(frozen=True)

    validation_count: int = 0
    successful_validations: int = 0
    failed_validations: int = 0


class ProfileStatistics(BaseModel):
    """Immutable metrics model for configuration profile management."""

    model_config = ConfigDict(frozen=True)

    registered_profiles_count: int = 0
    active_profile_switches_count: int = 0
    inheritance_resolutions_count: int = 0


class ProfileHealth(BaseModel):
    """Immutable health model for configuration profile subsystem."""

    model_config = ConfigDict(frozen=True)

    is_healthy: bool = True
    active_profile_name: str = "development"
    issues: Tuple[str, ...] = Field(default_factory=tuple)
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class FeatureStatistics(BaseModel):
    """Immutable metrics model for feature flag subsystem."""

    model_config = ConfigDict(frozen=True)

    total_features: int = 0
    enabled_features: int = 0
    evaluations_count: int = 0
    cache_hits: int = 0


class FeatureHealth(BaseModel):
    """Immutable health model for feature flag subsystem."""

    model_config = ConfigDict(frozen=True)

    is_healthy: bool = True
    issues: Tuple[str, ...] = Field(default_factory=tuple)
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ConfigurationContext(BaseModel):
    """Immutable model snapshotting runtime execution context for configuration."""

    model_config = ConfigDict(frozen=True)

    environment: ConfigurationProfileType = ConfigurationProfileType.DEVELOPMENT
    app_name: str = "Auralis"
    instance_id: str = "default_instance"
    context_data: Dict[str, Any] = Field(default_factory=dict)


class ConfigurationProfile(BaseModel):
    """Immutable model representing a deployment configuration profile."""

    model_config = ConfigDict(frozen=True)

    profile_type: ConfigurationProfileType = ConfigurationProfileType.DEVELOPMENT
    profile_name: str = "development"
    active: bool = True
    priority: int = 100


class ConfigurationProfileDefinition(BaseModel):
    """Immutable model defining a configuration profile with overrides and inheritance."""

    model_config = ConfigDict(frozen=True)

    profile_type: ConfigurationProfileType = ConfigurationProfileType.DEVELOPMENT
    profile_name: str = "development"
    parent_profile_name: Optional[str] = None
    overrides: Dict[str, Any] = Field(default_factory=dict)
    active: bool = True
    priority: int = 100


class ConfigurationProfileSnapshot(BaseModel):
    """Immutable snapshot of active profile and merged overrides."""

    model_config = ConfigDict(frozen=True)

    active_profile_name: str = "development"
    parent_profile_name: Optional[str] = None
    merged_values: Dict[str, Any] = Field(default_factory=dict)
    active_features_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class FeatureFlag(BaseModel):
    """Immutable model defining a feature flag configuration."""

    model_config = ConfigDict(frozen=True)

    feature_name: str
    enabled: bool = True
    description: str = ""
    rollout_percentage: float = 100.0
    allowed_profiles: Tuple[ConfigurationProfileType, ...] = Field(default_factory=tuple)
    allowed_environments: Tuple[str, ...] = Field(default_factory=tuple)
    dependencies: Tuple[str, ...] = Field(default_factory=tuple)


class FeatureEvaluation(BaseModel):
    """Immutable result of a feature flag evaluation."""

    model_config = ConfigDict(frozen=True)

    feature_name: str
    enabled: bool
    reason: str
    profile_name: str = "development"
    environment_name: str = "development"
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ConfigurationSource(BaseModel):
    """Immutable model representing a registered configuration source metadata."""

    model_config = ConfigDict(frozen=True)

    source_type: ConfigurationSourceType = ConfigurationSourceType.MEMORY
    source_name: str = "default_memory"
    enabled: bool = True
    priority: int = int(SourcePriority.MEMORY)


class SourceRegistration(BaseModel):
    """Immutable record for a registered configuration source."""

    model_config = ConfigDict(frozen=True)

    source_name: str
    source_type: ConfigurationSourceType
    priority: int = 100
    enabled: bool = True
    registered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SourceStatistics(BaseModel):
    """Immutable metrics model for an individual configuration source."""

    model_config = ConfigDict(frozen=True)

    total_keys: int = 0
    lookups_count: int = 0
    hits_count: int = 0
    misses_count: int = 0
    metrics: Dict[str, float] = Field(default_factory=dict)


class SourceHealth(BaseModel):
    """Immutable health assessment for an individual configuration source."""

    model_config = ConfigDict(frozen=True)

    is_healthy: bool = True
    source_name: str = ""
    issues: Tuple[str, ...] = Field(default_factory=tuple)
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ConfigurationEntry(BaseModel):
    """Immutable record for a single resolved configuration entry."""

    model_config = ConfigDict(frozen=True)

    key: str
    value: Any
    source_name: str
    source_type: ConfigurationSourceType
    priority: int
    loaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ConfigurationSnapshot(BaseModel):
    """Immutable merged snapshot of all active configuration values."""

    model_config = ConfigDict(frozen=True)

    values: Dict[str, Any] = Field(default_factory=dict)
    sources_metadata: Tuple[Dict[str, Any], ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ConfigurationError(BaseModel):
    """Immutable model representing a configuration error or validation failure."""

    model_config = ConfigDict(frozen=True)

    key: str
    message: str
    error_type: str = "VALIDATION_ERROR"


class ConfigurationWarning(BaseModel):
    """Immutable model representing a configuration resolution or validation warning."""

    model_config = ConfigDict(frozen=True)

    key: str
    message: str
    warning_type: str = "DEFAULT_APPLIED"


class ConfigurationConstraint(BaseModel):
    """Immutable model representing validation rules and constraints for a property."""

    model_config = ConfigDict(frozen=True)

    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    regex_pattern: Optional[str] = None
    allowed_values: Optional[Tuple[Any, ...]] = None


class ConfigurationDefinition(BaseModel):
    """Immutable model defining a single configuration schema property."""

    model_config = ConfigDict(frozen=True)

    key: str
    expected_type: Any = str
    default_value: Optional[Any] = None
    required: bool = False
    constraint: Optional[ConfigurationConstraint] = None
    description: str = ""


class ConfigurationSchema(BaseModel):
    """Immutable model representing a named collection of property definitions."""

    model_config = ConfigDict(frozen=True)

    schema_name: str
    definitions: Tuple[ConfigurationDefinition, ...] = Field(default_factory=tuple)


class ConfigurationValidationResult(BaseModel):
    """Immutable report containing validation outcome, errors, and warnings."""

    model_config = ConfigDict(frozen=True)

    is_valid: bool = True
    errors: Tuple[ConfigurationError, ...] = Field(default_factory=tuple)
    warnings: Tuple[ConfigurationWarning, ...] = Field(default_factory=tuple)
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ConfigurationResolutionResult(BaseModel):
    """Immutable report containing property resolution, type conversions, and defaults."""

    model_config = ConfigDict(frozen=True)

    resolved_values: Dict[str, Any] = Field(default_factory=dict)
    converted_keys: Tuple[str, ...] = Field(default_factory=tuple)
    defaulted_keys: Tuple[str, ...] = Field(default_factory=tuple)
    missing_required_keys: Tuple[str, ...] = Field(default_factory=tuple)
    errors: Tuple[ConfigurationError, ...] = Field(default_factory=tuple)
    resolved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ConfigurationDiagnostics(BaseModel):
    """Immutable model containing configuration runtime resolution diagnostics."""

    model_config = ConfigDict(frozen=True)

    state: ConfigurationRuntimeState = ConfigurationRuntimeState.UNINITIALIZED
    health: ConfigurationHealth = Field(default_factory=ConfigurationHealth)
    statistics: ConfigurationStatistics = Field(default_factory=ConfigurationStatistics)
    resolution_statistics: ResolutionStatistics = Field(default_factory=ResolutionStatistics)
    validation_statistics: ValidationStatistics = Field(default_factory=ValidationStatistics)
    profile_statistics: ProfileStatistics = Field(default_factory=ProfileStatistics)
    feature_statistics: FeatureStatistics = Field(default_factory=FeatureStatistics)
    active_profile_name: str = "development"
    active_sources_count: int = 0
    metrics: Dict[str, float] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
