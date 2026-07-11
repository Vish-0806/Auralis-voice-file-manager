"""Data models for Auralis Multi-Step Progress Monitoring and Metrics collection."""

from __future__ import annotations

from enum import Enum
from typing import List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


class ExecutionEvent(str, Enum):
    """The type of lifecycle events emitted by the execution engine."""

    ExecutionStarted = "ExecutionStarted"
    StepStarted = "StepStarted"
    StepCompleted = "StepCompleted"
    StepFailed = "StepFailed"
    RecoveryStarted = "RecoveryStarted"
    RecoveryFinished = "RecoveryFinished"
    ExecutionCompleted = "ExecutionCompleted"


class ExecutionProgress(BaseModel):
    """Observational snapshot of the currently running plan progress."""

    execution_id: str = Field(description="Unique execution session identifier")
    current_step: Optional[str] = Field(None, description="Active step ID")
    completed_steps: List[str] = Field(default_factory=list, description="List of completed step IDs")
    remaining_steps: List[str] = Field(default_factory=list, description="List of remaining step IDs")
    elapsed_time: float = Field(default=0.0, description="Elapsed time in seconds since start")
    estimated_remaining_time: float = Field(default=0.0, description="Estimated remaining duration in seconds")
    percent_complete: float = Field(default=0.0, description="Completion percentage from 0 to 100")


class ExecutionMetrics(BaseModel):
    """Aggregated performance metrics of step and plan executions."""

    execution_duration: float = Field(default=0.0, description="Duration of current execution run")
    average_step_duration: float = Field(default=0.0, description="Mean step completion time in seconds")
    success_rate: float = Field(default=0.0, description="Percentage of successful steps executed")
    failure_rate: float = Field(default=0.0, description="Percentage of failed steps executed")
    recovery_count: int = Field(default=0, description="Number of recovery self-correction actions applied")


class ProgressUpdate(BaseModel):
    """Progress monitoring event package published to system event pipelines."""

    event_type: ExecutionEvent = Field(description="The context event type")
    progress: ExecutionProgress = Field(description="Current step progress tracking metrics")
    metrics: ExecutionMetrics = Field(description="Accumulated metrics data")
    timestamp: float = Field(description="UTC timestamp when this status update package was compiled")
