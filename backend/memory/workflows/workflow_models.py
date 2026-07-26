"""Production-ready Pydantic models for the Workflow Observation subsystem."""

from datetime import datetime, timezone
from typing import Any, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field, field_validator


def ensure_utc(v: Optional[datetime]) -> Optional[datetime]:
    """Ensures a datetime is timezone-aware and set to UTC."""
    if v is None:
        return None
    if v.tzinfo is None:
        return v.replace(tzinfo=timezone.utc)
    return v.astimezone(timezone.utc)


class WorkflowStepObservation(BaseModel):
    """Represents an observation of a single step execution within a workflow."""

    step_id: str = Field(
        ...,
        description="Unique identifier for the workflow step."
    )
    intent: str = Field(
        ...,
        description="The action intent of this step."
    )
    target: Optional[str] = Field(
        default=None,
        description="The target entity of the step action."
    )
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters passed during this step execution."
    )
    status: str = Field(
        ...,
        description="Execution status of the step (e.g., 'SUCCESS', 'FAILED')."
    )
    duration_ms: float = Field(
        default=0.0,
        description="Duration of step execution in milliseconds."
    )
    timestamp: datetime = Field(
        ...,
        description="Timezone-aware timestamp when this step was executed."
    )

    @field_validator("timestamp", mode="before")
    @classmethod
    def validate_timestamp(cls, v: Any) -> Optional[datetime]:
        """Validates and enforces UTC timezone on timestamp."""
        if isinstance(v, str):
            v = datetime.fromisoformat(v)
        return ensure_utc(v)


class WorkflowSequence(BaseModel):
    """Represents a sequence of step observations during a single workflow run."""

    steps: list[WorkflowStepObservation] = Field(
        default_factory=list,
        description="Ordered list of step observations in the sequence."
    )
    sequence_hash: str = Field(
        ...,
        description="Unique hash identifying this particular sequence of actions."
    )
    total_duration_ms: float = Field(
        default=0.0,
        description="Total execution duration of the sequence in milliseconds."
    )


class WorkflowObservation(BaseModel):
    """Represents a complete workflow execution observation session."""

    user_id: int = Field(
        ...,
        description="Identifier of the user who executed the workflow."
    )
    execution_id: str = Field(
        ...,
        description="Unique execution run identifier."
    )
    sequence: WorkflowSequence = Field(
        ...,
        description="The sequence of actions recorded in this execution."
    )
    success: bool = Field(
        ...,
        description="Whether the entire execution succeeded."
    )
    timestamp: datetime = Field(
        ...,
        description="Timezone-aware timestamp of the workflow execution."
    )
    context_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Execution environment context information."
    )

    @field_validator("timestamp", mode="before")
    @classmethod
    def validate_timestamp(cls, v: Any) -> Optional[datetime]:
        """Validates and enforces UTC timezone on timestamp."""
        if isinstance(v, str):
            v = datetime.fromisoformat(v)
        return ensure_utc(v)


class WorkflowStatistics(BaseModel):
    """Aggregated metrics and statistical patterns for a specific workflow sequence."""

    sequence_hash: str = Field(
        ...,
        description="Unique hash identifier of the workflow sequence pattern."
    )
    total_observations: int = Field(
        default=0,
        ge=0,
        description="Total number of times this sequence was observed."
    )
    successful_executions: int = Field(
        default=0,
        ge=0,
        description="Number of successful runs of this sequence."
    )
    failed_executions: int = Field(
        default=0,
        ge=0,
        description="Number of failed runs of this sequence."
    )
    success_rate: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Rate of successful executions (between 0.0 and 1.0)."
    )
    average_duration_ms: float = Field(
        default=0.0,
        ge=0.0,
        description="Average duration of execution in milliseconds."
    )
    last_observed: Optional[datetime] = Field(
        default=None,
        description="Timezone-aware timestamp of the most recent observation."
    )

    @field_validator("last_observed", mode="before")
    @classmethod
    def validate_last_observed(cls, v: Any) -> Optional[datetime]:
        """Validates and enforces UTC timezone on last_observed timestamp."""
        if v is None:
            return None
        if isinstance(v, str):
            v = datetime.fromisoformat(v)
        return ensure_utc(v)


class ObservationWindow(BaseModel):
    """Represents a temporal window of observations analyzed together."""

    start_time: datetime = Field(
        ...,
        description="Timezone-aware start bound of the observation window."
    )
    end_time: datetime = Field(
        ...,
        description="Timezone-aware end bound of the observation window."
    )
    observations: list[WorkflowObservation] = Field(
        default_factory=list,
        description="Workflow observations recorded within this window."
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata describing this analysis window."
    )

    @field_validator("start_time", "end_time", mode="before")
    @classmethod
    def validate_times(cls, v: Any) -> Optional[datetime]:
        """Validates and enforces UTC timezone on window boundary timestamps."""
        if v is None:
            return None
        if isinstance(v, str):
            v = datetime.fromisoformat(v)
        return ensure_utc(v)
