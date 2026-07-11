"""Unit tests for the Auralis Multi-Step Execution Engine subsystem."""

from __future__ import annotations

from unittest.mock import MagicMock
# pyrefly: ignore [missing-import]
import pytest

from core.intents import Intent
from core.models import ExecutionResult
from brain.capability.models import RoutedExecutionPlan, CapabilityRoute
from brain.execution.models import ExecutionStatus, ExecutionRecord, ExecutionSummary
from brain.execution.execution_context import ExecutionContext
from brain.execution.execution_history import ExecutionHistory
from brain.execution.execution_validator import ExecutionValidator
from brain.execution.execution_scheduler import ExecutionScheduler
from brain.execution.execution_engine import ExecutionEngine


# --- Models Validation Tests ---

def test_execution_models_validation():
    """Validates that ExecutionRecord, ExecutionContext, and ExecutionSummary compile properly."""
    record = ExecutionRecord(
        step_id="1",
        intent=Intent.MUTE,
        capability="Desktop",
        status=ExecutionStatus.SUCCESS,
        duration=0.05,
        response="Muted successfully",
    )
    assert record.step_id == "1"
    assert record.intent == Intent.MUTE
    assert record.status == ExecutionStatus.SUCCESS

    summary = ExecutionSummary(
        execution_id="test_exec",
        success=True,
        records=[record],
        total_duration=0.05,
    )
    assert summary.success is True
    assert len(summary.records) == 1


# --- Execution Context Tests ---

def test_execution_context_tracking():
    """Validates live context tracking of running and completed steps."""
    context = ExecutionContext(execution_id="session_1")
    assert context.model.execution_id == "session_1"
    assert context.model.current_step is None

    # Start a step
    context.start_step(step_id="step_a", capability="Desktop")
    assert context.model.current_step == "step_a"
    assert context.model.current_capability == "Desktop"

    # Complete step
    context.complete_step(step_id="step_a", result={"response": "OK"})
    assert context.model.current_step is None
    assert "step_a" in context.model.completed_steps
    assert context.model.last_execution_result == {"response": "OK"}


# --- Execution History Tests ---

def test_execution_history_logging():
    """Validates logging and retrieving step records from execution history."""
    history = ExecutionHistory()
    record = ExecutionRecord(
        step_id="step_1",
        intent=Intent.LOCK_PC,
        capability="Desktop",
        status=ExecutionStatus.SUCCESS,
        duration=0.1,
    )
    history.record_step(record)
    
    logged = history.get_history()
    assert len(logged) == 1
    assert logged[0].step_id == "step_1"

    history.clear_history()
    assert len(history.get_history()) == 0


# --- Execution Validator Tests ---

def test_execution_validator():
    """Validates plan checks against dispatcher capabilities."""
    validator = ExecutionValidator()

    # Mock dispatcher with capabilities registered
    mock_dispatcher = MagicMock()
    mock_dispatcher._capabilities = {"desktop": MagicMock(), "mock_file": MagicMock()}

    # Valid plan
    plan_valid = RoutedExecutionPlan(
        intent=Intent.MUTE,
        confidence=1.0,
        routes=[CapabilityRoute(step_id="main", intent=Intent.MUTE, capability_name="Desktop")],
    )
    # Should pass without raising error
    validator.validate_plan(plan_valid, mock_dispatcher)

    # Invalid plan with missing capability
    plan_invalid = RoutedExecutionPlan(
        intent=Intent.UNKNOWN,
        confidence=1.0,
        routes=[CapabilityRoute(step_id="main", intent=Intent.UNKNOWN, capability_name="NonExistentCap")],
    )
    with pytest.raises(ValueError) as excinfo:
        validator.validate_plan(plan_invalid, mock_dispatcher)
    assert "is not available" in str(excinfo.value)


# --- Execution Scheduler Tests ---

def test_execution_scheduler():
    """Validates step ordering in sequential scheduler."""
    scheduler = ExecutionScheduler()
    routes = [
        CapabilityRoute(step_id="1", intent=Intent.MUTE, capability_name="Desktop"),
        CapabilityRoute(step_id="2", intent=Intent.SET_VOLUME, capability_name="Desktop"),
    ]
    scheduled = scheduler.schedule_steps(routes)
    assert len(scheduled) == 2
    assert scheduled[0].step_id == "1"
    assert scheduled[1].step_id == "2"


# --- Execution Engine Tests ---

def test_execution_engine_success():
    """Validates that ExecutionEngine executes all steps sequentially when successful."""
    engine = ExecutionEngine()

    # Mock dispatcher executing steps successfully
    mock_dispatcher = MagicMock()
    mock_dispatcher._capabilities = {"desktop": MagicMock()}
    mock_dispatcher.dispatch.return_value = ExecutionResult(
        success=True,
        response="Mock OK",
        execution_time=0.02,
    )

    plan = RoutedExecutionPlan(
        intent=Intent.RUN_WORKFLOW,
        target="Study Mode",
        confidence=1.0,
        routes=[
            CapabilityRoute(step_id="step_1", intent=Intent.OPEN_APPLICATION, capability_name="Desktop"),
            CapabilityRoute(step_id="step_2", intent=Intent.MUTE, capability_name="Desktop"),
        ],
    )

    summary = engine.execute_plan(plan, mock_dispatcher)
    
    assert summary.success is True
    assert len(summary.records) == 2
    assert summary.records[0].status == ExecutionStatus.SUCCESS
    assert summary.records[1].status == ExecutionStatus.SUCCESS
    assert mock_dispatcher.dispatch.call_count == 2


def test_execution_engine_early_failure_abort():
    """Validates that ExecutionEngine aborts remaining steps on first step failure."""
    engine = ExecutionEngine()

    # Mock dispatcher returning failure for step 1
    mock_dispatcher = MagicMock()
    mock_dispatcher._capabilities = {"desktop": MagicMock()}
    mock_dispatcher.dispatch.return_value = ExecutionResult(
        success=False,
        response="Failed to mute",
        error="Hardware mute failure",
        execution_time=0.01,
    )

    plan = RoutedExecutionPlan(
        intent=Intent.RUN_WORKFLOW,
        target="Study Mode",
        confidence=1.0,
        routes=[
            CapabilityRoute(step_id="step_1", intent=Intent.MUTE, capability_name="Desktop"),
            CapabilityRoute(step_id="step_2", intent=Intent.OPEN_APPLICATION, capability_name="Desktop"),
        ],
    )

    summary = engine.execute_plan(plan, mock_dispatcher)
    
    assert summary.success is False
    assert len(summary.records) == 1  # Executed only the first step and aborted
    assert summary.records[0].status == ExecutionStatus.FAILED
    assert summary.records[0].error == "Hardware mute failure"
    assert "Step 'step_1' failed" in summary.error
    assert mock_dispatcher.dispatch.call_count == 1  # Step 2 was never called!
