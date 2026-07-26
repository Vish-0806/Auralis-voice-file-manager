# pyrefly: ignore [missing-import]
import pytest
import logging
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from memory.workflows.workflow_models import WorkflowStepObservation, WorkflowObservation, WorkflowSequence
from memory.workflows.sequence_builder import SequenceBuilder
from memory.workflows.workflow_observer import WorkflowObserver


@pytest.mark.anyio
async def test_successful_observation_creation():
    builder = SequenceBuilder()
    repository = AsyncMock()
    observer = WorkflowObserver(builder, repository)
    
    t = datetime(2026, 7, 26, 12, 0, 0, tzinfo=timezone.utc)
    step = WorkflowStepObservation(
        step_id="step_1",
        intent="OPEN_FOLDER",
        status="SUCCESS",
        timestamp=t
    )
    
    observation = await observer.observe(
        user_id=123,
        execution_id="exec_1",
        steps=[step],
        context_metadata={"os": "windows"}
    )
    
    # Check return value
    assert observation.user_id == 123
    assert observation.execution_id == "exec_1"
    assert observation.success is True
    assert observation.timestamp == t
    assert len(observation.sequence.steps) == 1
    assert observation.context_metadata == {"os": "windows"}
    
    # Check repository call
    repository.save_observation.assert_called_once_with(observation)


@pytest.mark.anyio
async def test_dependency_delegation():
    mock_builder = MagicMock(spec=SequenceBuilder)
    mock_seq = WorkflowSequence(
        steps=[],
        sequence_id="test-id",
        sequence_hash="abc-hash",
        total_duration_ms=0.0
    )
    mock_builder.create_sequence.return_value = mock_seq
    mock_builder._determine_success.return_value = True
    mock_builder._sort_steps.return_value = []

    repository = AsyncMock()
    observer = WorkflowObserver(mock_builder, repository)
    
    t = datetime.now(timezone.utc)
    step = WorkflowStepObservation(
        step_id="s1",
        intent="INTENT",
        status="SUCCESS",
        timestamp=t
    )
    
    await observer.observe(user_id=99, execution_id="ex", steps=[step])
    
    # Verify builder was called
    mock_builder.create_sequence.assert_called_once_with([step])
    # Verify repository was called
    repository.save_observation.assert_called_once()


@pytest.mark.anyio
async def test_validation_failures_empty_steps():
    observer = WorkflowObserver(SequenceBuilder(), AsyncMock())
    
    with pytest.raises(ValueError, match="Steps list cannot be empty"):
        await observer.observe(user_id=123, execution_id="ex", steps=[])


@pytest.mark.anyio
async def test_validation_failures_duplicate_ids():
    observer = WorkflowObserver(SequenceBuilder(), AsyncMock())
    t = datetime.now(timezone.utc)
    step1 = WorkflowStepObservation(step_id="s1", intent="A", status="SUCCESS", timestamp=t)
    step2 = WorkflowStepObservation(step_id="s1", intent="B", status="SUCCESS", timestamp=t) # Duplicate ID
    
    with pytest.raises(ValueError, match="Duplicate step ID detected"):
        await observer.observe(user_id=123, execution_id="ex", steps=[step1, step2])


@pytest.mark.anyio
async def test_validation_failures_invalid_timestamp():
    observer = WorkflowObserver(SequenceBuilder(), AsyncMock())
    
    # Naive timestamp
    naive_t = datetime(2026, 7, 26, 12, 0, 0)
    
    # We must bypass pydantic's mode="before" validator to test how observer handles naive/missing tz info
    # by using object construction that gets naive input or manually altering step properties if allowed,
    # or just passing a manually built step that raises validation or passing naive datetime directly.
    # Pydantic's field_validator coorces naive to UTC, but if we pass None:
    # Actually, let's verify if timestamp is None:
    # (Since timestamp is required on model, passing None to dict init raisesValidationError,
    # but we can set it to a naive datetime without timezone if we construct it).
    # Wait, our validator coorces naive datetime to UTC automatically:
    # ensure_utc(naive_dt) returns a UTC timezone-aware datetime.
    # How can we make it naive?
    # We can manually set the attribute step.timestamp = naive_dt after construction!
    step = WorkflowStepObservation(
        step_id="s1",
        intent="A",
        status="SUCCESS",
        timestamp=datetime.now(timezone.utc)
    )
    step.timestamp = naive_t # Manually assign naive datetime
    
    with pytest.raises(ValueError, match="naive or missing timestamp"):
        observer._validate_steps([step])


@pytest.mark.anyio
async def test_stateless_behavior():
    observer = WorkflowObserver(SequenceBuilder(), AsyncMock())
    t = datetime.now(timezone.utc)
    step = WorkflowStepObservation(step_id="s1", intent="A", status="SUCCESS", timestamp=t)
    
    # Save original state
    original_dict = dict(observer.__dict__)
    
    await observer.observe(user_id=123, execution_id="ex", steps=[step])
    
    # Check that observer state remains unchanged
    assert observer.__dict__.keys() == original_dict.keys()
    for k, v in original_dict.items():
        assert observer.__dict__[k] == v
