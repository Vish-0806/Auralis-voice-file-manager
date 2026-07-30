"""Execution Engine data models for Auralis.

This module defines immutable models representing execution status, step execution results,
and overall execution plan outcomes.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


class ExecutionStatus(str, Enum):
    """Enumeration representing execution lifecycle states."""

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


class ExecutionResult(BaseModel):
    """Immutable model representing the final outcome of an ExecutionPlan execution."""

    model_config = ConfigDict(frozen=True)

    execution_id: str = ""
    status: ExecutionStatus = ExecutionStatus.COMPLETED
    step_results: List[ExecutionStepResult] = Field(default_factory=list)
    completed_steps: int = 0
    failed_steps: int = 0
    cancelled_steps: int = 0
    execution_time: float = 0.0
    started_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)
