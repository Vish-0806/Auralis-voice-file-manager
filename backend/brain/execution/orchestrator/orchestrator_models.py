"""Domain data models and enumerations for the Auralis Command Execution Orchestrator (Phase 12.3).

Defines immutable Pydantic v2 models representing execution requests, live execution contexts,
plan references, execution stages, results, summaries, statistics, and health reports.
"""

from datetime import datetime, timezone
from enum import Enum
import uuid
from typing import Any, Dict, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


class ExecutionStageType(str, Enum):
    """Enumeration of execution stage types in the orchestrator pipeline."""

    INTENT_RESOLUTION = "INTENT_RESOLUTION"
    PLANNING = "PLANNING"
    SECURITY_REVIEW = "SECURITY_REVIEW"
    OS_EXECUTION = "OS_EXECUTION"
    RESPONSE_SYNTHESIS = "RESPONSE_SYNTHESIS"


class ExecutionState(str, Enum):
    """Lifecycle execution state states."""

    PENDING = "PENDING"
    PREPARING = "PREPARING"
    ROUTING = "ROUTING"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"
    PAUSED = "PAUSED"


class ExecutionMode(str, Enum):
    """Execution modes supported by the Orchestrator."""

    DIRECT = "DIRECT"
    PLANNED = "PLANNED"
    AI_GUIDED = "AI_GUIDED"
    INTERACTIVE = "INTERACTIVE"
    CRITICAL = "CRITICAL"


class ExecutionPriority(str, Enum):
    """Priority levels assigned to execution requests."""

    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class OrchestrationStatus(str, Enum):
    """Status outcomes for orchestrations and stages."""

    READY = "READY"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    CANCELLED = "CANCELLED"


class ExecutionRequest(BaseModel):
    """Immutable model representing an incoming request to the orchestrator."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    request_id: str = Field(default_factory=lambda: f"orch-req-{uuid.uuid4().hex[:8]}")
    raw_prompt: str = ""
    intent_resolution: Optional[Any] = None
    mode: ExecutionMode = ExecutionMode.DIRECT
    priority: ExecutionPriority = ExecutionPriority.NORMAL
    context: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ExecutionContext(BaseModel):
    """Immutable model tracking live execution context and active state."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    context_id: str = Field(default_factory=lambda: f"orch-ctx-{uuid.uuid4().hex[:8]}")
    request: ExecutionRequest = Field(default_factory=ExecutionRequest)
    state: ExecutionState = ExecutionState.PENDING
    current_stage: Optional[ExecutionStageType] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ExecutionPlanReference(BaseModel):
    """Immutable reference to an associated execution plan."""

    model_config = ConfigDict(frozen=True)

    plan_id: str = Field(default_factory=lambda: f"plan-{uuid.uuid4().hex[:8]}")
    step_count: int = 0
    readiness: str = "READY"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExecutionStage(BaseModel):
    """Immutable model representing the outcome of an individual execution stage."""

    model_config = ConfigDict(frozen=True)

    stage_id: str = Field(default_factory=lambda: f"stage-{uuid.uuid4().hex[:8]}")
    stage_type: ExecutionStageType = ExecutionStageType.INTENT_RESOLUTION
    status: OrchestrationStatus = OrchestrationStatus.SUCCESS
    started_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    duration_ms: float = 0.0
    output: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExecutionResult(BaseModel):
    """Immutable model representing the overall outcome of orchestrated execution."""

    model_config = ConfigDict(frozen=True)

    execution_id: str = Field(default_factory=lambda: f"exec-{uuid.uuid4().hex[:8]}")
    status: OrchestrationStatus = OrchestrationStatus.SUCCESS
    state: ExecutionState = ExecutionState.COMPLETED
    stages: List[ExecutionStage] = Field(default_factory=list)
    plan_ref: Optional[ExecutionPlanReference] = None
    output: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    started_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExecutionSummary(BaseModel):
    """Immutable summary snapshot of an orchestrated execution."""

    model_config = ConfigDict(frozen=True)

    execution_id: str = ""
    prompt: str = ""
    status: OrchestrationStatus = OrchestrationStatus.SUCCESS
    completed_stages: int = 0
    total_stages: int = 0
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExecutionStatistics(BaseModel):
    """Immutable model representing diagnostic statistics of the Command Execution Orchestrator."""

    model_config = ConfigDict(frozen=True)

    total_orchestrations: int = 0
    successful_count: int = 0
    failed_count: int = 0
    aborted_count: int = 0
    average_duration_ms: float = 0.0
    orchestrations_by_mode: Dict[str, int] = Field(default_factory=dict)
    active_orchestrations: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExecutionHealth(BaseModel):
    """Immutable model representing health status of the Command Execution Orchestrator."""

    model_config = ConfigDict(frozen=True)

    status: str = "READY"
    healthy: bool = True
    components: Dict[str, bool] = Field(default_factory=dict)
    statistics: Dict[str, Any] = Field(default_factory=dict)
    detected_issues: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
