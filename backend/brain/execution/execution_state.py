"""Domain models for execution state tracking and progress monitoring."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field, ConfigDict


class ExecutionStatus(str, Enum):
    """Operational status values for an execution session."""

    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    WAITING = "WAITING"
    RETRYING = "RETRYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    TIMEOUT = "TIMEOUT"


class ExecutionProgress(BaseModel):
    """Details the real-time progress of a running execution."""

    percentage: float = Field(default=0.0, ge=0.0, le=100.0, description="Progress percentage from 0 to 100")
    current_step: int = Field(default=0, ge=0, description="Index of the currently active step")
    total_steps: int = Field(default=0, ge=0, description="Total number of steps in the task sequence")
    current_operation: Optional[str] = Field(default=None, description="Optional description of the active operation")
    estimated_remaining_seconds: Optional[float] = Field(default=None, description="Estimated time remaining in seconds")
    started_at: Optional[datetime] = Field(default=None, description="Timestamp of when execution started")
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of the last update")
    completed_at: Optional[datetime] = Field(default=None, description="Timestamp of completion or termination")

    def update_progress(
        self,
        percentage: float,
        current_step: int,
        total_steps: int,
        current_operation: Optional[str] = None,
        estimated_remaining_seconds: Optional[float] = None,
    ) -> None:
        """Updates the active progress metrics and updates the last_updated timestamp."""
        self.percentage = max(0.0, min(100.0, percentage))
        self.current_step = current_step
        self.total_steps = total_steps
        self.current_operation = current_operation
        self.estimated_remaining_seconds = estimated_remaining_seconds
        self.last_updated = datetime.now(timezone.utc)

    def mark_completed(self) -> None:
        """Sets progress to 100%, updates last_updated, and sets completed_at."""
        now = datetime.now(timezone.utc)
        self.percentage = 100.0
        self.last_updated = now
        self.completed_at = now

    def mark_failed(self) -> None:
        """Updates last_updated and sets completed_at timestamp on failure."""
        now = datetime.now(timezone.utc)
        self.last_updated = now
        self.completed_at = now


class ExecutionState(BaseModel):
    """Represents the complete execution state record for a session."""

    execution_id: str = Field(description="Unique execution run identifier")
    user_id: int = Field(description="User ID associated with the execution")
    workflow_id: Optional[str] = Field(default=None, description="Workflow ID if executing a workflow")
    status: ExecutionStatus = Field(default=ExecutionStatus.QUEUED, description="Current operational status")
    progress: ExecutionProgress = Field(default_factory=ExecutionProgress, description="Progress monitoring details")
    current_step_id: Optional[str] = Field(default=None, description="ID of the currently running step")
    completed_steps: List[str] = Field(default_factory=list, description="IDs of successfully completed steps")
    pending_steps: List[str] = Field(default_factory=list, description="IDs of pending steps")
    failed_steps: List[str] = Field(default_factory=list, description="IDs of failed steps")
    error_message: Optional[str] = Field(default=None, description="Error message description if failed")
    retry_count: int = Field(default=0, ge=0, description="Number of retries attempted")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last update timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata attributes dictionary")

    def is_active(self) -> bool:
        """Returns True if the execution is in an active (non-terminal) state."""
        return self.status in (
            ExecutionStatus.QUEUED,
            ExecutionStatus.RUNNING,
            ExecutionStatus.RETRYING,
            ExecutionStatus.WAITING,
            ExecutionStatus.PAUSED,
        )

    def is_finished(self) -> bool:
        """Returns True if the execution has reached a terminal state."""
        return self.status in (
            ExecutionStatus.COMPLETED,
            ExecutionStatus.FAILED,
            ExecutionStatus.CANCELLED,
            ExecutionStatus.TIMEOUT,
        )

    def can_retry(self, max_retries: int) -> bool:
        """Returns True if status is FAILED and retry attempts are below max_retries limit."""
        return self.status == ExecutionStatus.FAILED and self.retry_count < max_retries

    def _touch(self) -> None:
        """Internal helper to touch/update the updated_at timestamp."""
        self.updated_at = datetime.now(timezone.utc)

    def mark_running(self) -> None:
        """Transitions status to RUNNING, initializing started_at timestamp if not set."""
        self.status = ExecutionStatus.RUNNING
        if self.progress.started_at is None:
            self.progress.started_at = datetime.now(timezone.utc)
        self._touch()

    def mark_paused(self) -> None:
        """Transitions status to PAUSED."""
        self.status = ExecutionStatus.PAUSED
        self._touch()

    def mark_cancelled(self) -> None:
        """Transitions status to CANCELLED and completes progress timestamps."""
        self.status = ExecutionStatus.CANCELLED
        self.progress.mark_completed()
        self._touch()

    def mark_retrying(self) -> None:
        """Transitions status to RETRYING and increments the retry attempt count."""
        self.status = ExecutionStatus.RETRYING
        self.retry_count += 1
        self._touch()

    def mark_completed(self) -> None:
        """Transitions status to COMPLETED and completes progress timestamps."""
        self.status = ExecutionStatus.COMPLETED
        self.progress.mark_completed()
        self._touch()

    def mark_failed(self, error: str) -> None:
        """Transitions status to FAILED, updates error message, and marks progress failed."""
        self.status = ExecutionStatus.FAILED
        self.error_message = error
        self.progress.mark_failed()
        self._touch()


class ExecutionSnapshot(BaseModel):
    """Immutable snapshot capturing state variables at a specific point in time."""

    model_config = ConfigDict(frozen=True)

    execution_id: str = Field(description="Unique execution run identifier")
    status: ExecutionStatus = Field(description="Execution status at snapshot time")
    percentage: float = Field(description="Progress percentage at snapshot time")
    current_operation: Optional[str] = Field(default=None, description="Active operation description at snapshot time")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of snapshot")


class ExecutionStateConfig(BaseModel):
    """Configuration settings governing execution state parameters."""

    max_retry_count: int = Field(default=3, ge=0, description="Maximum retry limit")
    default_timeout_seconds: float = Field(default=600.0, ge=0.0, description="Timeout limit in seconds")
    progress_update_interval: float = Field(default=1.0, ge=0.0, description="Seconds between progress updates")
    snapshot_history_size: int = Field(default=50, ge=1, description="Size of the snapshot history ring buffer")
