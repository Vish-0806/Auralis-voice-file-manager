"""Unit and integration tests for LongRunningTaskManager recovery, persistence hooks, and lifecycle maintenance."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
from typing import Any, Dict, List, Optional
# pyrefly: ignore [missing-import]
pytest = None
try:
    # pyrefly: ignore [missing-import]
    import pytest
except ImportError:
    pass

from brain.execution.execution_monitor import ExecutionMonitor
from brain.execution.long_running_task_manager import (
    LongRunningTask,
    LongRunningTaskConfig,
    LongRunningTaskManager,
    LongRunningTaskPriority,
    LongRunningTaskStatus,
    NullTaskPersistenceHook,
    TaskPersistenceHook,
)
from brain.execution.task_events import TaskEvent, TaskEventType, TaskEventDispatcher


class MockPersistenceHook:
    """Mock persistence hook recording operations and supporting task loading."""

    def __init__(self, tasks_to_load: Optional[List[Any]] = None, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.tasks_to_load = tasks_to_load or []
        self.saved_tasks: List[LongRunningTask] = []
        self.updated_tasks: List[LongRunningTask] = []
        self.deleted_task_ids: List[str] = []

    def save_task(self, task: LongRunningTask) -> None:
        if self.should_fail:
            raise RuntimeError("Persistence Save Error")
        self.saved_tasks.append(task)

    def update_task(self, task: LongRunningTask) -> None:
        if self.should_fail:
            raise RuntimeError("Persistence Update Error")
        self.updated_tasks.append(task)

    def delete_task(self, task_id: str) -> None:
        if self.should_fail:
            raise RuntimeError("Persistence Delete Error")
        self.deleted_task_ids.append(task_id)

    def load_tasks(self) -> List[LongRunningTask]:
        if self.should_fail:
            raise RuntimeError("Persistence Load Error")
        return list(self.tasks_to_load)


class MockEventListener:
    """Mock event listener accumulating events."""

    def __init__(self) -> None:
        self.events: List[TaskEvent] = []

    def on_event(self, event: TaskEvent) -> None:
        self.events.append(event)


def test_null_persistence_hook() -> None:
    """Verifies NullTaskPersistenceHook operates silently as a no-op."""
    hook = NullTaskPersistenceHook()
    task = LongRunningTask(task_id="t1", name="Test")

    # None should raise exceptions
    hook.save_task(task)
    hook.update_task(task)
    hook.delete_task("t1")
    assert hook.load_tasks() == []


def test_custom_persistence_hook_invocation() -> None:
    """Verifies custom persistence hook receives save, update, delete calls."""
    hook = MockPersistenceHook()
    manager = LongRunningTaskManager(persistence_hook=hook)

    task = manager.create_task(name="Scan Workspace")
    assert task is not None
    assert len(hook.saved_tasks) == 1
    assert hook.saved_tasks[0].task_id == task.task_id

    manager.start_task(task.task_id)
    assert len(hook.updated_tasks) >= 1
    assert hook.updated_tasks[-1].status == LongRunningTaskStatus.RUNNING


def test_recover_tasks_active_and_completed() -> None:
    """Verifies recover_tasks restores active tasks into active map and completed tasks into history."""
    now = datetime.now(timezone.utc)
    t_active = LongRunningTask(task_id="t_act", name="Active Task", status=LongRunningTaskStatus.RUNNING, created_at=now)
    t_comp = LongRunningTask(task_id="t_done", name="Done Task", status=LongRunningTaskStatus.COMPLETED, created_at=now)

    hook = MockPersistenceHook(tasks_to_load=[t_active, t_comp])
    manager = LongRunningTaskManager(persistence_hook=hook)

    recovered_count = manager.recover_tasks()
    assert recovered_count == 1

    act = manager.get_task("t_act")
    assert act is not None
    assert act.status == LongRunningTaskStatus.RUNNING

    done = manager.get_task("t_done")
    assert done is not None
    assert done.status == LongRunningTaskStatus.COMPLETED


def test_corrupted_task_recovery_handling(caplog: Any) -> None:
    """Verifies corrupted or invalid objects in persistence are skipped gracefully."""
    corrupted_obj = "invalid_string_object"
    t_valid = LongRunningTask(task_id="t_ok", name="Valid Task", status=LongRunningTaskStatus.PENDING)

    hook = MockPersistenceHook(tasks_to_load=[corrupted_obj, t_valid])
    manager = LongRunningTaskManager(persistence_hook=hook)

    with caplog.at_level(logging.WARNING):
        recovered = manager.recover_tasks()

    assert recovered == 1
    assert manager.get_task("t_ok") is not None
    assert any("Corrupted task skipped" in r.message for r in caplog.records)



def test_cleanup_expired_tasks() -> None:
    """Verifies cleanup_expired_tasks removes tasks exceeding retention and calls delete_task."""
    hook = MockPersistenceHook()
    manager = LongRunningTaskManager(persistence_hook=hook)

    old_time = datetime.now(timezone.utc) - timedelta(seconds=100000)
    t_old = LongRunningTask(
        task_id="t_old",
        name="Old Task",
        status=LongRunningTaskStatus.COMPLETED,
        completed_at=old_time,
        created_at=old_time,
    )
    t_fresh = manager.create_task(name="Fresh Task")
    assert t_fresh is not None
    manager.complete_task(t_fresh.task_id)

    # Inject old task into completed history
    manager._completed_tasks.append(t_old)

    cleaned = manager.cleanup_expired_tasks(retention_seconds=86400)
    assert cleaned == 1
    assert "t_old" in hook.deleted_task_ids
    assert manager.get_task("t_old") is None
    assert manager.get_task(t_fresh.task_id) is not None


def test_check_timeouts_detection() -> None:
    """Verifies check_timeouts detects active tasks older than timeout limit."""
    manager = LongRunningTaskManager(config=LongRunningTaskConfig(default_timeout=10))
    listener = MockEventListener()
    manager.event_dispatcher.register_listener(listener)

    # Manually inject active task created 20s ago
    old_time = datetime.now(timezone.utc) - timedelta(seconds=20)
    task = LongRunningTask(
        task_id="t_timeout",
        name="Stale Task",
        status=LongRunningTaskStatus.RUNNING,
        created_at=old_time,
        updated_at=old_time,
    )
    manager._active_tasks[task.task_id] = task

    timed_out = manager.check_timeouts()
    assert timed_out == 1

    t_check = manager.get_task("t_timeout")
    assert t_check is not None
    assert t_check.status == LongRunningTaskStatus.TIMED_OUT

    event_types = [e.event_type for e in listener.events]
    assert TaskEventType.TASK_TIMED_OUT in event_types


def test_archive_task_event_and_logging(caplog: Any) -> None:
    """Verifies archiving task emits TASK_ARCHIVED event and logs structured message."""
    manager = LongRunningTaskManager()
    listener = MockEventListener()
    manager.event_dispatcher.register_listener(listener)

    task = manager.create_task(name="Task To Archive")
    assert task is not None

    with caplog.at_level(logging.INFO):
        manager.complete_task(task.task_id)

    event_types = [e.event_type for e in listener.events]
    assert TaskEventType.TASK_ARCHIVED in event_types
    log_messages = [r.message for r in caplog.records]
    assert "Task Archived" in log_messages


def test_persistence_failure_isolation(caplog: Any) -> None:
    """Verifies exceptions raised by custom persistence hook do not interrupt manager execution."""
    failing_hook = MockPersistenceHook(should_fail=True)
    manager = LongRunningTaskManager(persistence_hook=failing_hook)

    with caplog.at_level(logging.WARNING):
        task = manager.create_task(name="Failure Safety Task")
        assert task is not None
        assert manager.start_task(task.task_id) is True
        assert manager.complete_task(task.task_id) is True

    assert "Persistence Hook Failed" in [r.message for r in caplog.records]


def test_event_generation_recovered_archived_cleaned() -> None:
    """Verifies TASK_RECOVERED, TASK_ARCHIVED, TASK_CLEANED events are emitted correctly."""
    now = datetime.now(timezone.utc)
    t_rec = LongRunningTask(task_id="t_rec", name="Rec Task", status=LongRunningTaskStatus.RUNNING, created_at=now)

    hook = MockPersistenceHook(tasks_to_load=[t_rec])
    manager = LongRunningTaskManager(persistence_hook=hook)
    listener = MockEventListener()
    manager.event_dispatcher.register_listener(listener)

    manager.recover_tasks()
    manager.complete_task("t_rec")

    # Manually backdate for retention cleanup
    t_rec.completed_at = now - timedelta(seconds=100000)
    manager.cleanup_expired_tasks(retention_seconds=3600)

    event_types = [e.event_type for e in listener.events]
    assert TaskEventType.TASK_RECOVERED in event_types
    assert TaskEventType.TASK_ARCHIVED in event_types
    assert TaskEventType.TASK_CLEANED in event_types


def test_monitoring_integration_persistence_metrics() -> None:
    """Verifies ExecutionMonitor records recovered, archived, and cleaned metrics from events."""
    manager = LongRunningTaskManager()
    monitor = ExecutionMonitor(task_manager=manager)

    now = datetime.now(timezone.utc)
    t_rec = LongRunningTask(task_id="t_m1", name="M Task", status=LongRunningTaskStatus.RUNNING, created_at=now)
    manager.persistence_hook.load_tasks = lambda: [t_rec]

    manager.recover_tasks()
    manager.complete_task("t_m1")

    t_rec.completed_at = now - timedelta(seconds=100000)
    manager.cleanup_expired_tasks(retention_seconds=10)

    stats = monitor.get_event_statistics()
    assert stats["recovered_tasks"] == 1
    assert stats["archived_tasks"] == 1
    assert stats["cleaned_tasks"] == 1


def test_dependency_injection() -> None:
    """Verifies LongRunningTaskManager accepts custom persistence_hook in constructor."""
    hook = MockPersistenceHook()
    manager = LongRunningTaskManager(persistence_hook=hook)

    assert manager.persistence_hook is hook


def test_backward_compatibility() -> None:
    """Verifies default manager works seamlessly without passing persistence_hook."""
    manager = LongRunningTaskManager()
    assert isinstance(manager.persistence_hook, NullTaskPersistenceHook)

    task = manager.create_task(name="Default Manager Task")
    assert task is not None
    assert manager.start_task(task.task_id) is True
    assert manager.complete_task(task.task_id) is True
