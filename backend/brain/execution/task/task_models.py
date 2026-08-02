"""Domain data models and enumerations for the Auralis Task Management Runtime (Phase 12.5).

Defines immutable Pydantic v2 models representing task requests, task context, progress,
execution results, task state, statistics, and health reports.
"""

from datetime import datetime, timezone
from enum import Enum
import uuid
from typing import Any, Dict, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


class TaskStatus(str, Enum):
    """Lifecycle status states for background tasks."""

    PENDING = "PENDING"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    RECOVERING = "RECOVERING"


class TaskPriority(str, Enum):
    """Priority levels assigned to background tasks."""

    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TaskExecutionMode(str, Enum):
    """Execution modes for background tasks."""

    IMMEDIATE = "IMMEDIATE"
    DELAYED = "DELAYED"
    RECURRING = "RECURRING"
    BACKGROUND = "BACKGROUND"


class TaskFailureReason(str, Enum):
    """Enumeration of task failure causes."""

    TIMEOUT = "TIMEOUT"
    CRASH = "CRASH"
    CANCELLED_BY_USER = "CANCELLED_BY_USER"
    RESOURCE_EXHAUSTED = "RESOURCE_EXHAUSTED"
    UNKNOWN = "UNKNOWN"


class TaskRecoveryMode(str, Enum):
    """Recovery strategies for task failures."""

    NONE = "NONE"
    AUTO_RETRY = "AUTO_RETRY"
    REBOOT_RESUME = "REBOOT_RESUME"
    CHECKPOINT_RESTORE = "CHECKPOINT_RESTORE"


class TaskRequest(BaseModel):
    """Immutable model representing a request to run a background task."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    task_id: str = Field(default_factory=lambda: f"task-{uuid.uuid4().hex[:8]}")
    name: str = "Untitled Task"
    description: str = ""
    payload: Any = ""
    priority: TaskPriority = TaskPriority.NORMAL
    mode: TaskExecutionMode = TaskExecutionMode.IMMEDIATE
    delay_seconds: float = 0.0
    recurring_interval_seconds: Optional[float] = None
    timeout_seconds: Optional[float] = None
    recovery_mode: TaskRecoveryMode = TaskRecoveryMode.AUTO_RETRY
    context: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TaskContext(BaseModel):
    """Immutable model tracking live state and recovery checkpoints of a task."""

    model_config = ConfigDict(frozen=True)

    context_id: str = Field(default_factory=lambda: f"task-ctx-{uuid.uuid4().hex[:8]}")
    request: TaskRequest = Field(default_factory=TaskRequest)
    status: TaskStatus = TaskStatus.PENDING
    checkpoint_data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TaskProgress(BaseModel):
    """Immutable model representing progress metrics for a task."""

    model_config = ConfigDict(frozen=True)

    task_id: str = ""
    progress_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    completed_steps: int = 0
    total_steps: int = 1
    running_duration_seconds: float = 0.0
    estimated_remaining_seconds: float = 0.0
    status_message: str = "Initial"
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TaskResult(BaseModel):
    """Immutable model representing the final outcome of a task execution."""

    model_config = ConfigDict(frozen=True)

    task_id: str = ""
    status: TaskStatus = TaskStatus.COMPLETED
    output: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    failure_reason: Optional[TaskFailureReason] = None
    execution_time_seconds: float = 0.0
    started_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskExecution(BaseModel):
    """Immutable model tracking task execution state and progress snapshot."""

    model_config = ConfigDict(frozen=True)

    execution_id: str = Field(default_factory=lambda: f"task-exec-{uuid.uuid4().hex[:8]}")
    task_id: str = ""
    status: TaskStatus = TaskStatus.RUNNING
    progress: TaskProgress = Field(default_factory=TaskProgress)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskStatistics(BaseModel):
    """Immutable model representing diagnostic statistics of the Task Runtime."""

    model_config = ConfigDict(frozen=True)

    total_tasks: int = 0
    completed_count: int = 0
    failed_count: int = 0
    cancelled_count: int = 0
    paused_count: int = 0
    average_duration_seconds: float = 0.0
    active_tasks: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskHealth(BaseModel):
    """Immutable model representing health status of the Task Runtime."""

    model_config = ConfigDict(frozen=True)

    status: str = "READY"
    healthy: bool = True
    components: Dict[str, bool] = Field(default_factory=dict)
    statistics: Dict[str, Any] = Field(default_factory=dict)
    detected_issues: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
