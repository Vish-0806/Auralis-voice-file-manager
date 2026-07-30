"""Unit and integration tests for autonomous failure recovery runtime loop."""

from __future__ import annotations

import time
# pyrefly: ignore [missing-import]
import pytest
from typing import Any

from brain.capability.models import RoutedExecutionPlan, CapabilityRoute
from core.models import Intent
from brain.execution.execution_state import ExecutionStatus
from brain.execution.execution_state_manager import ExecutionStateManager
from brain.execution.execution_engine import ExecutionEngine
from brain.execution.execution_monitor import ExecutionMonitor
from brain.execution.failure_recovery import (
    FailureRecoveryEngine,
    RecoveryContext,
    FailureCategory,
    RecoveryStrategy,
    RecoveryPlan,
    FailureAnalysis,
)


class CustomFailureRecoveryEngine(FailureRecoveryEngine):
    """Custom recovery engine subclass for simulating specific plan responses."""
    def __init__(self, mocked_strategy: RecoveryStrategy = RecoveryStrategy.ABORT, wait_seconds: float = 0.0, fallback: str = "") -> None:
        self.mocked_strategy = mocked_strategy
        self.mocked_wait_seconds = wait_seconds
        self.mocked_fallback = fallback

    def build_recovery_plan(self, context: RecoveryContext) -> RecoveryPlan:
        return RecoveryPlan(
            strategy=self.mocked_strategy,
            reason="Mocked test recovery plan strategy",
            wait_seconds=self.mocked_wait_seconds,
            fallback_resource=self.mocked_fallback,
        )


from tests.mocks import MockDispatcher, MockResult


def test_autonomous_recovery_retry_succeeds() -> None:
    """Verifies that step recovers after a successful retry action."""
    # Fails 1st attempt, succeeds on 2nd (the 1st retry attempt)
    dispatcher = MockDispatcher(failure_count=1)
    
    rec_engine = CustomFailureRecoveryEngine(mocked_strategy=RecoveryStrategy.RETRY)
    engine = ExecutionEngine(failure_recovery_engine=rec_engine)

    plan = RoutedExecutionPlan(
        target="system",
        intent=Intent.OPEN_APPLICATION,
        parameters={"execution_id": "exec_retry_succ"},
        confidence=1.0,
        routes=[CapabilityRoute(step_id="step_1", intent=Intent.OPEN_APPLICATION, capability_name="mock_cap")],
    )

    summary = engine.execute_plan(plan, dispatcher, user_id=42)
    assert summary.success is True
    # Initial execution + 1 retry attempt = 2 dispatcher calls
    assert dispatcher.calls == 2

    state = engine._state_manager.get_execution("exec_retry_succ")
    assert state is not None
    assert state.recovery_attempts == 1
    assert state.last_recovery_strategy == "RETRY"
    assert state.metadata.get("successful_recoveries") == 1


def test_autonomous_recovery_retry_exhausted() -> None:
    """Verifies failure when retry attempts exhaust the limit."""
    # Fails all attempts
    dispatcher = MockDispatcher(failure_count=5)
    
    rec_engine = CustomFailureRecoveryEngine(mocked_strategy=RecoveryStrategy.RETRY)
    engine = ExecutionEngine(failure_recovery_engine=rec_engine)

    plan = RoutedExecutionPlan(
        target="system",
        intent=Intent.OPEN_APPLICATION,
        parameters={"execution_id": "exec_retry_exh"},
        confidence=1.0,
        routes=[CapabilityRoute(step_id="step_1", intent=Intent.OPEN_APPLICATION, capability_name="mock_cap")],
    )

    summary = engine.execute_plan(plan, dispatcher, user_id=42)
    assert summary.success is False

    state = engine._state_manager.get_execution("exec_retry_exh")
    assert state is not None
    # Maximum retry limit defaults to 3 (which means it attempts 3 retries, so total dispatcher calls = 4)
    assert dispatcher.calls == 4
    assert state.metadata.get("failed_recoveries") == 1


def test_autonomous_recovery_wait_strategy() -> None:
    """Verifies that wait strategy sleeps and then retries."""
    dispatcher = MockDispatcher(failure_count=1)
    
    # 0.1s wait
    rec_engine = CustomFailureRecoveryEngine(mocked_strategy=RecoveryStrategy.WAIT, wait_seconds=0.1)
    engine = ExecutionEngine(failure_recovery_engine=rec_engine)

    plan = RoutedExecutionPlan(
        target="network",
        intent=Intent.OPEN_APPLICATION,
        parameters={"execution_id": "exec_wait_strat"},
        confidence=1.0,
        routes=[CapabilityRoute(step_id="step_1", intent=Intent.OPEN_APPLICATION, capability_name="mock_cap")],
    )

    start = time.perf_counter()
    summary = engine.execute_plan(plan, dispatcher, user_id=42)
    elapsed = time.perf_counter() - start

    assert summary.success is True
    assert elapsed >= 0.1
    assert dispatcher.calls == 2

    state = engine._state_manager.get_execution("exec_wait_strat")
    assert state is not None
    assert state.last_recovery_strategy == "WAIT"


def test_autonomous_recovery_fallback() -> None:
    """Verifies fallback strategy replaces the resource target and retries."""
    dispatcher = MockDispatcher(failure_count=1)
    rec_engine = CustomFailureRecoveryEngine(mocked_strategy=RecoveryStrategy.USE_FALLBACK, fallback="Edge")
    engine = ExecutionEngine(failure_recovery_engine=rec_engine)

    plan = RoutedExecutionPlan(
        target="chrome",
        intent=Intent.OPEN_APPLICATION,
        parameters={"execution_id": "exec_fallback_strat"},
        confidence=1.0,
        routes=[CapabilityRoute(step_id="step_1", intent=Intent.OPEN_APPLICATION, capability_name="mock_cap")],
    )

    summary = engine.execute_plan(plan, dispatcher, user_id=42)
    assert summary.success is True
    assert dispatcher.calls == 2
    
    state = engine._state_manager.get_execution("exec_fallback_strat")
    assert state is not None
    assert state.last_recovery_strategy == "USE_FALLBACK"
    assert state.metadata.get("fallback_usage") == 1


def test_autonomous_recovery_skip() -> None:
    """Verifies skip strategy marks step successful and adds it to skipped list."""
    dispatcher = MockDispatcher(failure_count=1)
    rec_engine = CustomFailureRecoveryEngine(mocked_strategy=RecoveryStrategy.SKIP)
    engine = ExecutionEngine(failure_recovery_engine=rec_engine)

    plan = RoutedExecutionPlan(
        target="chrome",
        intent=Intent.OPEN_APPLICATION,
        parameters={"execution_id": "exec_skip_strat"},
        confidence=1.0,
        routes=[CapabilityRoute(step_id="step_1", intent=Intent.OPEN_APPLICATION, capability_name="mock_cap")],
    )

    summary = engine.execute_plan(plan, dispatcher, user_id=42)
    assert summary.success is True
    # First dispatch failed, skipped, so calls = 1
    assert dispatcher.calls == 1
    
    state = engine._state_manager.get_execution("exec_skip_strat")
    assert state is not None
    assert "step_1" in state.skipped_steps


def test_autonomous_recovery_ignore() -> None:
    """Verifies ignore strategy records the failure and proceeds."""
    dispatcher = MockDispatcher(failure_count=1)
    rec_engine = CustomFailureRecoveryEngine(mocked_strategy=RecoveryStrategy.IGNORE)
    engine = ExecutionEngine(failure_recovery_engine=rec_engine)

    plan = RoutedExecutionPlan(
        target="chrome",
        intent=Intent.OPEN_APPLICATION,
        parameters={"execution_id": "exec_ignore_strat"},
        confidence=1.0,
        routes=[CapabilityRoute(step_id="step_1", intent=Intent.OPEN_APPLICATION, capability_name="mock_cap")],
    )

    summary = engine.execute_plan(plan, dispatcher, user_id=42)
    assert summary.success is True
    assert dispatcher.calls == 1

    state = engine._state_manager.get_execution("exec_ignore_strat")
    assert state is not None
    assert len(state.ignored_failures) == 1


def test_autonomous_recovery_ask_user() -> None:
    """Verifies ask_user transitions status to WAITING_FOR_CONFIRMATION."""
    dispatcher = MockDispatcher(failure_count=1)
    rec_engine = CustomFailureRecoveryEngine(mocked_strategy=RecoveryStrategy.ASK_USER)
    engine = ExecutionEngine(failure_recovery_engine=rec_engine)

    plan = RoutedExecutionPlan(
        target="chrome",
        intent=Intent.OPEN_APPLICATION,
        parameters={"execution_id": "exec_ask_strat"},
        confidence=1.0,
        routes=[CapabilityRoute(step_id="step_1", intent=Intent.OPEN_APPLICATION, capability_name="mock_cap")],
    )

    summary = engine.execute_plan(plan, dispatcher, user_id=42)
    assert summary.success is False

    state = engine._state_manager.get_execution("exec_ask_strat")
    assert state is not None
    assert state.status == ExecutionStatus.WAITING_FOR_CONFIRMATION
    assert state.waiting_for_confirmation is True


def test_autonomous_recovery_abort() -> None:
    """Verifies abort strategy terminates immediately without other recovery."""
    dispatcher = MockDispatcher(failure_count=2)
    rec_engine = CustomFailureRecoveryEngine(mocked_strategy=RecoveryStrategy.ABORT)
    engine = ExecutionEngine(failure_recovery_engine=rec_engine)

    plan = RoutedExecutionPlan(
        target="chrome",
        intent=Intent.OPEN_APPLICATION,
        parameters={"execution_id": "exec_abort_strat"},
        confidence=1.0,
        routes=[CapabilityRoute(step_id="step_1", intent=Intent.OPEN_APPLICATION, capability_name="mock_cap")],
    )

    summary = engine.execute_plan(plan, dispatcher, user_id=42)
    assert summary.success is False
    assert dispatcher.calls == 1

    state = engine._state_manager.get_execution("exec_abort_strat")
    assert state is not None
    assert state.metadata.get("failed_recoveries") == 1


def test_autonomous_recovery_statistics() -> None:
    """Verifies that recovery metrics are aggregated correctly in statistics."""
    monitor = ExecutionMonitor()
    state_manager = ExecutionStateManager(monitor=monitor)
    rec_engine = CustomFailureRecoveryEngine(mocked_strategy=RecoveryStrategy.SKIP)
    engine = ExecutionEngine(state_manager=state_manager, failure_recovery_engine=rec_engine)
    monitor._state_manager = state_manager

    # 1. Run and skip step 1
    dispatcher = MockDispatcher(failure_count=1)
    plan = RoutedExecutionPlan(
        target="chrome",
        intent=Intent.OPEN_APPLICATION,
        parameters={"execution_id": "exec_stat_1"},
        confidence=1.0,
        routes=[CapabilityRoute(step_id="step_1", intent=Intent.OPEN_APPLICATION, capability_name="mock_cap")],
    )
    engine.execute_plan(plan, dispatcher, user_id=42)

    stats = monitor.get_statistics()
    assert stats.recovery_attempts == 1
    assert stats.skipped_steps == 1
    assert stats.successful_recoveries == 1


def test_autonomous_recovery_failure_fallback() -> None:
    """Verifies safety: if recovery strategy execution crashes, it falls back gracefully."""
    dispatcher = MockDispatcher(failure_count=1)
    
    class ExplodingRecoveryStrategyEngine(FailureRecoveryEngine):
        def build_recovery_plan(self, context: RecoveryContext) -> RecoveryPlan:
            # Blows up inside the recovery plan builder
            raise RuntimeError("Database connection timed out")

    engine = ExecutionEngine(failure_recovery_engine=ExplodingRecoveryStrategyEngine())
    plan = RoutedExecutionPlan(
        target="chrome",
        intent=Intent.OPEN_APPLICATION,
        parameters={"execution_id": "exec_crash_recovery"},
        confidence=1.0,
        routes=[CapabilityRoute(step_id="step_1", intent=Intent.OPEN_APPLICATION, capability_name="mock_cap")],
    )

    # Should fall back cleanly and abort execution without crash
    summary = engine.execute_plan(plan, dispatcher, user_id=42)
    assert summary.success is False
    assert dispatcher.calls == 1


def test_autonomous_recovery_dependency_injection() -> None:
    """Verifies default constructor setup."""
    engine = ExecutionEngine()
    assert isinstance(engine._failure_recovery_engine, FailureRecoveryEngine)


def test_autonomous_recovery_multiple_attempts() -> None:
    """Verifies multiple step recovery attempts accumulate correctly on the execution state."""
    dispatcher = MockDispatcher(failure_count=1)
    rec_engine = CustomFailureRecoveryEngine(mocked_strategy=RecoveryStrategy.SKIP)
    engine = ExecutionEngine(failure_recovery_engine=rec_engine)

    plan = RoutedExecutionPlan(
        target="multiple",
        intent=Intent.OPEN_APPLICATION,
        parameters={"execution_id": "exec_multiple_attempts"},
        confidence=1.0,
        routes=[
            CapabilityRoute(step_id="step_1", intent=Intent.OPEN_APPLICATION, capability_name="mock_cap"),
            CapabilityRoute(step_id="step_2", intent=Intent.OPEN_APPLICATION, capability_name="mock_cap"),
        ],
    )

    summary = engine.execute_plan(plan, dispatcher, user_id=42)
    assert summary.success is True
    
    state = engine._state_manager.get_execution("exec_multiple_attempts")
    assert state is not None
    # We fail on step_1 (recovers via skip), then step_2 succeeds. Total recovery attempts = 1.
    assert state.recovery_attempts == 1
    assert "step_1" in state.skipped_steps


def test_autonomous_recovery_backward_compatibility() -> None:
    """Verifies backward compatibility with the legacy recovery mechanism."""
    # When the new FailureRecoveryEngine returns ABORT (meaning no autonomous recovery),
    # it falls back to the legacy RecoveryEngine to perform recovery.
    from unittest.mock import MagicMock
    dispatcher = MockDispatcher(failure_count=1)
    
    # Custom recovery engine that returns ABORT to trigger fallback to legacy engine
    rec_engine = CustomFailureRecoveryEngine(mocked_strategy=RecoveryStrategy.ABORT)
    engine = ExecutionEngine(failure_recovery_engine=rec_engine)

    # Mock legacy recovery engine
    legacy_mock = MagicMock()
    legacy_mock.recover.return_value = MagicMock(success=True, strategy_applied="Legacy Mock Recovery")
    engine._recovery_engine = legacy_mock

    plan = RoutedExecutionPlan(
        target="chrome",
        intent=Intent.OPEN_APPLICATION,
        parameters={"execution_id": "exec_legacy_fallback"},
        confidence=1.0,
        routes=[CapabilityRoute(step_id="step_1", intent=Intent.OPEN_APPLICATION, capability_name="mock_cap")],
    )

    # Execute plan; the legacy recovery engine recovers it
    summary = engine.execute_plan(plan, dispatcher, user_id=42)
    assert summary.success is True


def test_autonomous_recovery_logging_events(caplog: pytest.LogCaptureFixture) -> None:
    """Verifies that appropriate structured log events are generated during recovery."""
    dispatcher = MockDispatcher(failure_count=1)
    rec_engine = CustomFailureRecoveryEngine(mocked_strategy=RecoveryStrategy.IGNORE)
    engine = ExecutionEngine(failure_recovery_engine=rec_engine)

    plan = RoutedExecutionPlan(
        target="chrome",
        intent=Intent.OPEN_APPLICATION,
        parameters={"execution_id": "exec_logging_events"},
        confidence=1.0,
        routes=[CapabilityRoute(step_id="step_1", intent=Intent.OPEN_APPLICATION, capability_name="mock_cap")],
    )

    with caplog.at_level("INFO"):
        engine.execute_plan(plan, dispatcher, user_id=42)

    # Verify structured messages in logger entries
    log_messages = [record.message for record in caplog.records]
    assert any("Recovery Started" in msg for msg in log_messages)
    assert any("Ignored Failure" in msg for msg in log_messages)
    assert any("Recovery Successful" in msg for msg in log_messages)


def test_autonomous_recovery_execution_state_updates() -> None:
    """Verifies all recovery fields are populated on ExecutionState model."""
    dispatcher = MockDispatcher(failure_count=1)
    rec_engine = CustomFailureRecoveryEngine(mocked_strategy=RecoveryStrategy.IGNORE)
    engine = ExecutionEngine(failure_recovery_engine=rec_engine)

    plan = RoutedExecutionPlan(
        target="chrome",
        intent=Intent.OPEN_APPLICATION,
        parameters={"execution_id": "exec_state_updates"},
        confidence=1.0,
        routes=[CapabilityRoute(step_id="step_1", intent=Intent.OPEN_APPLICATION, capability_name="mock_cap")],
    )

    engine.execute_plan(plan, dispatcher, user_id=42)

    state = engine._state_manager.get_execution("exec_state_updates")
    assert state is not None
    assert state.recovery_attempts == 1
    assert state.last_recovery_strategy == "IGNORE"
    assert len(state.ignored_failures) == 1
    assert state.waiting_for_confirmation is False

