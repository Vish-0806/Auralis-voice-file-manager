"""Domain data models and enumerations for the Auralis Workflow Execution Engine (Phase 12.4).

Defines immutable Pydantic v2 models representing workflow steps, dependencies, requests,
live context, execution state, workflow results, statistics, and health reports.
"""

from datetime import datetime, timezone
from enum import Enum
import uuid
from typing import Any, Dict, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


class WorkflowStatus(str, Enum):
    """Lifecycle status states for workflows."""

    PENDING = "PENDING"
    READY = "READY"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class WorkflowStepStatus(str, Enum):
    """Lifecycle status states for individual workflow steps."""

    PENDING = "PENDING"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    CANCELLED = "CANCELLED"
    RETRYING = "RETRYING"


class WorkflowExecutionMode(str, Enum):
    """Execution modes for workflow step scheduling."""

    SEQUENTIAL = "SEQUENTIAL"
    PARALLEL = "PARALLEL"
    HYBRID = "HYBRID"
    ADAPTIVE = "ADAPTIVE"


class DependencyType(str, Enum):
    """Types of dependencies between workflow steps."""

    HARD = "HARD"
    SOFT = "SOFT"
    CONDITIONAL = "CONDITIONAL"


class WorkflowPriority(str, Enum):
    """Priority levels for workflow execution."""

    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class WorkflowDependency(BaseModel):
    """Immutable model representing a dependency relationship between workflow steps."""

    model_config = ConfigDict(frozen=True)

    dependency_id: str = Field(default_factory=lambda: f"dep-{uuid.uuid4().hex[:8]}")
    source_step_id: str = ""
    target_step_id: str = ""
    dependency_type: DependencyType = DependencyType.HARD
    condition: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowStep(BaseModel):
    """Immutable model representing a single step within a workflow graph."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    step_id: str = Field(default_factory=lambda: f"step-{uuid.uuid4().hex[:8]}")
    name: str = ""
    action_type: str = "EXECUTE"
    prompt_or_payload: Any = ""
    status: WorkflowStepStatus = WorkflowStepStatus.PENDING
    dependencies: List[str] = Field(default_factory=list)
    priority: WorkflowPriority = WorkflowPriority.NORMAL
    retries_left: int = 0
    max_retries: int = 3
    output: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowRequest(BaseModel):
    """Immutable model representing a request to execute a workflow graph."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    request_id: str = Field(default_factory=lambda: f"wf-req-{uuid.uuid4().hex[:8]}")
    name: str = "Untitled Workflow"
    description: str = ""
    steps: List[WorkflowStep] = Field(default_factory=list)
    mode: WorkflowExecutionMode = WorkflowExecutionMode.SEQUENTIAL
    priority: WorkflowPriority = WorkflowPriority.NORMAL
    context: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WorkflowContext(BaseModel):
    """Immutable model tracking active state during workflow execution."""

    model_config = ConfigDict(frozen=True)

    context_id: str = Field(default_factory=lambda: f"wf-ctx-{uuid.uuid4().hex[:8]}")
    request: WorkflowRequest = Field(default_factory=WorkflowRequest)
    status: WorkflowStatus = WorkflowStatus.PENDING
    current_step_id: Optional[str] = None
    completed_step_ids: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WorkflowExecution(BaseModel):
    """Immutable record tracking execution state and topological step order."""

    model_config = ConfigDict(frozen=True)

    execution_id: str = Field(default_factory=lambda: f"wf-exec-{uuid.uuid4().hex[:8]}")
    workflow_id: str = ""
    status: WorkflowStatus = WorkflowStatus.PENDING
    step_results: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    execution_order: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowResult(BaseModel):
    """Immutable model representing the final outcome of a workflow execution."""

    model_config = ConfigDict(frozen=True)

    workflow_id: str = ""
    execution_id: str = Field(default_factory=lambda: f"res-{uuid.uuid4().hex[:8]}")
    status: WorkflowStatus = WorkflowStatus.COMPLETED
    step_results: List[WorkflowStep] = Field(default_factory=list)
    completed_steps: int = 0
    failed_steps: int = 0
    total_steps: int = 0
    execution_time_ms: float = 0.0
    started_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowStatistics(BaseModel):
    """Immutable model representing diagnostic statistics of the Workflow Execution Engine."""

    model_config = ConfigDict(frozen=True)

    total_workflows: int = 0
    completed_count: int = 0
    failed_count: int = 0
    cancelled_count: int = 0
    average_execution_time_ms: float = 0.0
    total_steps_executed: int = 0
    active_workflows: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowHealth(BaseModel):
    """Immutable model representing health status of the Workflow Execution Engine."""

    model_config = ConfigDict(frozen=True)

    status: str = "READY"
    healthy: bool = True
    components: Dict[str, bool] = Field(default_factory=dict)
    statistics: Dict[str, Any] = Field(default_factory=dict)
    detected_issues: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
