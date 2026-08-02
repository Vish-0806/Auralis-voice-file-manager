"""Execution Engine data models for Auralis (Phase 12.1).

Defines immutable Pydantic v2 models and enumerations representing execution lifecycle states,
requests, live context, decisions, step execution results, outcomes, statistics, and health reports.
"""

from datetime import datetime, timezone
from enum import Enum
import uuid
from typing import Any, Dict, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrEnumAdapter(str):
    """String subclass that exposes a .value property for backward compatibility."""

    @property
    def value(self) -> str:
        return str(self)


class ExecutionStatus(str, Enum):
    """Enumeration representing execution lifecycle statuses (backward-compatible)."""

    PENDING = "PENDING"
    READY = "READY"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    PAUSED = "PAUSED"
    RETRYING = "RETRYING"
    SUCCESS = "SUCCESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    TIMEOUT = "TIMEOUT"
    WAITING_FOR_CONFIRMATION = "WAITING_FOR_CONFIRMATION"
    BLOCKED = "BLOCKED"
    ROLLING_BACK = "ROLLING_BACK"


class ExecutionState(str, Enum):
    """Enumeration representing canonical execution lifecycle states."""

    PENDING = "PENDING"
    ANALYZING = "ANALYZING"
    DECIDING = "DECIDING"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    PAUSED = "PAUSED"


class DecisionType(str, Enum):
    """Types of execution strategies determined by the DecisionEngine."""

    DIRECT_EXECUTION = "DIRECT_EXECUTION"
    PLANNER_REQUIRED = "PLANNER_REQUIRED"
    AI_REQUIRED = "AI_REQUIRED"
    CLARIFICATION_REQUIRED = "CLARIFICATION_REQUIRED"
    SECURITY_REVIEW_REQUIRED = "SECURITY_REVIEW_REQUIRED"
    EXECUTE = "EXECUTE"
    SKIP = "SKIP"
    RETRY = "RETRY"
    WAIT = "WAIT"
    ASK_USER = "ASK_USER"
    USE_FALLBACK = "USE_FALLBACK"
    REUSE_RESOURCE = "REUSE_RESOURCE"
    CANCEL = "CANCEL"


class ExecutionMode(str, Enum):
    """Execution modes supported by the Brain Execution Engine."""

    DIRECT = "DIRECT"
    PLANNED = "PLANNED"
    AI_GUIDED = "AI_GUIDED"
    INTERACTIVE = "INTERACTIVE"
    CRITICAL = "CRITICAL"
    DEFAULT = "DEFAULT"


class ExecutionRequest(BaseModel):
    """Immutable Pydantic v2 model representing an incoming request to the execution engine."""

    model_config = ConfigDict(frozen=True)

    request_id: str = Field(default_factory=lambda: f"req-{uuid.uuid4().hex[:8]}")
    prompt: str = ""
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    category: Optional[str] = None
    mode: ExecutionMode = ExecutionMode.DEFAULT
    context: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ExecutionStepResult(BaseModel):
    """Immutable model representing the outcome of executing a single ActionStep."""

    model_config = ConfigDict(frozen=True)

    step_id: str = ""
    step_number: Optional[int] = None
    status: ExecutionStatus = ExecutionStatus.COMPLETED
    started_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    duration_ms: float = 0.0
    output: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExecutionDecision(BaseModel):
    """Immutable model encapsulating pre-execution decision analysis results."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    decision_type: DecisionType = DecisionType.DIRECT_EXECUTION
    requires_planner: bool = False
    requires_ai: bool = False
    requires_clarification: bool = False
    requires_security_review: bool = False
    mode: ExecutionMode = ExecutionMode.DIRECT
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    reason: Any = Field(default="UNKNOWN")
    message: str = ""
    recommended_action: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("reason", mode="before")
    @classmethod
    def _validate_reason(cls, v: Any) -> Any:
        if hasattr(v, "value"):
            return v
        if isinstance(v, str):
            return StrEnumAdapter(v)
        return StrEnumAdapter(str(v))


class ExecutionContext(BaseModel):
    """Immutable model representing active context variables during execution."""

    model_config = ConfigDict(frozen=True)

    execution_id: str = Field(default_factory=lambda: f"exec-{uuid.uuid4().hex[:8]}")
    request: ExecutionRequest = Field(default_factory=ExecutionRequest)
    state: ExecutionState = ExecutionState.PENDING
    mode: ExecutionMode = ExecutionMode.DEFAULT
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    progress: float = 0.0
    step_results: List[ExecutionStepResult] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ExecutionResult(BaseModel):
    """Immutable model representing the final outcome of execution."""

    model_config = ConfigDict(frozen=True)

    execution_id: str = ""
    status: ExecutionStatus = ExecutionStatus.COMPLETED
    state: ExecutionState = ExecutionState.COMPLETED
    step_results: List[ExecutionStepResult] = Field(default_factory=list)
    completed_steps: int = 0
    failed_steps: int = 0
    cancelled_steps: int = 0
    execution_time: float = 0.0
    output: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    started_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExecutionStatistics(BaseModel):
    """Immutable model representing diagnostic statistics of the Execution Engine."""

    model_config = ConfigDict(frozen=True)

    total_requests: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    cancelled_executions: int = 0
    average_execution_time_ms: float = 0.0
    decisions_by_type: Dict[str, int] = Field(default_factory=dict)
    active_sessions: int = 0
    # Backward compatibility attributes
    executions_started: int = 0
    executions_completed: int = 0
    executions_failed: int = 0
    average_runtime_ms: float = 0.0
    average_step_time_ms: float = 0.0
    current_running_sessions: int = 0
    peak_concurrent_sessions: int = 0
    cancellation_count: int = 0
    retry_count: int = 0
    rollback_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExecutionHealth(BaseModel):
    """Immutable model representing health status of the Execution Engine."""

    model_config = ConfigDict(frozen=True)

    status: Any = "READY"
    healthy: bool = True
    components: Dict[str, bool] = Field(default_factory=dict)
    registered_components: Dict[str, bool] = Field(default_factory=dict)
    statistics: Dict[str, Any] = Field(default_factory=dict)
    current_sessions: int = 0
    detected_issues: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
