"""Unit tests for LongRunningTaskManager and associated domain models."""

from __future__ import annotations

from datetime import datetime, timezone
import threading
import time
# pyrefly: ignore [missing-import]
pytest = None
try:
    # pyrefly: ignore [missing-import]
    import pytest
except ImportError:
    pass

from brain.execution.long_running_task_manager import (
    LongRunningTask,
    LongRunningTaskConfig,
    LongRunningTaskManager,
    LongRunningTaskPriority,
    LongRunningTaskStatus,
)


def test_create_task() -> None:
    """Verifies creating a task registers it in PENDING state."""
    manager = LongRunningTaskManager()
    task = manager.create_task(
        name="Workspace Indexing",
        description="Index all source files",
        total_steps=10,
        tags=["indexing", "workspace"],
    )

    assert task is not None
    assert task.task_id.startswith("task_")
    assert task.name == "Workspace Indexing"
    assert task.status == LongRunningTaskStatus.PENDING
    assert task.priority == LongRunningTaskPriority.NORMAL
    assert task.total_steps == 10
    assert "indexing" in task.tags
    assert task.is_active() is True
    assert task.is_finished() is False


def test_queue_task() -> None:
    """Verifies queuing a PENDING task."""
    manager = LongRunningTaskManager()
    task = manager.create_task("Sync Repo")
    assert task is not None

    success = manager.queue_task(task.task_id)
    assert success is True

    updated = manager.get_task(task.task_id)
    assert updated is not None
    assert updated.status == LongRunningTaskStatus.QUEUED


def test_start_task() -> None:
    """Verifies starting a task updates status to RUNNING and sets started_at timestamp."""
    manager = LongRunningTaskManager()
    task = manager.create_task("Document Processing")
    assert task is not None

    assert task.started_at is None
    success = manager.start_task(task.task_id)
    assert success is True

    updated = manager.get_task(task.task_id)
    assert updated is not None
    assert updated.status == LongRunningTaskStatus.RUNNING
    assert updated.started_at is not None


def test_pause_task() -> None:
    """Verifies pausing a RUNNING task."""
    manager = LongRunningTaskManager()
    task = manager.create_task("Batch Processing")
    assert task is not None
    manager.start_task(task.task_id)

    success = manager.pause_task(task.task_id)
    assert success is True

    updated = manager.get_task(task.task_id)
    assert updated is not None
    assert updated.status == LongRunningTaskStatus.PAUSED


def test_resume_task() -> None:
    """Verifies resuming a PAUSED task back to RUNNING state."""
    manager = LongRunningTaskManager()
    task = manager.create_task("AI Summarization")
    assert task is not None
    manager.start_task(task.task_id)
    manager.pause_task(task.task_id)

    success = manager.resume_task(task.task_id)
    assert success is True

    updated = manager.get_task(task.task_id)
    assert updated is not None
    assert updated.status == LongRunningTaskStatus.RUNNING


def test_cancel_task() -> None:
    """Verifies cancelling an active task marks it CANCELLED."""
    manager = LongRunningTaskManager()
    task = manager.create_task("Long Scan")
    assert task is not None

    success = manager.cancel_task(task.task_id)
    assert success is True

    updated = manager.get_task(task.task_id)
    assert updated is not None
    assert updated.status == LongRunningTaskStatus.CANCELLED
    assert updated.completed_at is not None
    assert updated.is_finished() is True


def test_fail_task() -> None:
    """Verifies failing a task records error trace."""
    manager = LongRunningTaskManager()
    task = manager.create_task("File Transfer")
    assert task is not None
    manager.start_task(task.task_id)

    success = manager.fail_task(task.task_id, "Network disconnection timeout")
    assert success is True

    updated = manager.get_task(task.task_id)
    assert updated is not None
    assert updated.status == LongRunningTaskStatus.FAILED
    assert updated.error == "Network disconnection timeout"
    assert updated.completed_at is not None


def test_timeout_task() -> None:
    """Verifies timing out a task marks it TIMED_OUT."""
    manager = LongRunningTaskManager()
    task = manager.create_task("Heavy Computation")
    assert task is not None
    manager.start_task(task.task_id)

    success = manager.timeout_task(task.task_id)
    assert success is True

    updated = manager.get_task(task.task_id)
    assert updated is not None
    assert updated.status == LongRunningTaskStatus.TIMED_OUT
    assert updated.error == "Task execution timed out"


def test_complete_task() -> None:
    """Verifies completing a task updates progress to 100% and stores result metadata."""
    manager = LongRunningTaskManager()
    task = manager.create_task("Data Export")
    assert task is not None
    manager.start_task(task.task_id)

    success = manager.complete_task(task.task_id, result_metadata={"files_exported": 42})
    assert success is True

    updated = manager.get_task(task.task_id)
    assert updated is not None
    assert updated.status == LongRunningTaskStatus.COMPLETED
    assert updated.progress == 100.0
    assert updated.metadata["files_exported"] == 42


def test_update_progress() -> None:
    """Verifies updating progress percentage, steps, and metadata."""
    manager = LongRunningTaskManager()
    task = manager.create_task("Large Indexing", total_steps=100)
    assert task is not None
    manager.start_task(task.task_id)

    success = manager.update_progress(
        task.task_id,
        progress=45.5,
        current_step=45,
        estimated_progress=48.0,
        metadata={"active_file": "src/main.py"},
    )
    assert success is True

    updated = manager.get_task(task.task_id)
    assert updated is not None
    assert updated.progress == 45.5
    assert updated.current_step == 45
    assert updated.estimated_progress == 48.0
    assert updated.metadata["active_file"] == "src/main.py"


def test_metadata_preservation() -> None:
    """Verifies custom metadata and tags are preserved throughout updates."""
    manager = LongRunningTaskManager()
    task = manager.create_task(
        "Backup Job",
        metadata={"cluster": "us-east-1"},
        tags=["infra", "backup"],
    )
    assert task is not None

    manager.start_task(task.task_id)
    manager.update_progress(task.task_id, progress=50.0, metadata={"bytes_written": 1024})

    updated = manager.get_task(task.task_id)
    assert updated is not None
    assert updated.metadata["cluster"] == "us-east-1"
    assert updated.metadata["bytes_written"] == 1024
    assert "infra" in updated.tags


def test_history_cleanup() -> None:
    """Verifies cleanup moves finished tasks to history and prunes active store."""
    config = LongRunningTaskConfig(cleanup_after_completion=False)
    manager = LongRunningTaskManager(config=config)

    t1 = manager.create_task("Task 1")
    t2 = manager.create_task("Task 2")
    assert t1 is not None and t2 is not None

    manager.complete_task(t1.task_id)
    manager.fail_task(t2.task_id, "Error")

    assert len(manager.list_tasks()) == 2
    cleaned_count = manager.cleanup()

    assert cleaned_count == 2
    assert manager.get_task(t1.task_id) is not None
    assert manager.get_task(t2.task_id) is not None


def test_maximum_task_limits() -> None:
    """Verifies manager enforces capacity limit configuration."""
    config = LongRunningTaskConfig(maximum_tasks=3, cleanup_after_completion=False)
    manager = LongRunningTaskManager(config=config)

    t1 = manager.create_task("Task 1")
    t2 = manager.create_task("Task 2")
    t3 = manager.create_task("Task 3")
    assert t1 and t2 and t3

    # Attempting 4th active task when limit is 3 should trigger cleanup or return None
    t4 = manager.create_task("Task 4")
    assert t4 is None


def test_thread_safety() -> None:
    """Verifies thread-safe concurrent creation and state updates."""
    manager = LongRunningTaskManager()
    errors: list[Exception] = []

    def worker(worker_id: int) -> None:
        try:
            for i in range(10):
                task = manager.create_task(f"Task_{worker_id}_{i}")
                if task:
                    manager.start_task(task.task_id)
                    manager.update_progress(task.task_id, progress=50.0)
                    manager.complete_task(task.task_id)
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0
    assert len(manager.list_completed()) == 50


def test_dependency_injection_compatibility() -> None:
    """Verifies manager accepts custom configuration and logger objects."""
    config = LongRunningTaskConfig(maximum_tasks=200, default_timeout=7200)
    manager = LongRunningTaskManager(config=config)

    task = manager.create_task("Injected Config Task")
    assert task is not None
    assert manager._config.maximum_tasks == 200
    assert manager._config.default_timeout == 7200


def test_unknown_task_handling() -> None:
    """Verifies safe handling of unknown or invalid task IDs without throwing exceptions."""
    manager = LongRunningTaskManager()

    assert manager.get_task("non_existent_id") is None
    assert manager.queue_task("non_existent_id") is False
    assert manager.start_task("non_existent_id") is False
    assert manager.pause_task("non_existent_id") is False
    assert manager.resume_task("non_existent_id") is False
    assert manager.cancel_task("non_existent_id") is False
    assert manager.complete_task("non_existent_id") is False
    assert manager.fail_task("non_existent_id", "error") is False
    assert manager.timeout_task("non_existent_id") is False
    assert manager.update_progress("non_existent_id", progress=10.0) is False
    assert manager.get_task("") is None
    assert manager.get_task(None) is None


def test_list_running_and_completed() -> None:
    """Verifies listing active running vs completed tasks."""
    manager = LongRunningTaskManager()

    t1 = manager.create_task("Task Run 1")
    t2 = manager.create_task("Task Run 2")
    t3 = manager.create_task("Task Run 3")
    assert t1 and t2 and t3

    manager.start_task(t1.task_id)
    manager.start_task(t2.task_id)
    manager.complete_task(t3.task_id)

    running = manager.list_running()
    completed = manager.list_completed()

    assert len(running) == 2
    assert len(completed) == 1
    assert t3.task_id in [t.task_id for t in completed]
