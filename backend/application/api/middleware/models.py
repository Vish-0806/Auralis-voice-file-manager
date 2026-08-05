"""API Middleware Models (Phase 15.3).

Defines immutable Pydantic v2 domain models and enums for the provider-independent
API Middleware Runtime, including middlewares, context, execution records,
execution results, capabilities, health, statistics, and diagnostics.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional, Tuple

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


class MiddlewareStage(str, Enum):
    """Execution stages for API request middleware."""

    BEFORE_REQUEST = "BEFORE_REQUEST"
    AROUND_REQUEST = "AROUND_REQUEST"
    AFTER_REQUEST = "AFTER_REQUEST"
    ERROR_HANDLER = "ERROR_HANDLER"


class MiddlewareState(str, Enum):
    """Operational states for individual API middleware components."""

    REGISTERED = "REGISTERED"
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"


class MiddlewareRuntimeState(str, Enum):
    """Lifecycle states for the middleware runtime."""

    UNINITIALIZED = "UNINITIALIZED"
    INITIALIZING = "INITIALIZING"
    READY = "READY"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"


class ApiMiddleware(BaseModel):
    """Immutable representation of registered API middleware."""

    model_config = ConfigDict(frozen=True)

    middleware_id: str
    name: str
    stage: MiddlewareStage = MiddlewareStage.BEFORE_REQUEST
    priority: int = 100
    state: MiddlewareState = MiddlewareState.ENABLED
    description: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)
    registered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MiddlewareContext(BaseModel):
    """Immutable context object passed through middleware pipelines."""

    model_config = ConfigDict(frozen=True)

    context_id: str
    route_id: str = ""
    path: str = ""
    stage: MiddlewareStage = MiddlewareStage.BEFORE_REQUEST
    state_data: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MiddlewareExecution(BaseModel):
    """Immutable execution telemetry record for a single middleware invocation."""

    model_config = ConfigDict(frozen=True)

    execution_id: str
    middleware_id: str
    stage: MiddlewareStage
    status: str = "SUCCESS"
    duration_ms: float = 0.0
    executed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    error_message: Optional[str] = None


class MiddlewareResult(BaseModel):
    """Immutable result of executing a pipeline of middleware for a stage."""

    model_config = ConfigDict(frozen=True)

    is_success: bool = True
    stage: MiddlewareStage = MiddlewareStage.BEFORE_REQUEST
    context: Optional[MiddlewareContext] = None
    executions: Tuple[MiddlewareExecution, ...] = Field(default_factory=tuple)
    error_message: Optional[str] = None
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MiddlewareCapabilities(BaseModel):
    """Immutable model declaring supported middleware runtime capabilities."""

    model_config = ConfigDict(frozen=True)

    supports_before_request: bool = True
    supports_around_request: bool = True
    supports_after_request: bool = True
    supports_error_handlers: bool = True
    supports_priority_ordering: bool = True
    supports_enable_disable: bool = True
    custom_capabilities: Dict[str, bool] = Field(default_factory=dict)


class MiddlewareStatistics(BaseModel):
    """Immutable aggregate metrics and statistics for the middleware runtime."""

    model_config = ConfigDict(frozen=True)

    total_middlewares: int = 0
    enabled_middlewares: int = 0
    disabled_middlewares: int = 0
    total_executions: int = 0
    failed_executions: int = 0
    metrics: Dict[str, Any] = Field(default_factory=dict)


class MiddlewareHealth(BaseModel):
    """Immutable health status evaluation of the middleware runtime."""

    model_config = ConfigDict(frozen=True)

    is_healthy: bool = True
    state: MiddlewareRuntimeState = MiddlewareRuntimeState.UNINITIALIZED
    details: Dict[str, Any] = Field(default_factory=dict)
    issues: Tuple[str, ...] = Field(default_factory=tuple)
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MiddlewareDiagnostics(BaseModel):
    """Immutable diagnostic information for troubleshooting and telemetry."""

    model_config = ConfigDict(frozen=True)

    state: MiddlewareRuntimeState = MiddlewareRuntimeState.UNINITIALIZED
    registered_count: int = 0
    enabled_count: int = 0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    thread_count: int = 0
    diagnostic_messages: Tuple[str, ...] = Field(default_factory=tuple)
    details: Dict[str, Any] = Field(default_factory=dict)
