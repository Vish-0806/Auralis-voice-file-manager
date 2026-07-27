"""Unit tests for the Autonomous Decision Engine."""

from __future__ import annotations

import pytest

from brain.execution.execution_state import ExecutionStatus, ExecutionState
from brain.execution.decision_engine import (
    DecisionType,
    DecisionReason,
    DecisionContext,
    DecisionEngine,
    ExecutionDecision,
)


def test_decision_engine_execute_by_default() -> None:
    """Verifies that the engine returns EXECUTE when there are no issues or matching rules."""
    engine = DecisionEngine()
    context = DecisionContext()
    
    decision = engine.evaluate(context)
    assert decision.decision_type == DecisionType.EXECUTE
    assert decision.reason == DecisionReason.UNKNOWN
    assert decision.confidence == 1.0


def test_decision_engine_reuse_resource_vscode() -> None:
    """Verifies REUSE_RESOURCE is chosen when VS Code is already open."""
    engine = DecisionEngine()
    context = DecisionContext(
        capability_metadata={"vscode_running": True}
    )

    decision = engine.evaluate(context)
    assert decision.decision_type == DecisionType.REUSE_RESOURCE
    assert decision.reason == DecisionReason.RESOURCE_ALREADY_AVAILABLE
    assert decision.recommended_action == "Reuse active VS Code instance"


def test_decision_engine_reuse_resource_app() -> None:
    """Verifies REUSE_RESOURCE is chosen when a specific application is already active."""
    engine = DecisionEngine()
    context = DecisionContext(
        capability_metadata={"app_already_running": True, "app_name": "Chrome"}
    )

    decision = engine.evaluate(context)
    assert decision.decision_type == DecisionType.REUSE_RESOURCE
    assert decision.reason == DecisionReason.APPLICATION_ALREADY_RUNNING
    assert "Chrome" in decision.message


def test_decision_engine_fallback_missing_executable() -> None:
    """Verifies USE_FALLBACK is suggested when an executable is missing on host."""
    engine = DecisionEngine()
    context = DecisionContext(
        capability_metadata={
            "missing_executable": True,
            "original_executable": "Chrome",
            "fallback_executable": "Edge",
        }
    )

    decision = engine.evaluate(context)
    assert decision.decision_type == DecisionType.USE_FALLBACK
    assert decision.reason == DecisionReason.RESOURCE_NOT_FOUND
    assert decision.recommended_action == "Launch using Edge"


def test_decision_engine_dependency_wait() -> None:
    """Verifies WAIT is returned when a dependency is missing."""
    engine = DecisionEngine()
    context = DecisionContext(
        workflow_metadata={
            "missing_dependency": True,
            "dependency_name": "Internet connection",
        }
    )

    decision = engine.evaluate(context)
    assert decision.decision_type == DecisionType.WAIT
    assert decision.reason == DecisionReason.DEPENDENCY_NOT_MET
    assert "Internet connection" in decision.message


def test_decision_engine_confirmation_required() -> None:
    """Verifies ASK_USER is returned when a dangerous operation is detected."""
    engine = DecisionEngine()
    context = DecisionContext(
        workflow_metadata={
            "dangerous_operation": True,
            "operation_description": "rm -rf system roots",
        }
    )

    decision = engine.evaluate(context)
    assert decision.decision_type == DecisionType.ASK_USER
    assert decision.reason == DecisionReason.USER_CONFIRMATION_REQUIRED
    assert "rm -rf system roots" in decision.message


def test_decision_engine_preference_match() -> None:
    """Verifies PREFERENCE_MATCH reason when a user preference default is met."""
    engine = DecisionEngine()
    context = DecisionContext(
        resolved_preferences={"browser": "Firefox"}
    )

    decision = engine.evaluate(context)
    assert decision.decision_type == DecisionType.EXECUTE
    assert decision.reason == DecisionReason.PREFERENCE_MATCH
    assert "Firefox" in decision.message


def test_decision_engine_retry_recommendation() -> None:
    """Verifies RETRY is suggested for recoverable failures below threshold."""
    engine = DecisionEngine()
    state = ExecutionState(execution_id="exec_1", user_id=1)
    state.status = ExecutionStatus.FAILED
    state.retry_count = 1  # 1 retry made, below max of 3

    context = DecisionContext(execution_state=state)
    decision = engine.evaluate(context)
    
    assert decision.decision_type == DecisionType.RETRY
    assert decision.reason == DecisionReason.RECOVERABLE_FAILURE


def test_decision_engine_cancel_on_invalid_context() -> None:
    """Verifies that passing None/invalid context returns CANCEL decision."""
    engine = DecisionEngine()
    decision = engine.evaluate(None)
    
    assert decision.decision_type == DecisionType.CANCEL
    assert decision.reason == DecisionReason.UNKNOWN
    assert decision.confidence == 0.0


def test_decision_engine_deterministic_outputs() -> None:
    """Verifies that decision evaluations are completely deterministic."""
    engine = DecisionEngine()
    context = DecisionContext(
        workflow_metadata={
            "dangerous_operation": True,
            "operation_description": "Delete workspace",
        }
    )

    # Calling it multiple times should always yield the exact same decision content
    dec1 = engine.evaluate(context)
    dec2 = engine.evaluate(context)
    assert dec1.model_dump() == dec2.model_dump()
