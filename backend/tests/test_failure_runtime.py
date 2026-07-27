"""Integration tests for failure recovery analysis during runtime execution."""

from __future__ import annotations

import logging
import pytest
from typing import Any

from brain.capability.models import RoutedExecutionPlan, CapabilityRoute
from core.models import Intent
from brain.execution.execution_state import ExecutionStatus
from brain.execution.execution_state_manager import ExecutionStateManager
from brain.execution.execution_engine import ExecutionEngine
from brain.execution.failure_recovery import (
    FailureRecoveryEngine,
    RecoveryContext,
    FailureCategory,
    RecoveryStrategy,
    RecoveryPlan,
)


class MockDispatcher:
    """Mock dispatcher that can raise custom exceptions upon request."""
    def __init__(self, exception_to_raise: Exception | None = None, return_failure: bool = False, failure_error: str = "") -> None:
        self.exception_to_raise = exception_to_raise
        self.return_failure = return_failure
        self.failure_error = failure_error
        self.dispatched = []

    def dispatch(self, plan: Any) -> Any:
        self.dispatched.append(plan)
        if self.exception_to_raise is not None:
            raise self.exception_to_raise
        
        class MockResult:
            success = not self.return_failure
            execution_time = 0.05
            response = "Dispatched" if not self.return_failure else ""
            error = self.failure_error if self.return_failure else None
            data = {}
        return MockResult()


def test_failure_runtime_filenotfound() -> None:
    """Verifies that FileNotFoundError is analyzed as RESOURCE_NOT_FOUND and USE_FALLBACK."""
    dispatcher = MockDispatcher(exception_to_raise=FileNotFoundError("Chrome.exe missing"))
    engine = ExecutionEngine()
    
    plan = RoutedExecutionPlan(
        target="chrome",
        intent=Intent.OPEN_APPLICATION,
        parameters={"execution_id": "exec_fnf"},
        confidence=1.0,
        routes=[CapabilityRoute(step_id="step_1", intent=Intent.OPEN_APPLICATION, capability_name="mock_cap")],
    )

    # Execute plan (which fails, recovery engine is run, but fails overall without auto-correction in this phase)
    summary = engine.execute_plan(plan, dispatcher, user_id=42)
    assert summary.success is False

    # Verify metadata on the state manager
    state = engine._state_manager.get_execution("exec_fnf")
    assert state is not None
    assert state.metadata["failure_category"] == "RESOURCE_NOT_FOUND"
    assert state.metadata["recovery_strategy"] == "USE_FALLBACK"
    assert state.metadata["recoverable"] is True


def test_failure_runtime_permissionerror() -> None:
    """Verifies that PermissionError maps to PERMISSION_DENIED and ASK_USER."""
    dispatcher = MockDispatcher(exception_to_raise=PermissionError("Admin rights required"))
    engine = ExecutionEngine()
    
    plan = RoutedExecutionPlan(
        target="system",
        intent=Intent.OPEN_APPLICATION,
        parameters={"execution_id": "exec_perm"},
        confidence=1.0,
        routes=[CapabilityRoute(step_id="step_1", intent=Intent.OPEN_APPLICATION, capability_name="mock_cap")],
    )

    summary = engine.execute_plan(plan, dispatcher, user_id=42)
    assert summary.success is False

    state = engine._state_manager.get_execution("exec_perm")
    assert state is not None
    assert state.metadata["failure_category"] == "PERMISSION_DENIED"
    assert state.metadata["recovery_strategy"] == "ASK_USER"
    assert state.metadata["recoverable"] is True


def test_failure_runtime_timeouterror() -> None:
    """Verifies that TimeoutError maps to TIMEOUT and RETRY."""
    dispatcher = MockDispatcher(exception_to_raise=TimeoutError("Network timed out"))
    engine = ExecutionEngine()
    
    plan = RoutedExecutionPlan(
        target="network",
        intent=Intent.OPEN_APPLICATION,
        parameters={"execution_id": "exec_timeout"},
        confidence=1.0,
        routes=[CapabilityRoute(step_id="step_1", intent=Intent.OPEN_APPLICATION, capability_name="mock_cap")],
    )

    summary = engine.execute_plan(plan, dispatcher, user_id=42)
    assert summary.success is False

    state = engine._state_manager.get_execution("exec_timeout")
    assert state is not None
    assert state.metadata["failure_category"] == "TIMEOUT"
    assert state.metadata["recovery_strategy"] == "RETRY"


def test_failure_runtime_generic_error() -> None:
    """Verifies that generic errors map to UNKNOWN and ABORT."""
    dispatcher = MockDispatcher(exception_to_raise=ValueError("Generic error message"))
    engine = ExecutionEngine()
    
    plan = RoutedExecutionPlan(
        target="system",
        intent=Intent.OPEN_APPLICATION,
        parameters={"execution_id": "exec_generic"},
        confidence=1.0,
        routes=[CapabilityRoute(step_id="step_1", intent=Intent.OPEN_APPLICATION, capability_name="mock_cap")],
    )

    summary = engine.execute_plan(plan, dispatcher, user_id=42)
    assert summary.success is False

    state = engine._state_manager.get_execution("exec_generic")
    assert state is not None
    assert state.metadata["failure_category"] == "UNKNOWN"
    assert state.metadata["recovery_strategy"] == "ABORT"
    assert state.metadata["recoverable"] is False


def test_failure_runtime_dispatch_fail_result() -> None:
    """Verifies failure analysis works when dispatcher returns success=False without raising exception."""
    dispatcher = MockDispatcher(return_failure=True, failure_error="Connection lost")
    engine = ExecutionEngine()
    
    plan = RoutedExecutionPlan(
        target="network",
        intent=Intent.OPEN_APPLICATION,
        parameters={"execution_id": "exec_dispatch_fail"},
        confidence=1.0,
        routes=[CapabilityRoute(step_id="step_1", intent=Intent.OPEN_APPLICATION, capability_name="mock_cap")],
    )

    summary = engine.execute_plan(plan, dispatcher, user_id=42)
    assert summary.success is False

    state = engine._state_manager.get_execution("exec_dispatch_fail")
    assert state is not None
    # "Connection lost" should classify as NETWORK_ERROR / WAIT
    assert state.metadata["failure_category"] == "NETWORK_ERROR"
    assert state.metadata["recovery_strategy"] == "WAIT"


def test_failure_runtime_dependency_injection() -> None:
    """Verifies default constructor instantiates default FailureRecoveryEngine."""
    engine = ExecutionEngine()
    assert isinstance(engine._failure_recovery_engine, FailureRecoveryEngine)


def test_failure_runtime_engine_exception_safety() -> None:
    """Verifies exception safety: recovery engine crash does not crash execution flow."""
    dispatcher = MockDispatcher(exception_to_raise=ValueError("Fatal execution error"))
    
    class CrashingRecoveryEngine(FailureRecoveryEngine):
        def build_recovery_plan(self, context: RecoveryContext) -> RecoveryPlan:
            raise RuntimeError("Recovery engine database connection timed out")

    engine = ExecutionEngine(failure_recovery_engine=CrashingRecoveryEngine())
    plan = RoutedExecutionPlan(
        target="system",
        intent=Intent.OPEN_APPLICATION,
        parameters={"execution_id": "exec_safety_crash"},
        confidence=1.0,
        routes=[CapabilityRoute(step_id="step_1", intent=Intent.OPEN_APPLICATION, capability_name="mock_cap")],
    )

    # Should run to completion failing the execution normally, without throwing recovery exceptions
    summary = engine.execute_plan(plan, dispatcher, user_id=42)
    assert summary.success is False


def test_failure_runtime_metadata_population() -> None:
    """Verifies all required metadata fields are written to active state."""
    dispatcher = MockDispatcher(exception_to_raise=PermissionError("Access denied"))
    engine = ExecutionEngine()
    
    plan = RoutedExecutionPlan(
        target="restricted",
        intent=Intent.OPEN_APPLICATION,
        parameters={"execution_id": "exec_metadata"},
        confidence=1.0,
        routes=[CapabilityRoute(step_id="step_1", intent=Intent.OPEN_APPLICATION, capability_name="mock_cap")],
    )

    engine.execute_plan(plan, dispatcher, user_id=42)
    
    state = engine._state_manager.get_execution("exec_metadata")
    assert state is not None
    assert "failure_category" in state.metadata
    assert "recovery_strategy" in state.metadata
    assert "recovery_reason" in state.metadata
    assert "recovery_confidence" in state.metadata
    assert "recoverable" in state.metadata
