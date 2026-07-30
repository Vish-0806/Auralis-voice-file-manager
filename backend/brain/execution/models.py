"""Data models for Auralis Multi-Step Execution monitoring and logging."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field
from core.intents import Intent


from brain.execution.execution_models import ExecutionStatus


class ExecutionRecord(BaseModel):
    """Represents the execution result record for a single planned step.

    Attributes:
        step_id: Unique identifier for the step.
        intent: The Intent executed.
        capability: The capability routed to.
        status: Success/failure status.
        duration: Duration of execution in seconds.
        response: Optional result response string.
        error: Optional error trace details.
    """

    step_id: str = Field(description="Unique step identifier")
    intent: Intent = Field(description="The action intent executed")
    capability: str = Field(description="The routed capability name")
    status: ExecutionStatus = Field(description="Execution status of this step")
    duration: float = Field(description="Execution duration in seconds")
    response: Optional[str] = Field(None, description="Response payload from dispatcher")
    error: Optional[str] = Field(None, description="Exception or error message if failed")


class ExecutionContext(BaseModel):
    """Tracks live execution state details across steps.

    Attributes:
        execution_id: Unique execution session identifier.
        current_step: Optional ID of the currently active step.
        completed_steps: List of step IDs successfully executed.
        current_capability: Optional name of the currently active capability.
        last_execution_result: Optional result dictionary of the last executed step.
    """

    execution_id: str = Field(description="Unique execution session identifier")
    current_step: Optional[str] = Field(None, description="Active execution step ID")
    completed_steps: List[str] = Field(default_factory=list, description="IDs of completed steps")
    current_capability: Optional[str] = Field(None, description="Active capability name")
    last_execution_result: Optional[Dict[str, Any]] = Field(None, description="Metadata result of last action")


class ExecutionSummary(BaseModel):
    """Details the complete summary results of an execution run.

    Attributes:
        execution_id: Unique execution session identifier.
        success: Boolean indicating if the overall run succeeded.
        records: Individual step execution record reports.
        total_duration: Sum of duration times in seconds.
        error: Optional summary execution error details.
    """

    execution_id: str = Field(description="Unique execution session identifier")
    success: bool = Field(description="Whether the entire execution succeeded")
    records: List[ExecutionRecord] = Field(default_factory=list, description="Execution records per step")
    total_duration: float = Field(description="Total execution time in seconds")
    error: Optional[str] = Field(None, description="Overall engine failure message if failed")
