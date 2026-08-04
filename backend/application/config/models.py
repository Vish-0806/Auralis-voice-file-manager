"""Configuration Runtime Domain Models (Phase 14.3.1).

Defines immutable Pydantic v2 domain models and enums representing configuration runtime states,
source types, profile types, capabilities, health metrics, statistics, configuration context,
profiles, sources, and diagnostics snapshots.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional, Tuple
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


class ConfigurationSource(BaseModel):
    """Immutable model representing a registered configuration source."""

    model_config = ConfigDict(frozen=True)

    source_type: ConfigurationSourceType = ConfigurationSourceType.MEMORY
    source_name: str = "default_memory"
    enabled: bool = True
    priority: int = 100


class ConfigurationDiagnostics(BaseModel):
    """Immutable model containing configuration runtime resolution diagnostics."""

    model_config = ConfigDict(frozen=True)

    state: ConfigurationRuntimeState = ConfigurationRuntimeState.UNINITIALIZED
    health: ConfigurationHealth = Field(default_factory=ConfigurationHealth)
    statistics: ConfigurationStatistics = Field(default_factory=ConfigurationStatistics)
    active_profile_name: str = "development"
    active_sources_count: int = 0
    metrics: Dict[str, float] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
