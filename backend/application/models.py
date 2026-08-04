"""Application Layer Domain Models (Phase 14.1).

Defines immutable Pydantic v2 models and enums representing application state,
configuration, capabilities, health metrics, statistics, execution context,
runtime registrations, and system diagnostics.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional, Tuple
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


class ApplicationLifecycleState(str, Enum):
    """Lifecycle states for the application runtime."""

    UNINITIALIZED = "UNINITIALIZED"
    BOOTSTRAPPING = "BOOTSTRAPPING"
    REGISTERING = "REGISTERING"
    VALIDATING = "VALIDATING"
    INITIALIZING = "INITIALIZING"
    READY = "READY"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    DEGRADED = "DEGRADED"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    SHUTDOWN = "SHUTDOWN"
    FAILED = "FAILED"


class ApplicationState(BaseModel):
    """Immutable model representing the overall application state snapshot."""

    model_config = ConfigDict(frozen=True)

    status: ApplicationLifecycleState = ApplicationLifecycleState.UNINITIALIZED
    is_active: bool = False
    is_healthy: bool = True
    start_time: Optional[datetime] = None
    uptime_seconds: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ApplicationConfiguration(BaseModel):
    """Immutable application configuration options."""

    model_config = ConfigDict(frozen=True)

    app_name: str = "Auralis"
    version: str = "1.0.0"
    environment: str = "production"
    debug: bool = False
    config_path: Optional[str] = None
    settings: Dict[str, Any] = Field(default_factory=dict)


class ApplicationCapabilities(BaseModel):
    """Immutable model declaring supported application capabilities."""

    model_config = ConfigDict(frozen=True)

    voice_enabled: bool = True
    ai_reasoning_enabled: bool = True
    planning_enabled: bool = True
    os_automation_enabled: bool = True
    background_tasks_enabled: bool = True
    supports_restart: bool = True
    supports_bootstrap: bool = True
    supports_runtime_registration: bool = True
    supports_health_checks: bool = True
    supports_validation: bool = True
    supports_shutdown: bool = True
    custom_capabilities: Dict[str, bool] = Field(default_factory=dict)


class ApplicationHealth(BaseModel):
    """Immutable model representing health status of the application and its subsystems."""

    model_config = ConfigDict(frozen=True)

    is_healthy: bool = True
    state: ApplicationLifecycleState = ApplicationLifecycleState.UNINITIALIZED
    subsystem_health: Dict[str, bool] = Field(default_factory=dict)
    issues: Tuple[str, ...] = Field(default_factory=tuple)
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ApplicationStatistics(BaseModel):
    """Immutable model containing aggregate runtime metrics and statistics."""

    model_config = ConfigDict(frozen=True)

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    active_sessions: int = 0
    registered_runtimes_count: int = 0
    metrics: Dict[str, float] = Field(default_factory=dict)


class ApplicationContext(BaseModel):
    """Immutable execution context for the application runtime."""

    model_config = ConfigDict(frozen=True)

    app_id: str = ""
    session_id: str = ""
    working_directory: str = ""
    environment_variables: Dict[str, str] = Field(default_factory=dict)
    context_data: Dict[str, Any] = Field(default_factory=dict)


class RuntimeRegistration(BaseModel):
    """Immutable metadata record for sub-system runtime registration."""

    model_config = ConfigDict(frozen=True)

    name: str
    version: str = "1.0.0"
    is_active: bool = True
    dependencies: Tuple[str, ...] = Field(default_factory=tuple)
    registered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ApplicationDiagnostics(BaseModel):
    """Immutable diagnostic information for troubleshooting and telemetry."""

    model_config = ConfigDict(frozen=True)

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    thread_count: int = 0
    diagnostic_messages: Tuple[str, ...] = Field(default_factory=tuple)
    extra_info: Dict[str, Any] = Field(default_factory=dict)
