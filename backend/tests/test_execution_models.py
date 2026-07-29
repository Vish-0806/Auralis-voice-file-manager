"""Unit tests for Execution Engine data models (Phase 9.4)."""

from datetime import datetime
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from brain.execution import (
    ExecutionResult,
    ExecutionStatus,
    ExecutionStepResult,
)


def test_execution_status_enum() -> None:
    """Verifies ExecutionStatus enum members."""
    statuses = [
        ExecutionStatus.PENDING,
        ExecutionStatus.READY,
        ExecutionStatus.RUNNING,
        ExecutionStatus.WAITING,
        ExecutionStatus.PAUSED,
        ExecutionStatus.CANCELLED,
        ExecutionStatus.FAILED,
        ExecutionStatus.COMPLETED,
        ExecutionStatus.BLOCKED,
        ExecutionStatus.ROLLING_BACK,
    ]
    assert len(statuses) == 10
    assert ExecutionStatus.COMPLETED.value == "COMPLETED"
    assert ExecutionStatus.FAILED.value == "FAILED"


def test_execution_step_result_defaults() -> None:
    """Verifies default values for ExecutionStepResult model."""
    res = ExecutionStepResult()
    assert res.step_id == ""
    assert res.step_number is None
    assert res.status == ExecutionStatus.COMPLETED
    assert isinstance(res.started_at, datetime)
    assert isinstance(res.finished_at, datetime)
    assert res.duration_ms == 0.0
    assert res.output == {}
    assert res.error is None
    assert res.metadata == {}


def test_execution_step_result_custom() -> None:
    """Verifies custom values for ExecutionStepResult model."""
    res = ExecutionStepResult(
        step_id="s1",
        step_number=1,
        status=ExecutionStatus.FAILED,
        duration_ms=150.5,
        output={"key": "val"},
        error="Execution failed",
        metadata={"attempt": 2},
    )
    assert res.step_id == "s1"
    assert res.step_number == 1
    assert res.status == ExecutionStatus.FAILED
    assert res.duration_ms == 150.5
    assert res.output == {"key": "val"}
    assert res.error == "Execution failed"
    assert res.metadata == {"attempt": 2}


def test_execution_step_result_immutability() -> None:
    """Verifies ExecutionStepResult is immutable (frozen=True)."""
    res = ExecutionStepResult(step_id="s1")
    with pytest.raises((TypeError, ValidationError)):
        res.step_id = "s2"  # type: ignore


def test_execution_result_defaults() -> None:
    """Verifies default values for ExecutionResult model."""
    res = ExecutionResult()
    assert res.execution_id == ""
    assert res.status == ExecutionStatus.COMPLETED
    assert res.step_results == []
    assert res.completed_steps == 0
    assert res.failed_steps == 0
    assert res.cancelled_steps == 0
    assert res.execution_time == 0.0
    assert isinstance(res.started_at, datetime)
    assert isinstance(res.finished_at, datetime)
    assert res.metadata == {}


def test_execution_result_custom() -> None:
    """Verifies custom values for ExecutionResult model."""
    sr = ExecutionStepResult(step_id="s1", status=ExecutionStatus.COMPLETED)
    res = ExecutionResult(
        execution_id="e100",
        status=ExecutionStatus.COMPLETED,
        step_results=[sr],
        completed_steps=1,
        execution_time=250.0,
        metadata={"user_id": "u1"},
    )
    assert res.execution_id == "e100"
    assert res.status == ExecutionStatus.COMPLETED
    assert len(res.step_results) == 1
    assert res.completed_steps == 1
    assert res.execution_time == 250.0
    assert res.metadata == {"user_id": "u1"}


def test_execution_result_immutability() -> None:
    """Verifies ExecutionResult is immutable (frozen=True)."""
    res = ExecutionResult(execution_id="e1")
    with pytest.raises((TypeError, ValidationError)):
        res.status = ExecutionStatus.FAILED  # type: ignore


def test_execution_step_result_serialization() -> None:
    """Verifies dict serialization of ExecutionStepResult."""
    sr = ExecutionStepResult(step_id="s1", duration_ms=10.0)
    data = sr.model_dump()
    assert data["step_id"] == "s1"
    assert data["duration_ms"] == 10.0


def test_execution_result_serialization() -> None:
    """Verifies dict serialization of ExecutionResult."""
    res = ExecutionResult(execution_id="e1", completed_steps=2)
    data = res.model_dump()
    assert data["execution_id"] == "e1"
    assert data["completed_steps"] == 2


def test_execution_step_result_json_schema() -> None:
    """Verifies JSON schema generation for ExecutionStepResult."""
    schema = ExecutionStepResult.model_json_schema()
    assert "properties" in schema
    assert "step_id" in schema["properties"]


def test_execution_result_json_schema() -> None:
    """Verifies JSON schema generation for ExecutionResult."""
    schema = ExecutionResult.model_json_schema()
    assert "properties" in schema
    assert "execution_id" in schema["properties"]


def test_execution_status_str_comparison() -> None:
    """Verifies ExecutionStatus string comparison."""
    assert ExecutionStatus.READY == "READY"
    assert ExecutionStatus.RUNNING == "RUNNING"


def test_step_result_with_none_timestamps() -> None:
    """Verifies ExecutionStepResult when timestamps are explicit None."""
    sr = ExecutionStepResult(started_at=None, finished_at=None)
    assert sr.started_at is None
    assert sr.finished_at is None


def test_result_with_none_timestamps() -> None:
    """Verifies ExecutionResult when timestamps are explicit None."""
    res = ExecutionResult(started_at=None, finished_at=None)
    assert res.started_at is None
    assert res.finished_at is None


def test_step_result_copy_with_changes() -> None:
    """Verifies copying ExecutionStepResult with updated fields."""
    sr = ExecutionStepResult(step_id="s1", status=ExecutionStatus.PENDING)
    sr2 = sr.model_copy(update={"status": ExecutionStatus.COMPLETED})
    assert sr.status == ExecutionStatus.PENDING
    assert sr2.status == ExecutionStatus.COMPLETED


def test_execution_result_copy_with_changes() -> None:
    """Verifies copying ExecutionResult with updated fields."""
    res = ExecutionResult(execution_id="e1", status=ExecutionStatus.RUNNING)
    res2 = res.model_copy(update={"status": ExecutionStatus.COMPLETED})
    assert res.status == ExecutionStatus.RUNNING
    assert res2.status == ExecutionStatus.COMPLETED


def test_multiple_step_results_in_execution_result() -> None:
    """Verifies ExecutionResult containing multiple ExecutionStepResult instances."""
    sr1 = ExecutionStepResult(step_id="s1", step_number=1, status=ExecutionStatus.COMPLETED)
    sr2 = ExecutionStepResult(step_id="s2", step_number=2, status=ExecutionStatus.FAILED, error="Err")
    res = ExecutionResult(execution_id="e1", step_results=[sr1, sr2], completed_steps=1, failed_steps=1)

    assert len(res.step_results) == 2
    assert res.step_results[0].status == ExecutionStatus.COMPLETED
    assert res.step_results[1].status == ExecutionStatus.FAILED


def test_execution_result_failed_steps_count() -> None:
    """Verifies failed_steps tracking in ExecutionResult."""
    res = ExecutionResult(failed_steps=3)
    assert res.failed_steps == 3


def test_execution_result_cancelled_steps_count() -> None:
    """Verifies cancelled_steps tracking in ExecutionResult."""
    res = ExecutionResult(cancelled_steps=2)
    assert res.cancelled_steps == 2


def test_execution_status_is_hashable() -> None:
    """Verifies ExecutionStatus enum members are hashable as dictionary keys."""
    d = {ExecutionStatus.COMPLETED: 1, ExecutionStatus.FAILED: 0}
    assert d[ExecutionStatus.COMPLETED] == 1


def test_step_result_metadata_dictionary() -> None:
    """Verifies arbitrary metadata in ExecutionStepResult."""
    sr = ExecutionStepResult(metadata={"trace_id": "12345", "retries": 1})
    assert sr.metadata["trace_id"] == "12345"
    assert sr.metadata["retries"] == 1


def test_result_metadata_dictionary() -> None:
    """Verifies arbitrary metadata in ExecutionResult."""
    res = ExecutionResult(metadata={"environment": "production"})
    assert res.metadata["environment"] == "production"
