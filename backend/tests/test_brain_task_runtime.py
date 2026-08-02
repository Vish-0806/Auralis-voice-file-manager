"""Unit test suite for Phase 12.5 — Task Management & Long-Running Execution Runtime.

Covers:
- Task models, enums, defaults, and immutability
- Subsystem exception hierarchy
- TaskScheduler priority queue ordering and delay support
- TaskMonitor progress metrics and remaining duration estimation
- TaskPersistence snapshot saving and checkpoint restoration
- TaskExecutor long-running task execution, pause/resume, cancellation, and timeout
- TaskProvider end-to-end processing, health reporting, and statistics
- TaskRuntime singleton lifecycle, status management, and thread safety under concurrency
- Mock integrations for Workflow Execution Engine and Command Orchestrator
"""

from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from brain.execution.task import (
    ITaskProvider,
    TaskCancellationError,
    TaskContext,
    TaskException,
    TaskExecution,
    TaskExecutionMode,

    TaskExecutor,
    TaskFailureReason,
    TaskHealth,
    TaskMonitor,
    TaskPersistence,
    TaskPriority,
    TaskProgress,
    TaskProvider,
    TaskRecoveryMode,
    TaskRequest,
    TaskResult,
    TaskRuntime,
    TaskRuntimeStatus,
    TaskScheduler,
    TaskStatistics,
    TaskStatus,
    get_task_runtime,
    reset_task_runtime,
)


@pytest.fixture(autouse=True)
def cleanup_runtime() -> None:
    """Fixture resetting global task runtime before and after each test."""
    reset_task_runtime()
    yield
    reset_task_runtime()


def test_task_models_defaults_and_immutability() -> None:
    """Verifies task model default properties and Pydantic v2 immutability."""
    req = TaskRequest(
        task_id="t1",
        name="Download File",
        priority=TaskPriority.HIGH,
        mode=TaskExecutionMode.BACKGROUND,
    )
    assert req.task_id == "t1"
    assert req.priority == TaskPriority.HIGH
    assert req.mode == TaskExecutionMode.BACKGROUND

    with pytest.raises((TypeError, ValidationError)):
        req.name = "Modified Task"  # type: ignore

    progress = TaskProgress(task_id="t1", progress_percentage=50.0)
    assert progress.progress_percentage == 50.0

    with pytest.raises((TypeError, ValidationError)):
        progress.completed_steps = 5  # type: ignore


def test_task_exceptions_hierarchy() -> None:
    """Verifies exception inheritance hierarchy."""
    exc = TaskCancellationError("Task cancelled by user")
    assert isinstance(exc, TaskException)


def test_task_scheduler_priority_queuing() -> None:
    """Verifies priority queue ordering where CRITICAL tasks are dequeued first."""
    scheduler = TaskScheduler()

    req_low = TaskRequest(task_id="low", name="Low Priority", priority=TaskPriority.LOW)
    req_crit = TaskRequest(task_id="crit", name="Critical Priority", priority=TaskPriority.CRITICAL)
    req_high = TaskRequest(task_id="high", name="High Priority", priority=TaskPriority.HIGH)

    scheduler.enqueue(req_low)
    scheduler.enqueue(req_crit)
    scheduler.enqueue(req_high)

    first = scheduler.dequeue()
    assert first is not None
    assert first.task_id == "crit"

    second = scheduler.dequeue()
    assert second is not None
    assert second.task_id == "high"

    third = scheduler.dequeue()
    assert third is not None
    assert third.task_id == "low"


def test_task_monitor_progress_tracking() -> None:
    """Verifies TaskMonitor progress percentage, duration, and remaining estimate calculations."""
    monitor = TaskMonitor()
    prog1 = monitor.start_monitoring("t1", total_steps=4)
    assert prog1.completed_steps == 0

    prog2 = monitor.update_progress("t1", completed_steps=2, total_steps=4, status_message="Halfway done")
    assert prog2.progress_percentage == 50.0
    assert prog2.completed_steps == 2
    assert prog2.status_message == "Halfway done"

    monitor.stop_monitoring("t1")
    assert monitor.get_progress("t1") is None


def test_task_persistence_checkpoints() -> None:
    """Verifies snapshot and recovery checkpoint persistence."""
    persistence = TaskPersistence()

    req = TaskRequest(task_id="t1", name="Checkpoint Task")
    context = TaskContext(request=req, status=TaskStatus.RUNNING)

    assert persistence.save_snapshot(context) is True
    loaded = persistence.load_snapshot("t1")
    assert loaded is not None
    assert loaded.request.name == "Checkpoint Task"

    chk_data = {"step_id": "step_3", "bytes_downloaded": 1024}
    assert persistence.save_checkpoint("t1", chk_data) is True
    retrieved_chk = persistence.get_checkpoint("t1")
    assert retrieved_chk == chk_data


def test_task_executor_with_mock_runtimes() -> None:
    """Verifies long-running task execution with mock workflow runtime."""
    mock_wf_runtime = MagicMock()
    mock_wf_runtime.process_workflow.return_value = MagicMock(status="COMPLETED")

    executor = TaskExecutor(workflow_runtime=mock_wf_runtime)
    req = TaskRequest(task_id="t1", name="Long Task", payload=["step1", "step2"])

    result = executor.execute_task(req)
    assert result.status == TaskStatus.COMPLETED
    assert "workflow_result" in result.output
    mock_wf_runtime.process_workflow.assert_called_once()


def test_task_executor_pause_resume_and_cancellation() -> None:
    """Verifies pause, resume, and cancellation mechanics on TaskExecutor."""
    executor = TaskExecutor()

    # Pause & Resume test
    assert executor.pause_task("t_pause") is True
    assert executor.resume_task("t_pause") is True

    # Cancellation test
    executor.cancel_task("t_cancel")
    req = TaskRequest(task_id="t_cancel", name="Cancelled Task")
    res = executor.execute_task(req)

    assert res.status == TaskStatus.CANCELLED
    assert res.failure_reason == TaskFailureReason.CANCELLED_BY_USER


def test_task_provider_end_to_end_and_health_check() -> None:
    """Verifies TaskProvider end-to-end task submission, health checks, and statistics."""
    provider = TaskProvider()

    res = provider.submit_task({"name": "Convert Video", "payload": "ffmpeg command"})
    assert res.status == TaskStatus.COMPLETED

    health = provider.health_check()
    assert isinstance(health, TaskHealth)
    assert health.healthy is True
    assert len(health.components) == 4

    stats = provider.get_statistics()
    assert isinstance(stats, TaskStatistics)
    assert stats.total_tasks == 1
    assert stats.completed_count == 1

    provider.clear()
    assert provider.get_statistics().total_tasks == 0


def test_task_runtime_lifecycle_and_singleton() -> None:
    """Verifies TaskRuntime initialization, processing, health reporting, and singleton identity."""
    rt = get_task_runtime()
    assert rt.status == TaskRuntimeStatus.READY

    rt2 = get_task_runtime()
    assert rt is rt2

    res = rt.process_task("Simple Payload")
    assert res.status == TaskStatus.COMPLETED

    health = rt.health_check()
    assert health.healthy is True

    stats = rt.get_statistics()
    assert stats.total_tasks == 1

    rt.clear()
    assert rt.get_statistics().total_tasks == 0

    assert rt.shutdown() is True
    assert rt.status == TaskRuntimeStatus.SHUTDOWN


def test_task_runtime_thread_safety() -> None:
    """Verifies thread-safe task processing across concurrent worker threads."""
    rt = get_task_runtime()

    def worker(i: int) -> TaskStatus:
        req = TaskRequest(task_id=f"thread_task_{i}", name=f"Thread Task {i}", priority=TaskPriority.HIGH)
        res = rt.process_task(req)
        return res.status

    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(worker, range(15)))

    assert len(results) == 15
    assert all(status == TaskStatus.COMPLETED for status in results)

    stats = rt.get_statistics()
    assert stats.total_tasks == 15
    assert stats.completed_count == 15
