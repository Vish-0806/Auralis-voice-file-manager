"""Unit and integration tests for runtime clarification engine loop."""

from __future__ import annotations

import logging
# pyrefly: ignore [missing-import]
import pytest
from typing import Any

from brain.capability.models import RoutedExecutionPlan, CapabilityRoute
from core.models import Intent
from brain.execution.execution_state import ExecutionStatus
from brain.execution.execution_state_manager import ExecutionStateManager
from brain.execution.execution_engine import ExecutionEngine
from brain.execution.clarification_engine import (
    ClarificationEngine,
    ClarificationContext,
    ClarificationRequest,
    ClarificationChoice,
    ClarificationType,
)


class MockDispatcher:
    """Mock dispatcher that records details of dispatcher requests."""
    def __init__(self) -> None:
        self.dispatched = []

    def dispatch(self, plan: Any) -> Any:
        self.dispatched.append(plan)
        class MockResult:
            success = True
            execution_time = 0.01
            response = "Execution succeeded"
            data = {}
        return MockResult()


def test_clarification_runtime_generated_and_suspended() -> None:
    """Verifies that when target is missing, a clarification is generated and execution suspends."""
    dispatcher = MockDispatcher()
    engine = ExecutionEngine()
    
    # Missing target trigger missing target clarification
    plan = RoutedExecutionPlan(
        target="",
        intent=Intent.OPEN_APPLICATION,
        parameters={"execution_id": "exec_suspend_1"},
        confidence=1.0,
        routes=[CapabilityRoute(step_id="step_1", intent=Intent.OPEN_APPLICATION, capability_name="mock_cap")],
    )

    summary = engine.execute_plan(plan, dispatcher)
    assert summary.success is False
    assert len(dispatcher.dispatched) == 0

    state = engine._state_manager.get_execution("exec_suspend_1")
    assert state is not None
    # Verifies waiting state stored
    from brain.execution.execution_state import ExecutionStatus as StateStatus
    assert state.status == StateStatus.WAITING_FOR_CONFIRMATION
    assert state.waiting_for_confirmation is True
    assert state.clarification_request_id == "clar_req_1"
    assert state.clarification_reason == "Clarification required before task execution."


def test_clarification_runtime_no_clarification_path() -> None:
    """Verifies normal execution when no clarification is required."""
    dispatcher = MockDispatcher()
    engine = ExecutionEngine()
    
    plan = RoutedExecutionPlan(
        target="Chrome",
        intent=Intent.OPEN_APPLICATION,
        parameters={"execution_id": "exec_normal_run"},
        confidence=1.0,
        routes=[CapabilityRoute(step_id="step_1", intent=Intent.OPEN_APPLICATION, capability_name="mock_cap")],
    )

    summary = engine.execute_plan(plan, dispatcher)
    assert summary.success is True
    assert len(dispatcher.dispatched) == 1

    state = engine._state_manager.get_execution("exec_normal_run")
    assert state is not None
    assert state.waiting_for_confirmation is False


def test_clarification_runtime_multiple_projects_selection() -> None:
    """Verifies that multiple projects in workspace trigger WORKSPACE_SELECTION."""
    dispatcher = MockDispatcher()
    engine = ExecutionEngine()
    
    plan = RoutedExecutionPlan(
        target="project",
        intent=Intent.DELETE_FOLDER,
        parameters={
            "execution_id": "exec_project_select",
            "multiple_projects": True,
        },
        confidence=1.0,
        routes=[CapabilityRoute(step_id="step_1", intent=Intent.DELETE_FOLDER, capability_name="mock_cap")],
    )

    summary = engine.execute_plan(plan, dispatcher)
    assert summary.success is False

    state = engine._state_manager.get_execution("exec_project_select")
    assert state is not None
    assert state.waiting_for_confirmation is True


def test_clarification_runtime_confirmation_requests() -> None:
    """Verifies confirmation requests for high-risk locations (Downloads)."""
    dispatcher = MockDispatcher()
    engine = ExecutionEngine()
    
    plan = RoutedExecutionPlan(
        target="Downloads",
        intent=Intent.DELETE_FOLDER,
        parameters={"execution_id": "exec_downloads_confirm", "needs_confirmation": True},
        confidence=1.0,
        routes=[CapabilityRoute(step_id="step_1", intent=Intent.DELETE_FOLDER, capability_name="mock_cap")],
    )

    summary = engine.execute_plan(plan, dispatcher)
    assert summary.success is False

    state = engine._state_manager.get_execution("exec_downloads_confirm")
    assert state is not None
    assert state.waiting_for_confirmation is True


def test_clarification_runtime_dependency_injection() -> None:
    """Verifies constructor dependency injection of ClarificationEngine."""
    engine = ExecutionEngine()
    assert isinstance(engine._clarification_engine, ClarificationEngine)


def test_clarification_runtime_engine_failure_fallback() -> None:
    """Verifies safety: if ClarificationEngine crashes, execution engine does not crash and runs normally."""
    dispatcher = MockDispatcher()

    class ExplodingClarificationEngine(ClarificationEngine):
        def generate_request(self, context: ClarificationContext) -> ClarificationRequest | None:
            raise RuntimeError("Database unavailable")

    engine = ExecutionEngine(clarification_engine=ExplodingClarificationEngine())
    plan = RoutedExecutionPlan(
        target="",
        intent=Intent.OPEN_APPLICATION,
        parameters={"execution_id": "exec_engine_crash"},
        confidence=1.0,
        routes=[CapabilityRoute(step_id="step_1", intent=Intent.OPEN_APPLICATION, capability_name="mock_cap")],
    )

    # ClarificationEngine crashed, falls back to legacy ASK_USER pause behavior
    summary = engine.execute_plan(plan, dispatcher)
    assert summary.success is False


def test_clarification_runtime_logging_entries(caplog: pytest.LogCaptureFixture) -> None:
    """Verifies that runtime generates expected logs."""
    dispatcher = MockDispatcher()
    engine = ExecutionEngine()

    plan = RoutedExecutionPlan(
        target="",
        intent=Intent.OPEN_APPLICATION,
        parameters={"execution_id": "exec_logging_run"},
        confidence=1.0,
        routes=[CapabilityRoute(step_id="step_1", intent=Intent.OPEN_APPLICATION, capability_name="mock_cap")],
    )

    with caplog.at_level("INFO"):
        engine.execute_plan(plan, dispatcher)

    log_messages = [record.message for record in caplog.records]
    assert any("Clarification Requested" in msg for msg in log_messages)
    assert any("Execution Suspended" in msg for msg in log_messages)
    assert any("Awaiting User Confirmation" in msg for msg in log_messages)


def test_clarification_runtime_logging_not_required(caplog: pytest.LogCaptureFixture) -> None:
    """Verifies logs when clarification is not required."""
    dispatcher = MockDispatcher()
    engine = ExecutionEngine()

    plan = RoutedExecutionPlan(
        target="Chrome",
        intent=Intent.OPEN_APPLICATION,
        parameters={"execution_id": "exec_not_req_logging"},
        confidence=1.0,
        routes=[CapabilityRoute(step_id="step_1", intent=Intent.OPEN_APPLICATION, capability_name="mock_cap")],
    )

    # To trigger the check and NOT require clarification, decision must be ASK_USER but clarification engine returns None
    class CustomDecisionEngine:
        def evaluate(self, context: Any) -> Any:
            from brain.execution.decision_engine import ExecutionDecision, DecisionType, DecisionReason
            return ExecutionDecision(
                decision_type=DecisionType.ASK_USER,
                reason=DecisionReason.USER_CONFIRMATION_REQUIRED,
                confidence=1.0,
                message="Triggering ASK_USER decision check"
            )

    class NullClarificationEngine(ClarificationEngine):
        def generate_request(self, context: ClarificationContext) -> ClarificationRequest | None:
            return None

    engine._decision_engine = CustomDecisionEngine()
    engine._clarification_engine = NullClarificationEngine()

    with caplog.at_level("INFO"):
        engine.execute_plan(plan, dispatcher)

    log_messages = [record.message for record in caplog.records]
    assert any("Clarification Not Required" in msg for msg in log_messages)
    assert any("Execution Resumed Ready" in msg for msg in log_messages)


def test_clarification_runtime_state_preservation() -> None:
    """Verifies that progress and map data are preserved when execution is suspended."""
    dispatcher = MockDispatcher()
    engine = ExecutionEngine()

    plan = RoutedExecutionPlan(
        target="",
        intent=Intent.OPEN_APPLICATION,
        parameters={"execution_id": "exec_state_preservation"},
        confidence=1.0,
        routes=[
            CapabilityRoute(step_id="step_1", intent=Intent.OPEN_APPLICATION, capability_name="mock_cap"),
            CapabilityRoute(step_id="step_2", intent=Intent.OPEN_APPLICATION, capability_name="mock_cap"),
        ],
    )

    engine.execute_plan(plan, dispatcher)
    state = engine._state_manager.get_execution("exec_state_preservation")
    assert state is not None
    assert state.waiting_for_confirmation is True
    # Verification that it stopped before running any step, but step mapping and basic fields are preserved
    assert len(state.completed_steps) == 0


def test_clarification_runtime_parameter_validation() -> None:
    """Verifies missing parameter detection triggers clarification requests."""
    dispatcher = MockDispatcher()
    engine = ExecutionEngine()

    plan = RoutedExecutionPlan(
        target="file.txt",
        intent=Intent.DRAG_DROP,
        parameters={
            "execution_id": "exec_param_validate",
            "destination": None,  # Parameter missing
        },
        confidence=1.0,
        routes=[CapabilityRoute(step_id="step_1", intent=Intent.DRAG_DROP, capability_name="mock_cap")],
    )

    engine.execute_plan(plan, dispatcher)
    state = engine._state_manager.get_execution("exec_param_validate")
    assert state is not None
    assert state.waiting_for_confirmation is True
    assert state.clarification_reason == "Clarification required before task execution."


def test_clarification_runtime_backward_compatibility() -> None:
    """Verifies backward compatibility: simple plans execute without crashing."""
    dispatcher = MockDispatcher()
    engine = ExecutionEngine()

    plan = RoutedExecutionPlan(
        target="Chrome",
        intent=Intent.OPEN_APPLICATION,
        confidence=1.0,
        routes=[CapabilityRoute(step_id="step_1", intent=Intent.OPEN_APPLICATION, capability_name="mock_cap")],
    )

    summary = engine.execute_plan(plan, dispatcher)
    assert summary.success is True

