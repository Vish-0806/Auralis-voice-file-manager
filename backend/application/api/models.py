"""API Runtime Models (Phase 15.1).

Defines immutable Pydantic v2 domain models and enums for the provider-independent
API Runtime foundation, including runtime states, health, statistics, capabilities,
diagnostics, context, and configuration.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional, Tuple

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


class ApiRuntimeState(str, Enum):
    """Lifecycle states for the API runtime."""

    UNINITIALIZED = "UNINITIALIZED"
    INITIALIZING = "INITIALIZING"
    READY = "READY"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"


class ApiState(BaseModel):
    """Immutable model representing the API runtime state snapshot."""

    model_config = ConfigDict(frozen=True)

    status: ApiRuntimeState = ApiRuntimeState.UNINITIALIZED
    is_active: bool = False
    is_healthy: bool = True
    initialized_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    uptime_seconds: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ApiCapabilities(BaseModel):
    """Immutable model declaring supported API capabilities."""

    model_config = ConfigDict(frozen=True)

    supports_initialize: bool = True
    supports_shutdown: bool = True
    supports_restart: bool = True
    supports_health_checks: bool = True
    supports_statistics: bool = True
    supports_diagnostics: bool = True
    custom_capabilities: Dict[str, bool] = Field(default_factory=dict)


class ApiHealth(BaseModel):
    """Immutable model representing health status of the API runtime."""

    model_config = ConfigDict(frozen=True)

    is_healthy: bool = True
    state: ApiRuntimeState = ApiRuntimeState.UNINITIALIZED
    details: Dict[str, Any] = Field(default_factory=dict)
    issues: Tuple[str, ...] = Field(default_factory=tuple)
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ApiStatistics(BaseModel):
    """Immutable model containing aggregate API runtime metrics and statistics."""

    model_config = ConfigDict(frozen=True)

    total_initializations: int = 0
    total_restarts: int = 0
    total_shutdowns: int = 0
    active_time_seconds: float = 0.0
    metrics: Dict[str, Any] = Field(default_factory=dict)


class ApiContext(BaseModel):
    """Immutable execution context for the API runtime."""

    model_config = ConfigDict(frozen=True)

    api_id: str = "default_api"
    version: str = "1.0.0"
    environment: str = "production"
    context_data: Dict[str, Any] = Field(default_factory=dict)


class ApiConfiguration(BaseModel):
    """Immutable configuration options for the API runtime."""

    model_config = ConfigDict(frozen=True)

    title: str = "Auralis API"
    version: str = "1.0.0"
    debug: bool = False
    max_connections: int = 100
    timeout_seconds: float = 30.0
    settings: Dict[str, Any] = Field(default_factory=dict)


class ApiDiagnostics(BaseModel):
    """Immutable diagnostic information for troubleshooting and telemetry."""

    model_config = ConfigDict(frozen=True)

    state: ApiRuntimeState = ApiRuntimeState.UNINITIALIZED
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    thread_count: int = 0
    diagnostic_messages: Tuple[str, ...] = Field(default_factory=tuple)
    details: Dict[str, Any] = Field(default_factory=dict)
