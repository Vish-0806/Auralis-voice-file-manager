"""Unit and integration tests for the Execution Engine State Manager integration."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
# pyrefly: ignore [missing-import]
import pytest

from brain.execution.execution_engine import ExecutionEngine
from brain.execution.execution_state import ExecutionStatus
from brain.execution.execution_state_manager import ExecutionStateManager
from brain.capability.models import RoutedExecutionPlan, CapabilityRoute
from core.intents import Intent
from core.models import ExecutionResult


@pytest.fixture
def mock_dispatcher() -> MagicMock:
    """Returns a mock dispatcher that returns a successful execution result."""
    dispatcher = MagicMock()
    dispatcher._capabilities = {"desktop": MagicMock()}
    dispatcher.dispatch.return_value = ExecutionResult(
        success=True,
        response="Action completed",
        execution_time=0.05,
    )
    return dispatcher


def test_runtime_execution_created_and_running(mock_dispatcher) -> None:
    """Verifies that an execution is registered and marked running when execution begins."""
    state_manager = ExecutionStateManager()
    engine = ExecutionEngine(state_manager=state_manager)

    plan = RoutedExecutionPlan(
        intent=Intent.MUTE,
        target="volume",
        confidence=1.0,
        routes=[CapabilityRoute(step_id="step_1", intent=Intent.MUTE, capability_name="desktop")],
    )

    summary = engine.execute_plan(plan, mock_dispatcher)
    assert summary.success is True

    # Retrieve execution state from manager
    exec_id = summary.execution_id
    state = state_manager.get_execution(exec_id)
    
    assert state is not None
    assert state.status == ExecutionStatus.COMPLETED
    assert state.progress.started_at is not None
    assert state.progress.completed_at is not None


def test_runtime_progress_updates(mock_dispatcher) -> None:
    """Verifies that the progress percentage and current operation update during step execution."""
    state_manager = ExecutionStateManager()
    engine = ExecutionEngine(state_manager=state_manager)

    plan = RoutedExecutionPlan(
        intent=Intent.RUN_WORKFLOW,
        target="Study Mode",
        confidence=1.0,
        routes=[
            CapabilityRoute(step_id="step_1", intent=Intent.MUTE, capability_name="desktop"),
            CapabilityRoute(step_id="step_2", intent=Intent.OPEN_APPLICATION, capability_name="desktop"),
        ],
    )

    summary = engine.execute_plan(plan, mock_dispatcher)
    assert summary.success is True

    exec_id = summary.execution_id
    history = state_manager.get_snapshot_history(exec_id)
    
    # Snapshots should be:
    # 0: QUEUED (0.0%)
    # 1: RUNNING (0.0%)
    # 2: Progress before step 1 (0.0%, current_operation="step_1")
    # 3: Progress after step 1 (50.0%)
    # 4: Progress before step 2 (50.0%, current_operation="step_2")
    # 5: Progress after step 2 (100.0%)
    # 6: COMPLETED (100.0%)
    assert len(history) >= 6
    assert history[0].percentage == 0.0
    assert history[0].status == ExecutionStatus.QUEUED
    assert any(h.percentage == 50.0 for h in history)
    assert any(h.percentage == 100.0 for h in history)


def test_runtime_failure_state() -> None:
    """Verifies that execution failure is captured and marked failed in the state manager."""
    state_manager = ExecutionStateManager()
    engine = ExecutionEngine(state_manager=state_manager)

    mock_dispatcher = MagicMock()
    mock_dispatcher._capabilities = {"desktop": MagicMock()}
    mock_dispatcher.dispatch.return_value = ExecutionResult(
        success=False,
        response="Failed to open",
        error="Application not found",
        execution_time=0.01,
    )

    plan = RoutedExecutionPlan(
        intent=Intent.OPEN_APPLICATION,
        target="chrome",
        confidence=1.0,
        routes=[CapabilityRoute(step_id="step_1", intent=Intent.OPEN_APPLICATION, capability_name="desktop")],
    )

    summary = engine.execute_plan(plan, mock_dispatcher)
    assert summary.success is False

    state = state_manager.get_execution(summary.execution_id)
    assert state is not None
    assert state.status == ExecutionStatus.FAILED
    assert "failed" in state.error_message.lower()


def test_runtime_retry_transition(mock_dispatcher) -> None:
    """Verifies that retrying self-correction marks the status as RETRYING."""
    state_manager = ExecutionStateManager()
    engine = ExecutionEngine(state_manager=state_manager)

    # Force a failure that gets recovered by the engine
    failing_result = ExecutionResult(success=False, response="failed", error="err", execution_time=0.01)
    success_result = ExecutionResult(success=True, response="recovered", execution_time=0.02)
    mock_dispatcher.dispatch.side_effect = [failing_result, success_result]

    plan = RoutedExecutionPlan(
        intent=Intent.MUTE,
        target="volume",
        confidence=1.0,
        routes=[CapabilityRoute(step_id="step_1", intent=Intent.MUTE, capability_name="desktop")],
    )

    # Mock recovery engine to return success
    recovery_mock = MagicMock()
    recovery_mock.recover.return_value = MagicMock(success=True, strategy_applied="Fallback Strategy")
    engine._recovery_engine = recovery_mock

    summary = engine.execute_plan(plan, mock_dispatcher)
    assert summary.success is True

    history = state_manager.get_snapshot_history(summary.execution_id)
    # Check that RETRYING was recorded in the snapshot history
    assert any(h.status == ExecutionStatus.RETRYING for h in history)
    
    state = state_manager.get_execution(summary.execution_id)
    assert state.retry_count == 1
    assert state.status == ExecutionStatus.COMPLETED


def test_runtime_uuid_generation(mock_dispatcher) -> None:
    """Verifies that a standard UUID4 is generated if no execution ID is supplied in metadata."""
    state_manager = ExecutionStateManager()
    engine = ExecutionEngine(state_manager=state_manager)

    plan = RoutedExecutionPlan(
        intent=Intent.MUTE,
        target="volume",
        confidence=1.0,
        routes=[CapabilityRoute(step_id="step_1", intent=Intent.MUTE, capability_name="desktop")],
    )

    summary = engine.execute_plan(plan, mock_dispatcher)
    exec_id = summary.execution_id
    
    # Check that it's a valid UUID4 (length 36, contains dashes)
    import uuid
    val = uuid.UUID(exec_id)
    assert str(val) == exec_id


def test_runtime_uuid_reuse(mock_dispatcher) -> None:
    """Verifies that an execution ID is reused if supplied in parameters or metadata."""
    state_manager = ExecutionStateManager()
    engine = ExecutionEngine(state_manager=state_manager)

    custom_id = "11111111-2222-3333-4444-555555555555"
    plan = RoutedExecutionPlan(
        intent=Intent.MUTE,
        target="volume",
        parameters={"execution_id": custom_id},
        confidence=1.0,
        routes=[CapabilityRoute(step_id="step_1", intent=Intent.MUTE, capability_name="desktop")],
    )

    summary = engine.execute_plan(plan, mock_dispatcher)
    assert summary.execution_id == custom_id
    assert state_manager.get_execution(custom_id) is not None


def test_runtime_dependency_injection(mock_dispatcher) -> None:
    """Verifies that execution engine defaults or reuses the injected state manager."""
    engine = ExecutionEngine()
    assert isinstance(engine._state_manager, ExecutionStateManager)

    state_manager = ExecutionStateManager()
    engine_injected = ExecutionEngine(state_manager=state_manager)
    assert engine_injected._state_manager is state_manager


def test_runtime_state_manager_failures_ignored(mock_dispatcher) -> None:
    """Verifies that state manager exceptions never halt/interrupt execution."""
    state_manager = ExecutionStateManager()
    # Stub create_execution to raise an exception
    state_manager.create_execution = MagicMock(side_effect=RuntimeError("State database crash"))

    engine = ExecutionEngine(state_manager=state_manager)
    plan = RoutedExecutionPlan(
        intent=Intent.MUTE,
        target="volume",
        confidence=1.0,
        routes=[CapabilityRoute(step_id="step_1", intent=Intent.MUTE, capability_name="desktop")],
    )

    # Execute should succeed fully despite the state manager failure
    summary = engine.execute_plan(plan, mock_dispatcher)
    assert summary.success is True
