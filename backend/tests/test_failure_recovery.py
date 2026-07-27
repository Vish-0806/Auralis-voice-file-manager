"""Unit tests for the Failure Recovery Engine."""

from __future__ import annotations

# pyrefly: ignore [missing-import]
import pytest

from brain.execution.failure_recovery import (
    FailureCategory,
    RecoveryStrategy,
    FailureAnalysis,
    RecoveryPlan,
    RecoveryContext,
    FailureRecoveryEngine,
)


def test_classify_file_not_found() -> None:
    """Verifies that FileNotFoundError maps to RESOURCE_NOT_FOUND category."""
    engine = FailureRecoveryEngine()
    category = engine.classify_exception(FileNotFoundError("Configuration file missing"))
    assert category == FailureCategory.RESOURCE_NOT_FOUND


def test_classify_permission_error() -> None:
    """Verifies that PermissionError maps to PERMISSION_DENIED category."""
    engine = FailureRecoveryEngine()
    category = engine.classify_exception(PermissionError("Unauthorized folder access"))
    assert category == FailureCategory.PERMISSION_DENIED


def test_classify_timeout_error() -> None:
    """Verifies that TimeoutError maps to TIMEOUT category."""
    engine = FailureRecoveryEngine()
    category = engine.classify_exception(TimeoutError("Response timeout exceeded"))
    assert category == FailureCategory.TIMEOUT


def test_classify_connection_error() -> None:
    """Verifies that ConnectionError maps to NETWORK_ERROR category."""
    engine = FailureRecoveryEngine()
    category = engine.classify_exception(ConnectionError("Refused tcp link connection"))
    assert category == FailureCategory.NETWORK_ERROR


def test_classify_unknown_exception() -> None:
    """Verifies that generic exceptions map to UNKNOWN category."""
    engine = FailureRecoveryEngine()
    category = engine.classify_exception(ValueError("Invalid float parse"))
    assert category == FailureCategory.UNKNOWN


def test_recoverable_classification() -> None:
    """Verifies recoverable boolean status on recoverable analysis results."""
    engine = FailureRecoveryEngine()
    context = RecoveryContext(exception=TimeoutError("Request timed out"))
    
    analysis = engine.analyse_failure(context)
    assert analysis.recoverable is True
    assert analysis.confidence == 1.0


def test_non_recoverable_classification() -> None:
    """Verifies recoverable boolean status is False for unknown classification outcomes."""
    engine = FailureRecoveryEngine()
    context = RecoveryContext(exception=ValueError("Invalid index configuration"))
    
    analysis = engine.analyse_failure(context)
    assert analysis.recoverable is False
    assert analysis.confidence == 0.5


def test_retry_strategy_recommendation() -> None:
    """Verifies RETRY strategy is recommended for timeout failures."""
    engine = FailureRecoveryEngine()
    context = RecoveryContext(exception=TimeoutError("Request timed out"))
    
    plan = engine.build_recovery_plan(context)
    assert plan.strategy == RecoveryStrategy.RETRY
    assert plan.wait_seconds == 0.0
    assert plan.requires_user_confirmation is False


def test_wait_strategy_recommendation() -> None:
    """Verifies WAIT strategy is recommended for network failures."""
    engine = FailureRecoveryEngine()
    context = RecoveryContext(exception=ConnectionError("TCP connection lost"))
    
    plan = engine.build_recovery_plan(context)
    assert plan.strategy == RecoveryStrategy.WAIT
    assert plan.wait_seconds == 10.0
    assert plan.requires_user_confirmation is False


def test_fallback_strategy_recommendation() -> None:
    """Verifies USE_FALLBACK strategy is recommended for missing resource/files."""
    engine = FailureRecoveryEngine()
    context = RecoveryContext(
        exception=FileNotFoundError("Chrome.exe missing"),
        resolved_preferences={"fallback": "Edge.exe"}
    )
    
    plan = engine.build_recovery_plan(context)
    assert plan.strategy == RecoveryStrategy.USE_FALLBACK
    assert plan.fallback_resource == "Edge.exe"
    assert plan.requires_user_confirmation is False


def test_abort_strategy_recommendation() -> None:
    """Verifies ABORT strategy is recommended for generic unknown errors."""
    engine = FailureRecoveryEngine()
    context = RecoveryContext(exception=ValueError("Parsing metadata failed"))
    
    plan = engine.build_recovery_plan(context)
    assert plan.strategy == RecoveryStrategy.ABORT
    assert plan.recommended_action == "Clean up and cancel parent pipeline run"


def test_recovery_outputs_deterministic() -> None:
    """Verifies recovery engine execution outputs are fully deterministic."""
    engine = FailureRecoveryEngine()
    context = RecoveryContext(exception=PermissionError("System level access denied"))
    
    plan1 = engine.build_recovery_plan(context)
    plan2 = engine.build_recovery_plan(context)
    assert plan1.model_dump() == plan2.model_dump()
