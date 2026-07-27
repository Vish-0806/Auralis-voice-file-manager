"""Unit tests for the ExecutionMonitor and tracking history."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
import pytest

from brain.execution.execution_state import ExecutionStatus, ExecutionState
from brain.execution.execution_state_manager import ExecutionStateManager
from brain.execution.execution_monitor import ExecutionMonitor, ExecutionSummary


def test_monitor_record_completion() -> None:
    """Verifies that record_completion stores a correct success summary."""
    monitor = ExecutionMonitor()
    state = ExecutionState(execution_id="exec_1", user_id=42)
    state.status = ExecutionStatus.COMPLETED
    state.progress.started_at = datetime.now(timezone.utc) - timedelta(seconds=10)
    state.progress.completed_at = datetime.now(timezone.utc)
    state.progress.percentage = 100.0
    state.completed_steps = ["step_1", "step_2"]

    monitor.record_completion(state)
    
    summary = monitor.get_summary("exec_1")
    assert summary is not None
    assert summary.status == ExecutionStatus.COMPLETED
    assert summary.duration_seconds == pytest.approx(10.0, abs=0.1)
    assert summary.steps_executed == 2
    assert summary.steps_failed == 0
    assert summary.completion_percentage == 100.0


def test_monitor_record_failure() -> None:
    """Verifies that record_failure stores a correct failure summary."""
    monitor = ExecutionMonitor()
    state = ExecutionState(execution_id="exec_2", user_id=42)
    state.status = ExecutionStatus.FAILED
    state.progress.started_at = datetime.now(timezone.utc) - timedelta(seconds=5)
    state.progress.completed_at = datetime.now(timezone.utc)
    state.progress.percentage = 50.0
    state.completed_steps = ["step_1"]
    state.failed_steps = ["step_2"]
    state.error_message = "Mute hardware timeout"

    monitor.record_failure(state)

    summary = monitor.get_summary("exec_2")
    assert summary is not None
    assert summary.status == ExecutionStatus.FAILED
    assert summary.duration_seconds == pytest.approx(5.0, abs=0.1)
    assert summary.steps_executed == 2
    assert summary.steps_failed == 1


def test_monitor_record_cancellation() -> None:
    """Verifies that record_cancellation stores a cancelled summary."""
    monitor = ExecutionMonitor()
    state = ExecutionState(execution_id="exec_3", user_id=42)
    state.status = ExecutionStatus.CANCELLED
    state.progress.started_at = datetime.now(timezone.utc) - timedelta(seconds=2)
    state.progress.completed_at = datetime.now(timezone.utc)
    state.progress.percentage = 25.0
    state.completed_steps = ["step_1"]

    monitor.record_cancellation(state)

    summary = monitor.get_summary("exec_3")
    assert summary is not None
    assert summary.status == ExecutionStatus.CANCELLED
    assert summary.duration_seconds == pytest.approx(2.0, abs=0.1)


def test_monitor_get_summary_unknown_id() -> None:
    """Verifies get_summary returns None if the execution ID is unknown."""
    monitor = ExecutionMonitor()
    assert monitor.get_summary("unknown") is None


def test_monitor_list_history_and_limit() -> None:
    """Verifies that list_history respects limits and ejections (FIFO)."""
    # Max size = 3
    monitor = ExecutionMonitor(max_history_size=3)
    
    for i in range(5):
        state = ExecutionState(execution_id=f"exec_{i}", user_id=42)
        state.status = ExecutionStatus.COMPLETED
        monitor.record_completion(state)

    history = monitor.list_history()
    # History size should be capped at 3
    assert len(history) == 3
    # Oldest entries (exec_0, exec_1) should be evicted (FIFO)
    assert [h.execution_id for h in history] == ["exec_2", "exec_3", "exec_4"]

    # Test limit parameter in list_history
    limited = monitor.list_history(limit=2)
    assert len(limited) == 2
    assert [h.execution_id for h in limited] == ["exec_3", "exec_4"]


def test_monitor_clear_history() -> None:
    """Verifies that clear_history clears all summaries in memory."""
    monitor = ExecutionMonitor()
    state = ExecutionState(execution_id="exec_1", user_id=42)
    state.status = ExecutionStatus.COMPLETED
    monitor.record_completion(state)

    monitor.clear_history()
    assert len(monitor.list_history()) == 0


def test_monitor_statistics_calculation() -> None:
    """Verifies correct calculation of success rate, retry rate, and counts."""
    monitor = ExecutionMonitor()

    # 1. Successful run with retry
    state1 = ExecutionState(execution_id="exec_1", user_id=42)
    state1.status = ExecutionStatus.COMPLETED
    state1.retry_count = 1
    state1.progress.started_at = datetime.now(timezone.utc) - timedelta(seconds=12)
    state1.progress.completed_at = datetime.now(timezone.utc)
    monitor.record_completion(state1)

    # 2. Failed run
    state2 = ExecutionState(execution_id="exec_2", user_id=42)
    state2.status = ExecutionStatus.FAILED
    state2.progress.started_at = datetime.now(timezone.utc) - timedelta(seconds=6)
    state2.progress.completed_at = datetime.now(timezone.utc)
    monitor.record_failure(state2)

    # 3. Cancelled run
    state3 = ExecutionState(execution_id="exec_3", user_id=42)
    state3.status = ExecutionStatus.CANCELLED
    state3.progress.started_at = datetime.now(timezone.utc) - timedelta(seconds=3)
    state3.progress.completed_at = datetime.now(timezone.utc)
    monitor.record_cancellation(state3)

    stats = monitor.get_statistics()
    assert stats.total_executions == 3
    assert stats.completed == 1
    assert stats.failed == 1
    assert stats.cancelled == 1
    assert stats.running == 0
    assert stats.average_duration == pytest.approx(7.0, abs=0.1)  # (12 + 6 + 3) / 3
    assert stats.success_rate == pytest.approx(1.0 / 3.0)
    assert stats.retry_rate == pytest.approx(1.0 / 3.0)


def test_monitor_calculate_metrics() -> None:
    """Verifies runtime performance metrics calculation helper."""
    monitor = ExecutionMonitor()
    state = ExecutionState(execution_id="exec_1", user_id=42)
    state.status = ExecutionStatus.COMPLETED
    state.progress.started_at = datetime.now(timezone.utc) - timedelta(seconds=8)
    state.progress.completed_at = datetime.now(timezone.utc)
    state.completed_steps = ["step_1", "step_2"]
    state.retry_count = 2

    metrics = monitor.calculate_metrics(state)
    assert metrics.execution_id == "exec_1"
    assert metrics.total_steps == 2
    assert metrics.completed_steps == 2
    assert metrics.failed_steps == 0
    assert metrics.retry_count == 2
    assert metrics.duration_seconds == pytest.approx(8.0, abs=0.1)
    assert metrics.average_step_duration == pytest.approx(4.0, abs=0.1)
    assert metrics.success is True


def test_manager_integration_completed() -> None:
    """Verifies that the state manager automatically notifies the monitor upon completion."""
    monitor = ExecutionMonitor()
    mgr = ExecutionStateManager(monitor=monitor)

    mgr.create_execution("exec_1", user_id=42)
    mgr.mark_running("exec_1")
    mgr.mark_completed("exec_1")

    summary = monitor.get_summary("exec_1")
    assert summary is not None
    assert summary.status == ExecutionStatus.COMPLETED


def test_manager_integration_failed() -> None:
    """Verifies that the state manager automatically notifies the monitor upon failure."""
    monitor = ExecutionMonitor()
    mgr = ExecutionStateManager(monitor=monitor)

    mgr.create_execution("exec_1", user_id=42)
    mgr.mark_running("exec_1")
    mgr.mark_failed("exec_1", "Fatal error")

    summary = monitor.get_summary("exec_1")
    assert summary is not None
    assert summary.status == ExecutionStatus.FAILED


def test_manager_integration_cancelled() -> None:
    """Verifies that the state manager automatically notifies the monitor upon cancellation."""
    monitor = ExecutionMonitor()
    mgr = ExecutionStateManager(monitor=monitor)

    mgr.create_execution("exec_1", user_id=42)
    mgr.mark_running("exec_1")
    mgr.mark_cancelled("exec_1")

    summary = monitor.get_summary("exec_1")
    assert summary is not None
    assert summary.status == ExecutionStatus.CANCELLED


def test_monitor_statistics_with_running_manager() -> None:
    """Verifies statistics calculation queries active states from injected state manager."""
    monitor = ExecutionMonitor()
    mgr = ExecutionStateManager(monitor=monitor)
    monitor._state_manager = mgr

    # 1. Running execution
    mgr.create_execution("exec_run", user_id=42)
    mgr.mark_running("exec_run")

    # 2. Completed execution
    mgr.create_execution("exec_comp", user_id=42)
    mgr.mark_running("exec_comp")
    mgr.mark_completed("exec_comp")

    stats = monitor.get_statistics()
    assert stats.total_executions == 2
    assert stats.running == 1
    assert stats.completed == 1
    assert stats.failed == 0
