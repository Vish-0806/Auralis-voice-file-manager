"""Domain data models and enumerations for the Auralis Automation & Scheduling Runtime (Phase 12.6).

Defines immutable Pydantic v2 models representing automation rules, triggers, schedules,
execution contexts, history records, statistics, and health reports.
"""

from datetime import datetime, timezone
from enum import Enum
import uuid
from typing import Any, Dict, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


class AutomationStatus(str, Enum):
    """Lifecycle status states for automation rules and executions."""

    INACTIVE = "INACTIVE"
    ACTIVE = "ACTIVE"
    SCHEDULED = "SCHEDULED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class AutomationTriggerType(str, Enum):
    """Types of triggers firing automation rules."""

    TIME = "TIME"
    MANUAL = "MANUAL"
    SYSTEM_EVENT = "SYSTEM_EVENT"
    TASK_COMPLETION = "TASK_COMPLETION"
    FILE_SYSTEM = "FILE_SYSTEM"
    CUSTOM = "CUSTOM"


class AutomationScheduleType(str, Enum):
    """Schedule types for time-based automations."""

    ONE_TIME = "ONE_TIME"
    RECURRING = "RECURRING"
    CRON = "CRON"
    EVENT_DRIVEN = "EVENT_DRIVEN"


class AutomationPriority(str, Enum):
    """Priority levels for automation dispatches."""

    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AutomationExecutionMode(str, Enum):
    """Execution dispatch modes for automation actions."""

    INDEPENDENT = "INDEPENDENT"
    TASK_MANAGED = "TASK_MANAGED"
    WORKFLOW_MANAGED = "WORKFLOW_MANAGED"
    ORCHESTRATED = "ORCHESTRATED"


class AutomationSchedule(BaseModel):
    """Immutable model representing time schedule parameters."""

    model_config = ConfigDict(frozen=True)

    schedule_id: str = Field(default_factory=lambda: f"sched-{uuid.uuid4().hex[:8]}")
    schedule_type: AutomationScheduleType = AutomationScheduleType.ONE_TIME
    start_time: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    interval_seconds: Optional[float] = None
    cron_expression: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AutomationTrigger(BaseModel):
    """Immutable model representing trigger criteria for an automation rule."""

    model_config = ConfigDict(frozen=True)

    trigger_id: str = Field(default_factory=lambda: f"trig-{uuid.uuid4().hex[:8]}")
    trigger_type: AutomationTriggerType = AutomationTriggerType.TIME
    schedule: Optional[AutomationSchedule] = None
    event_pattern: Optional[str] = None
    condition: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AutomationRule(BaseModel):
    """Immutable model representing an automation rule definition."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    rule_id: str = Field(default_factory=lambda: f"rule-{uuid.uuid4().hex[:8]}")
    name: str = "Untitled Rule"
    description: str = ""
    trigger: AutomationTrigger = Field(default_factory=AutomationTrigger)
    action_payload: Any = ""
    enabled: bool = True
    priority: AutomationPriority = AutomationPriority.NORMAL
    mode: AutomationExecutionMode = AutomationExecutionMode.INDEPENDENT
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AutomationContext(BaseModel):
    """Immutable context model tracking rule operational state."""

    model_config = ConfigDict(frozen=True)

    context_id: str = Field(default_factory=lambda: f"auto-ctx-{uuid.uuid4().hex[:8]}")
    rule_id: str = ""
    status: AutomationStatus = AutomationStatus.ACTIVE
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AutomationExecution(BaseModel):
    """Immutable model recording a single execution event of an automation rule."""

    model_config = ConfigDict(frozen=True)

    execution_id: str = Field(default_factory=lambda: f"auto-exec-{uuid.uuid4().hex[:8]}")
    rule_id: str = ""
    status: AutomationStatus = AutomationStatus.COMPLETED
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    duration_seconds: float = 0.0
    output: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AutomationHistory(BaseModel):
    """Immutable model storing execution history and run metrics for an automation rule."""

    model_config = ConfigDict(frozen=True)

    rule_id: str = ""
    executions: List[AutomationExecution] = Field(default_factory=list)
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AutomationStatistics(BaseModel):
    """Immutable model representing diagnostic statistics of the Automation Runtime."""

    model_config = ConfigDict(frozen=True)

    total_rules: int = 0
    active_rules: int = 0
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    average_duration_seconds: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AutomationHealth(BaseModel):
    """Immutable model representing health status of the Automation Runtime."""

    model_config = ConfigDict(frozen=True)

    status: str = "READY"
    healthy: bool = True
    components: Dict[str, bool] = Field(default_factory=dict)
    statistics: Dict[str, Any] = Field(default_factory=dict)
    detected_issues: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
