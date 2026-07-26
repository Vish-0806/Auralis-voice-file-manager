# pyrefly: ignore [missing-import]
import pytest
from datetime import datetime, timezone
# pyrefly: ignore [missing-import]
from pydantic import ValidationError
from memory.workflows.workflow_models import (
    WorkflowStepObservation,
    WorkflowSequence,
    WorkflowObservation,
    WorkflowStatistics,
    ObservationWindow,
)


def test_workflow_step_observation_timezone_awareness():
    # Test with timezone-naive datetime
    naive_dt = datetime(2026, 7, 26, 12, 0, 0)
    step = WorkflowStepObservation(
        step_id="step_1",
        intent="OPEN_FOLDER",
        target="/some/path",
        parameters={"path": "/some/path"},
        status="SUCCESS",
        duration_ms=120.5,
        timestamp=naive_dt,
    )
    # Naive datetime should be coerced to UTC
    assert step.timestamp.tzinfo == timezone.utc
    assert step.timestamp.hour == 12

    # Test with string ISO format
    iso_str = "2026-07-26T12:00:00+05:30"
    step2 = WorkflowStepObservation(
        step_id="step_2",
        intent="CLOSE_WINDOW",
        status="SUCCESS",
        timestamp=iso_str,
    )
    # Offset should be correctly normalized to UTC (12:00:00 +05:30 -> 6:30:00 UTC)
    assert step2.timestamp.tzinfo == timezone.utc
    assert step2.timestamp.hour == 6
    assert step2.timestamp.minute == 30


def test_workflow_sequence_nesting():
    step1 = WorkflowStepObservation(
        step_id="s1",
        intent="OPEN_FOLDER",
        status="SUCCESS",
        timestamp=datetime.now(timezone.utc),
    )
    step2 = WorkflowStepObservation(
        step_id="s2",
        intent="CREATE_FOLDER",
        status="SUCCESS",
        timestamp=datetime.now(timezone.utc),
    )
    
    seq = WorkflowSequence(
        steps=[step1, step2],
        sequence_hash="abcdef123456",
        total_duration_ms=250.0,
    )
    
    assert len(seq.steps) == 2
    assert seq.sequence_hash == "abcdef123456"
    assert seq.total_duration_ms == 250.0


def test_workflow_observation_validation():
    step = WorkflowStepObservation(
        step_id="s1",
        intent="OPEN_FOLDER",
        status="SUCCESS",
        timestamp=datetime.now(timezone.utc),
    )
    seq = WorkflowSequence(
        steps=[step],
        sequence_hash="abcdef",
        total_duration_ms=100.0,
    )
    
    obs = WorkflowObservation(
        user_id=123,
        execution_id="exec_abc",
        sequence=seq,
        success=True,
        timestamp="2026-07-26T20:00:00",
    )
    
    assert obs.user_id == 123
    assert obs.timestamp.tzinfo == timezone.utc


def test_workflow_statistics_constraints():
    # Success rate validation limits [0.0, 1.0]
    with pytest.raises(ValidationError):
        WorkflowStatistics(
            sequence_hash="abc",
            total_observations=5,
            success_rate=1.5,  # Invalid (> 1.0)
        )

    with pytest.raises(ValidationError):
        WorkflowStatistics(
            sequence_hash="abc",
            total_observations=-1,  # Invalid (< 0)
        )

    # Valid statistics
    stats = WorkflowStatistics(
        sequence_hash="abc",
        total_observations=10,
        successful_executions=8,
        failed_executions=2,
        success_rate=0.8,
        average_duration_ms=150.0,
        last_observed="2026-07-26T20:00:00Z",
    )
    assert stats.success_rate == 0.8
    assert stats.last_observed.tzinfo == timezone.utc


def test_observation_window_validation():
    step = WorkflowStepObservation(
        step_id="s1",
        intent="OPEN_FOLDER",
        status="SUCCESS",
        timestamp=datetime.now(timezone.utc),
    )
    seq = WorkflowSequence(
        steps=[step],
        sequence_hash="hash",
        total_duration_ms=50.0,
    )
    obs = WorkflowObservation(
        user_id=99,
        execution_id="exec_1",
        sequence=seq,
        success=True,
        timestamp=datetime.now(timezone.utc),
    )

    window = ObservationWindow(
        start_time="2026-07-26T00:00:00",
        end_time="2026-07-26T23:59:59",
        observations=[obs],
    )
    assert window.start_time.tzinfo == timezone.utc
    assert window.end_time.tzinfo == timezone.utc
    assert len(window.observations) == 1
