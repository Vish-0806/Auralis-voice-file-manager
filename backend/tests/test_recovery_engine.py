"""Unit tests for the Auralis Self-Correction and Recovery subsystem."""

from __future__ import annotations

from unittest.mock import MagicMock
# pyrefly: ignore [missing-import]
import pytest

from core.intents import Intent
from core.models import ExecutionResult
from brain.capability.models import RoutedExecutionPlan, CapabilityRoute
from brain.execution.models import ExecutionStatus, ExecutionSummary
from brain.execution.execution_engine import ExecutionEngine
from brain.recovery.models import FailureType, FallbackOption, RecoveryStrategy, RecoveryResult as RecoveryResultModel
from brain.recovery.fallback_registry import FallbackRegistry
from brain.recovery.failure_analyzer import FailureAnalyzer
from brain.recovery.recovery_strategy import RecoveryStrategyBuilder
from brain.recovery.recovery_engine import RecoveryEngine


# --- Models Validation Tests ---

def test_recovery_models_validation():
    """Validates that FailureType, FallbackOption, RecoveryStrategy, and RecoveryResult can be instantiated."""
    fallback = FallbackOption(original="AppA", fallback="AppB", requires_confirmation=True)
    assert fallback.original == "AppA"
    assert fallback.fallback == "AppB"
    assert fallback.requires_confirmation is True

    result = RecoveryResultModel(
        success=True,
        strategy_applied="Resolve_APPLICATION_NOT_FOUND",
    )
    assert result.success is True
    assert result.strategy_applied == "Resolve_APPLICATION_NOT_FOUND"


# --- Failure Analyzer Tests ---

def test_failure_analyzer_classification():
    """Validates error message parsing into FailureType categories."""
    analyzer = FailureAnalyzer()

    assert analyzer.analyze_failure("Could not resolve executable path for Chrome") == FailureType.APPLICATION_NOT_FOUND
    assert analyzer.analyze_failure("FileNotFoundError: no such file test.txt") == FailureType.FILE_NOT_FOUND
    assert analyzer.analyze_failure("PermissionError: access denied") == FailureType.PERMISSION_DENIED
    assert analyzer.analyze_failure("socket.error: Host is offline") == FailureType.NETWORK_UNAVAILABLE
    assert analyzer.analyze_failure("TimeoutError: operation expired") == FailureType.TIMEOUT
    assert analyzer.analyze_failure("Something went wrong") == FailureType.UNKNOWN


# --- Fallback Registry Tests ---

def test_fallback_registry():
    """Validates fallback mappings and custom registry registrations."""
    registry = FallbackRegistry()

    # Default mappings
    assert registry.has_fallback("Chrome") is True
    assert registry.get_fallback("Chrome").fallback == "Microsoft Edge"
    assert registry.get_fallback("Chrome").requires_confirmation is False

    assert registry.get_fallback("Admin Command Prompt").requires_confirmation is True

    # Custom mapping
    registry.register_fallback("OriginalApp", "FallbackApp", requires_confirmation=False)
    assert registry.has_fallback("OriginalApp") is True
    assert registry.get_fallback("OriginalApp").fallback == "FallbackApp"


# --- Recovery Strategy Builder Tests ---

def test_recovery_strategy_builder():
    """Validates building recovery strategies for failures."""
    builder = RecoveryStrategyBuilder()

    # App fallback strategy
    strategy = builder.build_strategy(
        failure_type=FailureType.APPLICATION_NOT_FOUND,
        step_id="step_1",
        intent=Intent.OPEN_APPLICATION,
        target="Chrome",
        parameters={},
        fallback=FallbackOption(original="Chrome", fallback="Microsoft Edge"),
    )
    assert strategy is not None
    assert strategy.name == "Resolve_APPLICATION_NOT_FOUND"
    assert len(strategy.remediation_actions) == 1
    assert strategy.remediation_actions[0].target == "Microsoft Edge"


# --- Recovery Engine Tests ---

def test_recovery_engine_success():
    """Validates successful recovery strategy execution."""
    engine = RecoveryEngine()

    mock_dispatcher = MagicMock()
    mock_dispatcher.dispatch.return_value = ExecutionResult(success=True, response="Running Edge", execution_time=0.01)

    result = engine.recover(
        step_id="step_1",
        intent=Intent.OPEN_APPLICATION,
        target="Chrome",
        parameters={},
        error_message="Could not resolve executable path for Chrome",
        dispatcher=mock_dispatcher,
    )

    assert result.success is True
    assert result.strategy_applied == "Resolve_APPLICATION_NOT_FOUND"
    assert len(result.remediation_actions) == 1
    assert result.remediation_actions[0].target == "Microsoft Edge"
    mock_dispatcher.dispatch.assert_called_once()


def test_recovery_engine_aborted_by_confirmation():
    """Validates that recovery aborts if target requires user confirmation."""
    engine = RecoveryEngine()
    mock_dispatcher = MagicMock()

    result = engine.recover(
        step_id="step_1",
        intent=Intent.OPEN_APPLICATION,
        target="Admin Command Prompt",
        parameters={},
        error_message="Permission denied",
        dispatcher=mock_dispatcher,
    )

    assert result.success is False
    assert result.strategy_applied == "UserConfirmationRequired"
    assert "user confirmation required" in result.error.lower()
    mock_dispatcher.dispatch.assert_not_called()


# --- Execution Engine Integration Tests ---

def test_execution_engine_recovery_integration():
    """Validates that successful recovery lets sequential step execution resume."""
    from automation.workflow.models import WorkflowDefinition, WorkflowStep
    from automation.workflow.workflow_registry import WorkflowRegistry
    
    # Register dynamic workflow with expected step targets
    WorkflowRegistry._dynamic_registry["Custom Study Mode"] = WorkflowDefinition(
        name="Custom Study Mode",
        description="Test mode with Chrome",
        steps=[
            WorkflowStep(intent=Intent.OPEN_APPLICATION, target="Chrome"),
            WorkflowStep(intent=Intent.MUTE),
        ],
    )

    engine = ExecutionEngine()

    mock_dispatcher = MagicMock()
    mock_dispatcher._capabilities = {"desktop": MagicMock()}
    
    # First dispatch fails (Chrome not found), recovery succeeds (Edge launches), second step succeeds
    mock_dispatcher.dispatch.side_effect = [
        ExecutionResult(success=False, response="", error="Could not resolve executable path for Chrome", execution_time=0.01),  # Step 1 fails
        ExecutionResult(success=True, response="Running Edge", execution_time=0.01),  # Recovery step succeeds
        ExecutionResult(success=True, response="Muted", execution_time=0.01),  # Step 2 succeeds
    ]

    plan = RoutedExecutionPlan(
        intent=Intent.RUN_WORKFLOW,
        target="Custom Study Mode",
        confidence=1.0,
        routes=[
            CapabilityRoute(step_id="step_1", intent=Intent.OPEN_APPLICATION, capability_name="Desktop"),
            CapabilityRoute(step_id="step_2", intent=Intent.MUTE, capability_name="Desktop"),
        ],
    )

    summary = engine.execute_plan(plan, mock_dispatcher)
    
    # Clean up registry
    WorkflowRegistry._dynamic_registry.pop("Custom Study Mode", None)

    assert summary.success is True
    assert len(summary.records) == 2
    assert summary.records[0].status == ExecutionStatus.SUCCESS  # Replaced to Success due to recovery
    assert "Recovered via strategy" in summary.records[0].response
    assert summary.records[1].status == ExecutionStatus.SUCCESS
    assert mock_dispatcher.dispatch.call_count == 3
