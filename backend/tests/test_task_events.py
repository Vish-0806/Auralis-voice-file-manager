"""Unit and integration tests for TaskEvents progress monitoring and event notification layer."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, List
# pyrefly: ignore [missing-import]
pytest = None
try:
    # pyrefly: ignore [missing-import]
    import pytest
except ImportError:
    pass

from brain.execution.execution_monitor import ExecutionMonitor
from brain.execution.long_running_task_manager import (
    LongRunningTaskManager,
)
from brain.execution.task_events import (
    TaskEvent,
    TaskEventDispatcher,
    TaskEventType,
)


class MockListener:
    """Mock event listener accumulating events."""

    def __init__(self, should_raise: bool = False) -> None:
        self.should_raise = should_raise
        self.received_events: List[TaskEvent] = []

    def on_event(self, event: TaskEvent) -> None:
        if self.should_raise:
            raise RuntimeError("Simulated listener exception")
        self.received_events.append(event)


def test_register_listener() -> None:
    """Verifies registering listeners in TaskEventDispatcher."""
    dispatcher = TaskEventDispatcher()
    listener = MockListener()

    assert dispatcher.listener_count() == 0
    assert dispatcher.register_listener(listener) is True
    assert dispatcher.listener_count() == 1

    # Duplicate registration returns False
    assert dispatcher.register_listener(listener) is False
    assert dispatcher.listener_count() == 1


def test_remove_listener() -> None:
    """Verifies removing registered listeners."""
    dispatcher = TaskEventDispatcher()
    listener = MockListener()

    dispatcher.register_listener(listener)
    assert dispatcher.remove_listener(listener) is True
    assert dispatcher.listener_count() == 0
    assert dispatcher.remove_listener(listener) is False


def test_dispatch_events() -> None:
    """Verifies single event dispatch to registered listeners."""
    dispatcher = TaskEventDispatcher()
    listener = MockListener()
    dispatcher.register_listener(listener)

    event = TaskEvent(
        task_id="t1",
        event_type=TaskEventType.TASK_CREATED,
        message="Created task",
    )

    notified = dispatcher.dispatch(event)
    assert notified == 1
    assert len(listener.received_events) == 1
    assert listener.received_events[0].task_id == "t1"
    assert listener.received_events[0].event_type == TaskEventType.TASK_CREATED


def test_multiple_listeners() -> None:
    """Verifies event broadcasting to multiple registered listeners."""
    dispatcher = TaskEventDispatcher()
    l1 = MockListener()
    l2 = MockListener()
    l3 = MockListener()

    dispatcher.register_listener(l1)
    dispatcher.register_listener(l2)
    dispatcher.register_listener(l3)

    event = TaskEvent(task_id="t2", event_type=TaskEventType.TASK_STARTED)
    notified = dispatcher.dispatch(event)

    assert notified == 3
    assert len(l1.received_events) == 1
    assert len(l2.received_events) == 1
    assert len(l3.received_events) == 1


def test_listener_failure_isolation(caplog: Any) -> None:
    """Verifies exceptions in one listener do not disrupt dispatching to other listeners."""
    dispatcher = TaskEventDispatcher()
    failing_l = MockListener(should_raise=True)
    normal_l = MockListener()

    dispatcher.register_listener(failing_l)
    dispatcher.register_listener(normal_l)

    event = TaskEvent(task_id="t3", event_type=TaskEventType.TASK_PROGRESS, progress=50.0)

    with caplog.at_level(logging.WARNING):
        notified = dispatcher.dispatch(event)

    # Both attempted, 1 succeeded without throwing
    assert notified == 1
    assert len(normal_l.received_events) == 1
    assert "Listener Error" in [record.message for record in caplog.records]


def test_progress_events() -> None:
    """Verifies TASK_PROGRESS event payload structure and values."""
    dispatcher = TaskEventDispatcher()
    listener = MockListener()
    dispatcher.register_listener(listener)

    event = TaskEvent(
        task_id="t_prog",
        event_type=TaskEventType.TASK_PROGRESS,
        progress=75.5,
        current_step=3,
        total_steps=4,
    )
    dispatcher.dispatch(event)

    ev = listener.received_events[0]
    assert ev.event_type == TaskEventType.TASK_PROGRESS
    assert ev.progress == 75.5
    assert ev.current_step == 3
    assert ev.total_steps == 4


def test_completion_events() -> None:
    """Verifies TASK_COMPLETED event handling."""
    dispatcher = TaskEventDispatcher()
    listener = MockListener()
    dispatcher.register_listener(listener)

    event = TaskEvent(
        task_id="t_comp",
        event_type=TaskEventType.TASK_COMPLETED,
        progress=100.0,
    )
    dispatcher.dispatch(event)

    ev = listener.received_events[0]
    assert ev.event_type == TaskEventType.TASK_COMPLETED
    assert ev.progress == 100.0


def test_cancellation_events() -> None:
    """Verifies TASK_CANCELLED event handling."""
    dispatcher = TaskEventDispatcher()
    listener = MockListener()
    dispatcher.register_listener(listener)

    event = TaskEvent(
        task_id="t_cancel",
        event_type=TaskEventType.TASK_CANCELLED,
        message="Task cancelled by user",
    )
    dispatcher.dispatch(event)

    ev = listener.received_events[0]
    assert ev.event_type == TaskEventType.TASK_CANCELLED
    assert ev.message == "Task cancelled by user"


def test_timeout_events() -> None:
    """Verifies TASK_TIMED_OUT event handling."""
    dispatcher = TaskEventDispatcher()
    listener = MockListener()
    dispatcher.register_listener(listener)

    event = TaskEvent(
        task_id="t_timeout",
        event_type=TaskEventType.TASK_TIMED_OUT,
        message="Task execution timed out",
    )
    dispatcher.dispatch(event)

    ev = listener.received_events[0]
    assert ev.event_type == TaskEventType.TASK_TIMED_OUT
    assert ev.message == "Task execution timed out"


def test_thread_safety() -> None:
    """Verifies thread-safe registration and dispatch under high concurrency."""
    dispatcher = TaskEventDispatcher()
    listener = MockListener()
    threads = []

    def register_and_dispatch(idx: int) -> None:
        dispatcher.register_listener(listener)
        ev = TaskEvent(task_id=f"t_thread_{idx}", event_type=TaskEventType.TASK_PROGRESS)
        dispatcher.dispatch(ev)

    for i in range(20):
        t = threading.Thread(target=register_and_dispatch, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    assert dispatcher.listener_count() == 1
    assert len(listener.received_events) == 20


def test_integration_with_long_running_task_manager() -> None:
    """Verifies LongRunningTaskManager automatically emits TaskEvents across state transitions."""
    manager = LongRunningTaskManager()
    listener = MockListener()
    manager.event_dispatcher.register_listener(listener)

    task = manager.create_task(name="Scan Workspace", total_steps=2)
    assert task is not None
    manager.queue_task(task.task_id)
    manager.start_task(task.task_id)
    manager.update_progress(task.task_id, progress=50.0, current_step=1)
    manager.complete_task(task.task_id)

    event_types = [e.event_type for e in listener.received_events]
    assert TaskEventType.TASK_CREATED in event_types
    assert TaskEventType.TASK_QUEUED in event_types
    assert TaskEventType.TASK_STARTED in event_types
    assert TaskEventType.TASK_PROGRESS in event_types
    assert TaskEventType.TASK_COMPLETED in event_types


def test_monitoring_integration() -> None:
    """Verifies ExecutionMonitor subscribes to events and collects event statistics."""
    manager = LongRunningTaskManager()
    monitor = ExecutionMonitor(task_manager=manager)

    task = manager.create_task(name="Indexing", total_steps=1)
    assert task is not None
    manager.start_task(task.task_id)
    manager.update_progress(task.task_id, progress=100.0, current_step=1)
    manager.complete_task(task.task_id)

    event_stats = monitor.get_event_statistics()
    assert event_stats["total_events"] >= 4
    assert event_stats["completion_events"] == 1
    assert event_stats["event_completion_rate"] > 0.0
    assert event_stats["average_task_progress"] == 100.0


def test_backward_compatibility() -> None:
    """Verifies LongRunningTaskManager works seamlessly without custom listeners or dispatchers."""
    manager = LongRunningTaskManager()
    task = manager.create_task(name="Ordinary Task")
    assert task is not None
    assert manager.start_task(task.task_id) is True
    assert manager.complete_task(task.task_id) is True
