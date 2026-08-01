"""Integration Subsystem Domain Models for Auralis (Phase 11.9).

Defines immutable Pydantic v2 models and enums representing OS operation requests,
responses, execution results, capability descriptors, execution summaries, statistics,
health status, and runtime state.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


class OperationTarget(str, Enum):
    """Target OS subsystem category."""

    FILESYSTEM = "filesystem"
    APPLICATION = "application"
    PROCESS = "process"
    DESKTOP = "desktop"
    WINDOW = "window"
    DEVICE = "device"
    SECURITY = "security"
    SYSTEM = "system"


class OperationType(str, Enum):
    """Classification of operation action types."""

    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    CONTROL = "control"
    MONITOR = "monitor"
    SECURITY_EVAL = "security_eval"


class ExecutionState(str, Enum):
    """Pipeline execution lifecycle states."""

    PENDING = "pending"
    VALIDATING = "validating"
    EVALUATING_SECURITY = "evaluating_security"
    DISPATCHING = "dispatching"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DispatchStrategy(str, Enum):
    """Strategy for dispatching operation execution."""

    DIRECT = "direct"
    SECURE = "secure"
    ASYNC = "async"
    FALLBACK = "fallback"


class OperationContext(BaseModel):
    """Immutable operation execution context."""

    model_config = ConfigDict(frozen=True)

    session_id: str = "console"
    user_id: str = "current_user"
    is_admin: bool = False
    client_ip: str = "127.0.0.1"


class OperationRequest(BaseModel):
    """Immutable unified OS operation request."""

    model_config = ConfigDict(frozen=True)

    request_id: str = ""
    target: OperationTarget = OperationTarget.SYSTEM
    capability: str = ""
    action: str = ""
    target_resource: str = ""
    parameters: Dict[str, Any] = Field(default_factory=dict)
    context: OperationContext = Field(default_factory=OperationContext)


class OperationResult(BaseModel):
    """Immutable raw execution result data."""

    model_config = ConfigDict(frozen=True)

    success: bool = True
    data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    duration_ms: float = 0.0


class ExecutionSummary(BaseModel):
    """Immutable execution pipeline summary and telemetry."""

    model_config = ConfigDict(frozen=True)

    request_id: str = ""
    state: ExecutionState = ExecutionState.COMPLETED
    duration_ms: float = 0.0
    stages: List[str] = Field(default_factory=list)
    security_decision: Optional[Dict[str, Any]] = None
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class OperationResponse(BaseModel):
    """Immutable unified OS operation response."""

    model_config = ConfigDict(frozen=True)

    request_id: str = ""
    success: bool = True
    result: OperationResult = Field(default_factory=OperationResult)
    summary: ExecutionSummary = Field(default_factory=ExecutionSummary)


class CapabilityDescriptor(BaseModel):
    """Immutable capability registration descriptor."""

    model_config = ConfigDict(frozen=True)

    capability_name: str = ""
    target: OperationTarget = OperationTarget.SYSTEM
    description: str = ""
    is_enabled: bool = True
    requires_admin: bool = False
    parameters_schema: Dict[str, Any] = Field(default_factory=dict)


class ExecutionStatistics(BaseModel):
    """Immutable performance statistics for Integration Subsystem."""

    model_config = ConfigDict(frozen=True)

    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    security_denied: int = 0
    average_duration_ms: float = 0.0


class IntegrationHealth(BaseModel):
    """Immutable health status of Integration Subsystem services."""

    model_config = ConfigDict(frozen=True)

    healthy: bool = True
    status: str = "READY"
    capabilities_count: int = 0
    total_dispatches: int = 0
    uptime_seconds: float = 0.0
    details: Dict[str, Any] = Field(default_factory=dict)


class IntegrationStatus(BaseModel):
    """Immutable overall Integration Runtime status report."""

    model_config = ConfigDict(frozen=True)

    state: str = "Initializing"
    healthy: bool = True
    provider_registered: bool = False
    capabilities_registered: int = 0
    total_operations: int = 0
    uptime_seconds: float = 0.0
