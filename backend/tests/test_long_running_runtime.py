"""Runtime integration tests for LongRunningTaskManager with ExecutionEngine and ExecutionMonitor."""

from __future__ import annotations

import logging
from typing import Any
# pyrefly: ignore [missing-import]
pytest = None
try:
    # pyrefly: ignore [missing-import]
    import pytest
except ImportError:
    pass

from brain.capability.models import CapabilityRoute, RoutedExecutionPlan
from brain.execution.execution_engine import ExecutionEngine, is_long_running_task
from brain.execution.execution_monitor import ExecutionMonitor
from brain.execution.long_running_task_manager import (
    LongRunningTask,
    LongRunningTaskConfig,
    LongRunningTaskManager,
    LongRunningTaskStatus,
)
from core.models import Intent


from tests.mocks import MockResult


class MockDispatcher:
    """Mock dispatcher recording requests."""

    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.dispatched = []

    def dispatch(self, plan: Any) -> Any:
        self.dispatched.append(plan)
        return MockResult(
            success=not self.should_fail,
            execution_time=0.05,
            response="Success" if not self.should_fail else "",
            error="Execution Error" if self.should_fail else None,
        )


class FailingTaskManager(LongRunningTaskManager):
    """Failing manager to test runtime error isolation."""

    def create_task(self, *args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("Task manager internal storage failure")

    def update_progress(self, *args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("Progress update failure")


def test_detection_long_running() -> None:
    """Verifies is_long_running_task detects indexing, scanning, batching, etc."""
    plan_index = RoutedExecutionPlan(
        target="workspace_index",
        intent=Intent.OPEN_APPLICATION,
        parameters={},
        confidence=1.0,
        routes=[],
    )
    plan_param = RoutedExecutionPlan(
        target="files",
        intent=Intent.OPEN_FILE,
        parameters={"is_long_running": True},
        confidence=1.0,
        routes=[],
    )
    assert is_long_running_task(plan_index) is True
    assert is_long_running_task(plan_param) is True


def test_detection_ordinary_command() -> None:
    """Verifies is_long_running_task returns False for ordinary commands."""
    plan_norm = RoutedExecutionPlan(
        target="Chrome",
        intent=Intent.OPEN_APPLICATION,
        parameters={},
        confidence=1.0,
        routes=[CapabilityRoute(step_id="s1", intent=Intent.OPEN_APPLICATION, capability_name="cap")],
    )
    assert is_long_running_task(plan_norm) is False


def test_task_registration_and_queue() -> None:
    """Verifies long-running plan triggers task creation and queuing."""
    task_manager = LongRunningTaskManager()
    engine = ExecutionEngine(task_manager=task_manager)
    dispatcher = MockDispatcher()

    plan = RoutedExecutionPlan(
        target="workspace_index",
        intent=Intent.OPEN_APPLICATION,
        parameters={"execution_id": "exec_reg_1"},
        confidence=1.0,
        routes=[CapabilityRoute(step_id="step_1", intent=Intent.OPEN_APPLICATION, capability_name="mock_cap")],
    )

    summary = engine.execute_plan(plan, dispatcher)
    assert summary.success is True

    tasks = task_manager.list_completed()
    assert len(tasks) == 1
    assert tasks[0].execution_id == "exec_reg_1"


def test_task_start_and_running_state() -> None:
    """Verifies task transitions through QUEUED to RUNNING and COMPLETED."""
    task_manager = LongRunningTaskManager()
    engine = ExecutionEngine(task_manager=task_manager)
    dispatcher = MockDispatcher()

    plan = RoutedExecutionPlan(
        target="repo_scan",
        intent=Intent.OPEN_APPLICATION,
        parameters={"execution_id": "exec_start_1"},
        confidence=1.0,
        routes=[CapabilityRoute(step_id="step_1", intent=Intent.OPEN_APPLICATION, capability_name="mock_cap")],
    )

    engine.execute_plan(plan, dispatcher)
    task = task_manager.get_task(task_manager.list_completed()[0].task_id)
    assert task is not None
    assert task.started_at is not None
    assert task.completed_at is not None
    assert task.status == LongRunningTaskStatus.COMPLETED


def test_progress_updates_during_execution() -> None:
    """Verifies step progress is updated during execution loop."""
    task_manager = LongRunningTaskManager()
    engine = ExecutionEngine(task_manager=task_manager)
    dispatcher = MockDispatcher()

    plan = RoutedExecutionPlan(
        target="workspace_index",
        intent=Intent.OPEN_APPLICATION,
        parameters={"execution_id": "exec_prog_1"},
        confidence=1.0,
        routes=[
            CapabilityRoute(step_id="s1", intent=Intent.OPEN_APPLICATION, capability_name="c1"),
            CapabilityRoute(step_id="s2", intent=Intent.OPEN_APPLICATION, capability_name="c2"),
        ],
    )

    engine.execute_plan(plan, dispatcher)
    task = task_manager.list_completed()[0]
    assert task.progress == 100.0
    assert task.total_steps == 2


def test_task_completion_on_success() -> None:
    """Verifies task status marks COMPLETED on successful plan finish."""
    task_manager = LongRunningTaskManager()
    engine = ExecutionEngine(task_manager=task_manager)
    dispatcher = MockDispatcher()

    plan = RoutedExecutionPlan(
        target="batch_workflow",
        intent=Intent.OPEN_APPLICATION,
        parameters={"execution_id": "exec_comp_1"},
        confidence=1.0,
        routes=[CapabilityRoute(step_id="s1", intent=Intent.OPEN_APPLICATION, capability_name="c1")],
    )

    summary = engine.execute_plan(plan, dispatcher)
    assert summary.success is True

    completed = task_manager.list_completed()
    assert len(completed) == 1
    assert completed[0].status == LongRunningTaskStatus.COMPLETED


def test_task_failure_handling() -> None:
    """Verifies task status transitions to FAILED when step execution fails."""
    task_manager = LongRunningTaskManager()
    engine = ExecutionEngine(task_manager=task_manager)
    dispatcher = MockDispatcher(should_fail=True)

    plan = RoutedExecutionPlan(
        target="workspace_index",
        intent=Intent.OPEN_APPLICATION,
        parameters={"execution_id": "exec_fail_1"},
        confidence=1.0,
        routes=[CapabilityRoute(step_id="s1", intent=Intent.OPEN_APPLICATION, capability_name="c1")],
    )

    summary = engine.execute_plan(plan, dispatcher)
    assert summary.success is False

    completed = task_manager.list_completed()
    assert len(completed) == 1
    assert completed[0].status == LongRunningTaskStatus.FAILED
    assert completed[0].error is not None


def test_task_cancellation_handling() -> None:
    """Verifies task status transitions to CANCELLED when task is cancelled."""
    task_manager = LongRunningTaskManager()
    engine = ExecutionEngine(task_manager=task_manager)

    task = engine._safe_create_long_running_task(
        name="workspace_index",
        execution_id="exec_cancel_1",
        total_steps=1,
    )
    assert task is not None
    engine._safe_cancel_long_running_task(task.task_id)

    tasks = task_manager.list_completed()
    assert len(tasks) == 1
    assert tasks[0].status == LongRunningTaskStatus.CANCELLED


def test_dependency_injection() -> None:
    """Verifies ExecutionEngine accepts custom task manager via constructor."""
    config = LongRunningTaskConfig(maximum_tasks=50)
    tm = LongRunningTaskManager(config=config)
    engine = ExecutionEngine(task_manager=tm)

    assert engine._task_manager is tm
    assert engine._task_manager._config.maximum_tasks == 50


def test_monitoring_integration() -> None:
    """Verifies ExecutionMonitor records long-running task metrics."""
    tm = LongRunningTaskManager()
    monitor = ExecutionMonitor(task_manager=tm)
    engine = ExecutionEngine(task_manager=tm)
    dispatcher = MockDispatcher()

    plan = RoutedExecutionPlan(
        target="workspace_index",
        intent=Intent.OPEN_APPLICATION,
        parameters={"execution_id": "exec_mon_1"},
        confidence=1.0,
        routes=[CapabilityRoute(step_id="s1", intent=Intent.OPEN_APPLICATION, capability_name="c1")],
    )

    engine.execute_plan(plan, dispatcher)
    stats = monitor.get_statistics()

    assert stats.long_running_task_count == 1
    assert stats.long_running_completion_percentage == 100.0
    assert stats.long_running_failed_count == 0


def test_manager_failure_fallback_isolation() -> None:
    """Verifies exceptions in task manager do not interrupt core plan execution."""
    failing_tm = FailingTaskManager()
    engine = ExecutionEngine(task_manager=failing_tm)
    dispatcher = MockDispatcher()

    plan = RoutedExecutionPlan(
        target="workspace_index",
        intent=Intent.OPEN_APPLICATION,
        parameters={"execution_id": "exec_isolation_1"},
        confidence=1.0,
        routes=[CapabilityRoute(step_id="s1", intent=Intent.OPEN_APPLICATION, capability_name="c1")],
    )

    # Should execute successfully despite task manager raising internal exceptions
    summary = engine.execute_plan(plan, dispatcher)
    assert summary.success is True
    assert len(dispatcher.dispatched) == 1


def test_structured_logging(caplog: Any) -> None:
    """Verifies structured logging entries are emitted during task execution."""
    tm = LongRunningTaskManager()
    engine = ExecutionEngine(task_manager=tm)
    dispatcher = MockDispatcher()

    plan = RoutedExecutionPlan(
        target="workspace_index",
        intent=Intent.OPEN_APPLICATION,
        parameters={"execution_id": "exec_log_1"},
        confidence=1.0,
        routes=[CapabilityRoute(step_id="s1", intent=Intent.OPEN_APPLICATION, capability_name="c1")],
    )

    with caplog.at_level(logging.INFO):
        engine.execute_plan(plan, dispatcher)

    log_messages = [record.message for record in caplog.records]
    assert "Long Running Task Detected" in log_messages
    assert "Task Registered" in log_messages
    assert "Task Started" in log_messages
    assert "Task Completed" in log_messages


def test_backward_compatibility() -> None:
    """Verifies standard short-running executions proceed completely unaffected."""
    task_manager = LongRunningTaskManager()
    engine = ExecutionEngine(task_manager=task_manager)
    dispatcher = MockDispatcher()

    plan = RoutedExecutionPlan(
        target="Calculator",
        intent=Intent.OPEN_APPLICATION,
        parameters={"execution_id": "exec_short_1"},
        confidence=1.0,
        routes=[CapabilityRoute(step_id="s1", intent=Intent.OPEN_APPLICATION, capability_name="c1")],
    )

    summary = engine.execute_plan(plan, dispatcher)
    assert summary.success is True
    assert len(task_manager.list_tasks()) == 0
