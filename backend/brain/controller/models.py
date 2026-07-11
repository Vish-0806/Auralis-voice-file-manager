"""Data models for Auralis AI Brain Controller orchestration."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


class BrainStatus(str, Enum):
    """Execution status states of the BrainController pipeline."""

    IDLE = "IDLE"
    PROCESSING = "PROCESSING"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class BrainRequest(BaseModel):
    """Envelope wrapper for incoming user request pipelines.

    Attributes:
        message: The natural language request string.
        context: Optional session context payload dictionary.
        correlation_id: Unique trace correlation identifier.
    """

    message: str = Field(description="Natural language request command")
    context: Optional[Dict[str, Any]] = Field(None, description="Optional session context details")
    correlation_id: str = Field(description="Trace ID tracking execution lifecycle runs")


class BrainExecution(BaseModel):
    """Tracks active pipeline state operations.

    Attributes:
        execution_id: Unique run execution identifier.
        status: Active BrainStatus state.
        start_time: Session start timestamp.
        end_time: Session end timestamp.
    """

    execution_id: str = Field(description="Unique execution identifier")
    status: BrainStatus = Field(default=BrainStatus.IDLE, description="Current controller status state")
    start_time: float = Field(description="Start epoch time")
    end_time: Optional[float] = Field(None, description="End epoch time")


class BrainResponse(BaseModel):
    """Standard return payload compiled after brain controller runs.

    Attributes:
        success: Whether the pipeline execution resolved successfully.
        message: Descriptive execution outcome message.
        goal_name: Canonical goal name interpreted.
        plan: The executed RoutedExecutionPlan.
        summary: Optional summary execution stats.
        metrics: Optional performance metrics compiled.
    """

    success: bool = Field(description="Success indicator")
    message: str = Field(description="Output message response payload")
    goal_name: str = Field(description="Canonical interpreted goal name")
    plan: Optional[Any] = Field(None, description="The executed RoutedExecutionPlan")
    summary: Optional[Any] = Field(None, description="Detailed multi-step ExecutionSummary")
    metrics: Optional[Any] = Field(None, description="Aggregated ExecutionMetrics statistics")
