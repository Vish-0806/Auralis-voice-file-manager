"""Unit tests for the Execution State Manager domain models."""

from __future__ import annotations

from datetime import datetime, timezone
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from brain.execution.execution_state import (
    ExecutionStatus,
    ExecutionProgress,
    ExecutionState,
    ExecutionSnapshot,
    ExecutionStateConfig,
)


def test_execution_status_enum() -> None:
    """Verifies that all required ExecutionStatus enum values exist."""
    expected_values = {
        "QUEUED",
        "RUNNING",
        "PAUSED",
        "WAITING",
        "RETRYING",
        "COMPLETED",
        "FAILED",
        "CANCELLED",
        "TIMEOUT",
        "WAITING_FOR_CONFIRMATION",
    }
    assert {status.value for status in ExecutionStatus} == expected_values


def test_execution_progress_defaults() -> None:
    """Verifies that ExecutionProgress initializes with correct defaults."""
    prog = ExecutionProgress()
    assert prog.percentage == 0.0
    assert prog.current_step == 0
    assert prog.total_steps == 0
    assert prog.current_operation is None
    assert prog.estimated_remaining_seconds is None
    assert prog.started_at is None
    assert prog.completed_at is None
    assert isinstance(prog.last_updated, datetime)
    assert prog.last_updated.tzinfo is timezone.utc


def test_execution_progress_update() -> None:
    """Verifies that update_progress correctly updates progress fields."""
    prog = ExecutionProgress()
    prog.update_progress(
        percentage=45.5,
        current_step=2,
        total_steps=5,
        current_operation="Downloading file",
        estimated_remaining_seconds=12.5,
    )
    assert prog.percentage == 45.5
    assert prog.current_step == 2
    assert prog.total_steps == 5
    assert prog.current_operation == "Downloading file"
    assert prog.estimated_remaining_seconds == 12.5
    assert prog.last_updated.tzinfo is timezone.utc


def test_execution_progress_mark_completed() -> None:
    """Verifies that mark_completed sets completion fields properly."""
    prog = ExecutionProgress()
    prog.mark_completed()
    assert prog.percentage == 100.0
    assert prog.completed_at is not None
    assert prog.completed_at.tzinfo is timezone.utc


def test_execution_progress_mark_failed() -> None:
    """Verifies that mark_failed sets completion timestamp on failure."""
    prog = ExecutionProgress()
    prog.mark_failed()
    assert prog.completed_at is not None
    assert prog.completed_at.tzinfo is timezone.utc


def test_execution_state_defaults() -> None:
    """Verifies default values on ExecutionState creation."""
    state = ExecutionState(execution_id="exec_123", user_id=1)
    assert state.execution_id == "exec_123"
    assert state.user_id == 1
    assert state.workflow_id is None
    assert state.status == ExecutionStatus.QUEUED
    assert isinstance(state.progress, ExecutionProgress)
    assert state.current_step_id is None
    assert state.completed_steps == []
    assert state.pending_steps == []
    assert state.failed_steps == []
    assert state.error_message is None
    assert state.retry_count == 0
    assert isinstance(state.created_at, datetime)
    assert state.created_at.tzinfo is timezone.utc
    assert isinstance(state.updated_at, datetime)
    assert state.updated_at.tzinfo is timezone.utc


def test_execution_state_is_active_finished() -> None:
    """Verifies is_active and is_finished return correct states."""
    state = ExecutionState(execution_id="exec_123", user_id=1)

    # QUEUED is active
    assert state.is_active() is True
    assert state.is_finished() is False

    # RUNNING is active
    state.status = ExecutionStatus.RUNNING
    assert state.is_active() is True
    assert state.is_finished() is False

    # COMPLETED is terminal
    state.status = ExecutionStatus.COMPLETED
    assert state.is_active() is False
    assert state.is_finished() is True

    # FAILED is terminal
    state.status = ExecutionStatus.FAILED
    assert state.is_active() is False
    assert state.is_finished() is True


def test_execution_state_retry_logic() -> None:
    """Verifies retry conditions based on count limits."""
    state = ExecutionState(execution_id="exec_123", user_id=1)

    # Cannot retry if QUEUED
    assert state.can_retry(max_retries=3) is False

    # Can retry if FAILED and count < limit
    state.status = ExecutionStatus.FAILED
    assert state.can_retry(max_retries=3) is True

    # Cannot retry if count reaches limit
    state.retry_count = 3
    assert state.can_retry(max_retries=3) is False


def test_execution_state_running_paused() -> None:
    """Verifies state marking transitions for running and paused."""
    state = ExecutionState(execution_id="exec_123", user_id=1)
    
    state.mark_running()
    assert state.status == ExecutionStatus.RUNNING
    assert state.progress.started_at is not None
    assert state.progress.started_at.tzinfo is timezone.utc

    state.mark_paused()
    assert state.status == ExecutionStatus.PAUSED


def test_execution_state_cancelled() -> None:
    """Verifies that mark_cancelled updates state and progress completes."""
    state = ExecutionState(execution_id="exec_123", user_id=1)
    state.mark_cancelled()
    assert state.status == ExecutionStatus.CANCELLED
    assert state.progress.completed_at is not None


def test_execution_state_retrying() -> None:
    """Verifies that mark_retrying transitions state and increments retry count."""
    state = ExecutionState(execution_id="exec_123", user_id=1)
    state.mark_retrying()
    assert state.status == ExecutionStatus.RETRYING
    assert state.retry_count == 1


def test_execution_state_completed_failed() -> None:
    """Verifies mark_completed and mark_failed transitions."""
    state = ExecutionState(execution_id="exec_123", user_id=1)
    
    state.mark_completed()
    assert state.status == ExecutionStatus.COMPLETED
    assert state.progress.percentage == 100.0

    state.mark_failed("Critical network failure")
    assert state.status == ExecutionStatus.FAILED
    assert state.error_message == "Critical network failure"
    assert state.progress.completed_at is not None


def test_execution_snapshot_immutability() -> None:
    """Verifies that ExecutionSnapshot is immutable."""
    snapshot = ExecutionSnapshot(
        execution_id="exec_123",
        status=ExecutionStatus.RUNNING,
        percentage=50.0,
        current_operation="Compiling",
    )
    assert snapshot.execution_id == "exec_123"
    assert snapshot.status == ExecutionStatus.RUNNING

    with pytest.raises(ValidationError):
        # Mutating frozen Pydantic models raises validation/mutation error
        snapshot.percentage = 75.0


def test_execution_state_config_defaults() -> None:
    """Verifies default values for ExecutionStateConfig."""
    config = ExecutionStateConfig()
    assert config.max_retry_count == 3
    assert config.default_timeout_seconds == 600.0
    assert config.progress_update_interval == 1.0
    assert config.snapshot_history_size == 50
