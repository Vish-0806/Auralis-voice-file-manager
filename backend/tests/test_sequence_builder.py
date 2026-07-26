# pyrefly: ignore [missing-import]
import pytest
from datetime import datetime, timezone, timedelta
from memory.workflows.workflow_models import WorkflowStepObservation
from memory.workflows.sequence_builder import SequenceBuilder


def test_sequence_builder_deterministic_sorting():
    builder = SequenceBuilder()
    
    # Base times
    t1 = datetime(2026, 7, 26, 12, 0, 0, tzinfo=timezone.utc)
    t2 = t1 + timedelta(seconds=10)
    
    # 1. Step with same started_at/timestamp, should sort by step_id
    step_b = WorkflowStepObservation(
        step_id="step_b",
        intent="CREATE_FOLDER",
        status="SUCCESS",
        timestamp=t1,
        started_at=t1,
    )
    step_a = WorkflowStepObservation(
        step_id="step_a",
        intent="OPEN_FOLDER",
        status="SUCCESS",
        timestamp=t1,
        started_at=t1,
    )
    
    sorted_steps = builder._sort_steps([step_b, step_a])
    assert sorted_steps[0].step_id == "step_a"
    assert sorted_steps[1].step_id == "step_b"

    # 2. Step with different started_at
    step_c = WorkflowStepObservation(
        step_id="step_c",
        intent="DELETE_FOLDER",
        status="SUCCESS",
        timestamp=t2,
        started_at=t2,
    )
    
    sorted_steps2 = builder._sort_steps([step_c, step_b, step_a])
    assert sorted_steps2[0].step_id == "step_a"
    assert sorted_steps2[1].step_id == "step_b"
    assert sorted_steps2[2].step_id == "step_c"


def test_sequence_builder_create_sequence():
    builder = SequenceBuilder()
    t = datetime(2026, 7, 26, 12, 0, 0, tzinfo=timezone.utc)
    
    step1 = WorkflowStepObservation(
        step_id="s1",
        intent="OPEN_FOLDER",
        status="SUCCESS",
        duration_ms=100.0,
        timestamp=t,
    )
    step2 = WorkflowStepObservation(
        step_id="s2",
        intent="CREATE_FOLDER",
        status="SUCCESS",
        duration_ms=150.0,
        timestamp=t + timedelta(seconds=5),
    )
    
    seq = builder.create_sequence([step2, step1], sequence_id="my-custom-id")
    
    # Verify sequence ID is preserved/assigned
    assert seq.sequence_id == "my-custom-id"
    # Verify steps are ordered
    assert seq.steps[0].step_id == "s1"
    assert seq.steps[1].step_id == "s2"
    # Verify total duration
    assert seq.total_duration_ms == 250.0
    # Verify sequence hash is generated
    assert seq.sequence_hash != ""


def test_sequence_builder_success_detection():
    builder = SequenceBuilder()
    t = datetime.now(timezone.utc)
    
    s_success = WorkflowStepObservation(step_id="1", intent="A", status="SUCCESS", timestamp=t)
    s_failed = WorkflowStepObservation(step_id="2", intent="B", status="FAILED", timestamp=t)
    
    # 1. Mixed status -> failed
    assert builder._determine_success([s_success, s_failed]) is False
    # 2. All success -> success
    assert builder._determine_success([s_success]) is True
    # 3. Empty -> failed (or False)
    assert builder._determine_success([]) is False


def test_sequence_builder_statistics():
    builder = SequenceBuilder()
    t = datetime(2026, 7, 26, 12, 0, 0, tzinfo=timezone.utc)
    
    step1 = WorkflowStepObservation(
        step_id="s1",
        intent="OPEN_FOLDER",
        status="SUCCESS",
        duration_ms=100.0,
        timestamp=t,
    )
    
    stats = builder._calculate_statistics([step1], "some_hash")
    
    assert stats.sequence_hash == "some_hash"
    assert stats.total_observations == 1
    assert stats.successful_executions == 1
    assert stats.failed_executions == 0
    assert stats.success_rate == 1.0
    assert stats.average_duration_ms == 100.0
    assert stats.last_observed == t


def test_sequence_builder_metadata_preservation():
    builder = SequenceBuilder()
    t = datetime.now(timezone.utc)
    
    params = {"path": "/user/workspace", "recursive": True}
    step = WorkflowStepObservation(
        step_id="s1",
        intent="LIST_DIRECTORY",
        parameters=params,
        status="SUCCESS",
        timestamp=t,
    )
    
    seq = builder.create_sequence([step])
    assert seq.steps[0].parameters == params


def test_sequence_builder_empty_sequence():
    builder = SequenceBuilder()
    seq = builder.create_sequence([])
    
    assert seq.steps == []
    assert seq.sequence_hash == "empty_sequence"
    assert seq.total_duration_ms == 0.0
    assert seq.sequence_id != ""
