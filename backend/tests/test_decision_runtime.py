"""End-to-end integration tests for DecisionEngine runtime flow."""

from __future__ import annotations

import logging
# pyrefly: ignore [missing-import]
import pytest
from typing import Any, Dict

from brain.capability.models import RoutedExecutionPlan, CapabilityRoute
from core.models import Intent
from brain.execution.execution_state import ExecutionStatus
from brain.execution.execution_state_manager import ExecutionStateManager
from brain.execution.execution_engine import ExecutionEngine
from brain.execution.decision_engine import (
    DecisionEngine,
    DecisionContext,
    DecisionType,
    DecisionReason,
    ExecutionDecision,
)


class MockDispatcher:
    """Mock dispatcher tracking calls and returning mock responses."""
    def __init__(self, should_fail: bool = False) -> None:
        self.dispatched_plans = []
        self.should_fail = should_fail

    def dispatch(self, plan: Any) -> Any:
        self.dispatched_plans.append(plan)
        class MockResult:
            success = not self.should_fail
            execution_time = 0.05
            response = "Dispatched successfully"
            error = None if not self.should_fail else "Dispatch execution failure"
            data = {}
        return MockResult()


def test_runtime_execute_decision() -> None:
    """Verifies standard execute path runs the dispatcher."""
    dispatcher = MockDispatcher()
    engine = ExecutionEngine()
    
    plan = RoutedExecutionPlan(
        target="some_target",
        intent=Intent.OPEN_APPLICATION,
        parameters={"app_name": "notepad", "execution_id": "exec_1"},
        confidence=1.0,
        routes=[CapabilityRoute(step_id="step_1", intent=Intent.OPEN_APPLICATION, capability_name="mock_cap")],
    )
    
    summary = engine.execute_plan(plan, dispatcher, user_id=42)
    assert summary.success is True
    assert len(dispatcher.dispatched_plans) == 1


def test_runtime_reuse_resource() -> None:
    """Verifies that REUSE_RESOURCE skips the dispatcher and marks step successful."""
    dispatcher = MockDispatcher()
    # Construct a decision engine that always returns REUSE_RESOURCE for vscode
    class VSCodeReuseDecisionEngine(DecisionEngine):
        def evaluate(self, context: DecisionContext) -> ExecutionDecision:
            if context.capability_metadata and context.capability_metadata.get("vscode_running"):
                return ExecutionDecision(
                    decision_type=DecisionType.REUSE_RESOURCE,
                    reason=DecisionReason.RESOURCE_ALREADY_AVAILABLE,
                    message="VS Code is already running, reusing",
                    recommended_action="Reuse active VS Code instance",
                )
            return super().evaluate(context)

    engine = ExecutionEngine(decision_engine=VSCodeReuseDecisionEngine())
    plan = RoutedExecutionPlan(
        target="vscode",
        intent=Intent.OPEN_APPLICATION,
        parameters={"vscode_running": True, "execution_id": "exec_reuse"},
        confidence=1.0,
        routes=[CapabilityRoute(step_id="step_1", intent=Intent.OPEN_APPLICATION, capability_name="mock_cap")],
    )

    summary = engine.execute_plan(plan, dispatcher, user_id=42)
    assert summary.success is True
    # The dispatcher should be skipped completely because resource is reused
    assert len(dispatcher.dispatched_plans) == 0
    
    # Check internal execution metadata retention
    state = engine._state_manager.get_execution("exec_reuse")
    assert state is not None
    assert state.metadata["decision_type"] == "REUSE_RESOURCE"
    assert state.metadata["decision_reason"] == "RESOURCE_ALREADY_AVAILABLE"


def test_runtime_fallback_replacement() -> None:
    """Verifies that USE_FALLBACK replaces the executable target."""
    dispatcher = MockDispatcher()
    class ChromeFallbackDecisionEngine(DecisionEngine):
        def evaluate(self, context: DecisionContext) -> ExecutionDecision:
            if context.capability_metadata and context.capability_metadata.get("missing_executable"):
                return ExecutionDecision(
                    decision_type=DecisionType.USE_FALLBACK,
                    reason=DecisionReason.RESOURCE_NOT_FOUND,
                    message="Chrome missing, fallback to Edge",
                    recommended_action="Launch Edge",
                    metadata={"fallback": "Edge"},
                )
            return super().evaluate(context)

    engine = ExecutionEngine(decision_engine=ChromeFallbackDecisionEngine())
    plan = RoutedExecutionPlan(
        target="chrome",
        intent=Intent.OPEN_APPLICATION,
        parameters={"missing_executable": True, "execution_id": "exec_fallback"},
        confidence=1.0,
        routes=[CapabilityRoute(step_id="step_1", intent=Intent.OPEN_APPLICATION, capability_name="mock_cap")],
    )

    summary = engine.execute_plan(plan, dispatcher, user_id=42)
    assert summary.success is True
    assert len(dispatcher.dispatched_plans) == 1
    # Target should be swapped from chrome to Edge
    assert dispatcher.dispatched_plans[0].target == "Edge"


def test_runtime_wait_decision() -> None:
    """Verifies that WAIT halts execution and returns wait state."""
    dispatcher = MockDispatcher()
    class WaitDecisionEngine(DecisionEngine):
        def evaluate(self, context: DecisionContext) -> ExecutionDecision:
            return ExecutionDecision(
                decision_type=DecisionType.WAIT,
                reason=DecisionReason.DEPENDENCY_NOT_MET,
                message="Missing internet, waiting",
            )

    engine = ExecutionEngine(decision_engine=WaitDecisionEngine())
    plan = RoutedExecutionPlan(
        target="chrome",
        intent=Intent.OPEN_APPLICATION,
        parameters={"execution_id": "exec_wait"},
        confidence=1.0,
        routes=[CapabilityRoute(step_id="step_1", intent=Intent.OPEN_APPLICATION, capability_name="mock_cap")],
    )

    summary = engine.execute_plan(plan, dispatcher, user_id=42)
    assert summary.success is False
    assert len(dispatcher.dispatched_plans) == 0

    state = engine._state_manager.get_execution("exec_wait")
    assert state is not None
    assert state.status == ExecutionStatus.WAITING


def test_runtime_ask_user_decision() -> None:
    """Verifies that ASK_USER halts execution and pauses the run."""
    dispatcher = MockDispatcher()
    class AskUserDecisionEngine(DecisionEngine):
        def evaluate(self, context: DecisionContext) -> ExecutionDecision:
            return ExecutionDecision(
                decision_type=DecisionType.ASK_USER,
                reason=DecisionReason.USER_CONFIRMATION_REQUIRED,
                message="Dangerous command detected",
            )

    engine = ExecutionEngine(decision_engine=AskUserDecisionEngine())
    plan = RoutedExecutionPlan(
        target="cmd",
        intent=Intent.OPEN_APPLICATION,
        parameters={"execution_id": "exec_ask"},
        confidence=1.0,
        routes=[CapabilityRoute(step_id="step_1", intent=Intent.OPEN_APPLICATION, capability_name="mock_cap")],
    )

    summary = engine.execute_plan(plan, dispatcher, user_id=42)
    assert summary.success is False
    assert len(dispatcher.dispatched_plans) == 0

    state = engine._state_manager.get_execution("exec_ask")
    assert state is not None
    assert state.status in (ExecutionStatus.PAUSED, ExecutionStatus.WAITING_FOR_CONFIRMATION)


def test_runtime_cancel_execution() -> None:
    """Verifies CANCEL halts execution immediately and cancels it."""
    dispatcher = MockDispatcher()
    class CancelDecisionEngine(DecisionEngine):
        def evaluate(self, context: DecisionContext) -> ExecutionDecision:
            return ExecutionDecision(
                decision_type=DecisionType.CANCEL,
                reason=DecisionReason.UNKNOWN,
                message="Workspace lock error",
            )

    engine = ExecutionEngine(decision_engine=CancelDecisionEngine())
    plan = RoutedExecutionPlan(
        target="cmd",
        intent=Intent.OPEN_APPLICATION,
        parameters={"execution_id": "exec_cancel"},
        confidence=1.0,
        routes=[CapabilityRoute(step_id="step_1", intent=Intent.OPEN_APPLICATION, capability_name="mock_cap")],
    )

    summary = engine.execute_plan(plan, dispatcher, user_id=42)
    assert summary.success is False
    assert len(dispatcher.dispatched_plans) == 0

    state = engine._state_manager.get_execution("exec_cancel")
    assert state is not None
    assert state.status == ExecutionStatus.CANCELLED


def test_runtime_skip_step() -> None:
    """Verifies SKIP bypasses the dispatcher for a step and proceeds."""
    dispatcher = MockDispatcher()
    class SkipDecisionEngine(DecisionEngine):
        def evaluate(self, context: DecisionContext) -> ExecutionDecision:
            return ExecutionDecision(
                decision_type=DecisionType.SKIP,
                reason=DecisionReason.PREFERENCE_MATCH,
                message="Skip configuration check",
            )

    engine = ExecutionEngine(decision_engine=SkipDecisionEngine())
    plan = RoutedExecutionPlan(
        target="cmd",
        intent=Intent.OPEN_APPLICATION,
        parameters={"execution_id": "exec_skip"},
        confidence=1.0,
        routes=[
            CapabilityRoute(step_id="step_1", intent=Intent.OPEN_APPLICATION, capability_name="mock_cap1"),
            CapabilityRoute(step_id="step_2", intent=Intent.OPEN_APPLICATION, capability_name="mock_cap2"),
        ],
    )

    summary = engine.execute_plan(plan, dispatcher, user_id=42)
    # The whole execution succeeds because skipped step is marked SUCCESS
    assert summary.success is True
    # Bypassed dispatch entirely for both steps
    assert len(dispatcher.dispatched_plans) == 0


def test_runtime_retry_handling() -> None:
    """Verifies RETRY decision transitions state to RETRYING."""
    dispatcher = MockDispatcher()
    class RetryDecisionEngine(DecisionEngine):
        def evaluate(self, context: DecisionContext) -> ExecutionDecision:
            return ExecutionDecision(
                decision_type=DecisionType.RETRY,
                reason=DecisionReason.RECOVERABLE_FAILURE,
                message="Temporary network issue",
            )

    engine = ExecutionEngine(decision_engine=RetryDecisionEngine())
    plan = RoutedExecutionPlan(
        target="cmd",
        intent=Intent.OPEN_APPLICATION,
        parameters={"execution_id": "exec_retry"},
        confidence=1.0,
        routes=[CapabilityRoute(step_id="step_1", intent=Intent.OPEN_APPLICATION, capability_name="mock_cap")],
    )

    summary = engine.execute_plan(plan, dispatcher, user_id=42)
    assert summary.success is True
    assert len(dispatcher.dispatched_plans) == 1
    
    state = engine._state_manager.get_execution("exec_retry")
    assert state is not None
    # Will eventually complete successfully since dispatcher succeeds, but metadata will have RETRY
    assert state.metadata["decision_type"] == "RETRY"


def test_runtime_decision_engine_failure_fallback() -> None:
    """Verifies that decision engine runtime exceptions default to EXECUTE safely."""
    dispatcher = MockDispatcher()
    class ExplodingDecisionEngine(DecisionEngine):
        def evaluate(self, context: DecisionContext) -> ExecutionDecision:
            raise RuntimeError("Out of bounds index error inside logic")

    engine = ExecutionEngine(decision_engine=ExplodingDecisionEngine())
    plan = RoutedExecutionPlan(
        target="cmd",
        intent=Intent.OPEN_APPLICATION,
        parameters={"execution_id": "exec_explode"},
        confidence=1.0,
        routes=[CapabilityRoute(step_id="step_1", intent=Intent.OPEN_APPLICATION, capability_name="mock_cap")],
    )

    # Should run successfully despite the decision engine throwing an exception
    summary = engine.execute_plan(plan, dispatcher, user_id=42)
    assert summary.success is True
    assert len(dispatcher.dispatched_plans) == 1


def test_runtime_dependency_injection() -> None:
    """Verifies default constructor instantiates default DecisionEngine."""
    engine = ExecutionEngine()
    assert isinstance(engine._decision_engine, DecisionEngine)
