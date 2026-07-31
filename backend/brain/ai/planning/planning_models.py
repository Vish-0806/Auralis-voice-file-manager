"""Strongly typed Pydantic models for Multi-Step Planning Engine (Phase 10.6).

Defines PlanStatus, StepStatus, PlanningGoal, StepDependency, PlanStep, Plan, and ExecutionResult.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


class PlanStatus(str, Enum):
    """Lifecycle status of a multi-step execution Plan."""

    DRAFT = "draft"
    VALIDATED = "validated"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(str, Enum):
    """Lifecycle status of an individual PlanStep."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class StepDependency(BaseModel):
    """Dependency relationship between plan steps."""

    model_config = ConfigDict(frozen=True)

    step_id: str
    depends_on_step_id: str
    condition: Optional[str] = None


class PlanningGoal(BaseModel):
    """Normalized goal representation extracted by GoalAnalyzer."""

    model_config = ConfigDict(frozen=True)

    goal_id: str
    raw_text: str
    normalized_goal: str
    constraints: Dict[str, Any] = Field(default_factory=dict)
    required_capabilities: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PlanStep(BaseModel):
    """Individual executable step within a Plan."""

    model_config = ConfigDict(frozen=True)

    step_id: str
    step_number: int
    description: str
    required_tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[StepDependency] = Field(default_factory=list)
    expected_output_description: str = ""
    status: StepStatus = StepStatus.PENDING
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Plan(BaseModel):
    """Structured, multi-step execution plan."""

    model_config = ConfigDict(frozen=True)

    plan_id: str
    goal_id: str
    steps: List[PlanStep] = Field(default_factory=list)
    status: PlanStatus = PlanStatus.DRAFT
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExecutionResult(BaseModel):
    """Execution status result record for a tracked step."""

    model_config = ConfigDict(frozen=True)

    step_id: str
    status: StepStatus
    output: Optional[Any] = None
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
