"""Unit and integration tests for BackgroundJobScheduler runtime execution pipeline integration."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
from typing import Any, Dict, List
# pyrefly: ignore [missing-import]
pytest = None
try:
    # pyrefly: ignore [missing-import]
    import pytest
except ImportError:
    pass

from brain.execution.background_job_scheduler import (
    BackgroundJob,
    BackgroundJobPriority,
    BackgroundJobScheduler,
    BackgroundJobStatus,
    BackgroundJobTriggerType,
    convert_to_execution_request,
)
from brain.execution.execution_engine import ExecutionEngine
from brain.execution.execution_monitor import ExecutionMonitor


class MockDispatcher:
    """Mock capability dispatcher returning predictable responses."""

    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.executed_plans: List[Any] = []

    def dispatch(self, plan: Any) -> Any:
        self.executed_plans.append(plan)
        if self.should_fail:
            raise RuntimeError("Mock Dispatch Failure")
        from core.models import ExecutionResult
        return ExecutionResult(success=True, response="Dispatched successfully", execution_time=0.01)



def test_convert_to_execution_request() -> None:
    """Verifies convert_to_execution_request converts BackgroundJob to an execution request payload."""
    job = BackgroundJob(
        job_id="job_conv_1",
        name="Scan Repo",
        priority=BackgroundJobPriority.HIGH,
        trigger_type=BackgroundJobTriggerType.INTERVAL,
        parameters={"interval_seconds": 600, "target": "workspace_scan"},
        metadata={"category": "maintenance"},
        tags=["scan", "repo"],
    )

    request = convert_to_execution_request(job)
    assert request is not None
    assert getattr(request, "intent", None) is not None or "intent" in request



def test_start_job_execution() -> None:
    """Verifies start_job_execution transitions READY job to RUNNING and updates last_run."""
    scheduler = BackgroundJobScheduler()
    job = scheduler.create_job(name="Task Start", trigger_type=BackgroundJobTriggerType.MANUAL)
    assert job is not None

    job.status = BackgroundJobStatus.READY
    assert scheduler.start_job_execution(job.job_id) is True
    running_job = scheduler.get_job(job.job_id)
    assert running_job is not None
    assert running_job.status == BackgroundJobStatus.RUNNING
    assert running_job.last_run is not None


def test_complete_job_execution_one_time() -> None:
    """Verifies one-time job is marked COMPLETED and archived to history."""
    scheduler = BackgroundJobScheduler()
    job = scheduler.create_job(name="Once Job", trigger_type=BackgroundJobTriggerType.ONCE)
    assert job is not None

    scheduler.start_job_execution(job.job_id)
    assert scheduler.complete_job_execution(job.job_id, result_metadata={"output": "ok"}) is True

    done_job = scheduler.get_job(job.job_id)
    assert done_job is not None
    assert done_job.status == BackgroundJobStatus.COMPLETED
    assert done_job.metadata.get("output") == "ok"


def test_complete_job_execution_recurring() -> None:
    """Verifies recurring job is rescheduled with updated next_run timestamp."""
    scheduler = BackgroundJobScheduler()
    job = scheduler.create_job(
        name="Interval Job",
        trigger_type=BackgroundJobTriggerType.INTERVAL,
        parameters={"interval_seconds": 300},
    )
    assert job is not None

    scheduler.start_job_execution(job.job_id)
    assert scheduler.complete_job_execution(job.job_id) is True

    rescheduled = scheduler.get_job(job.job_id)
    assert rescheduled is not None
    assert rescheduled.status == BackgroundJobStatus.SCHEDULED
    assert rescheduled.next_run is not None


def test_fail_job_execution_recurring() -> None:
    """Verifies failing a recurring job records error and reschedules next run."""
    scheduler = BackgroundJobScheduler()
    job = scheduler.create_job(
        name="Daily Job",
        trigger_type=BackgroundJobTriggerType.DAILY,
        parameters={"time_of_day": "10:00"},
    )
    assert job is not None

    scheduler.start_job_execution(job.job_id)
    assert scheduler.fail_job_execution(job.job_id, "Connection timeout") is True

    failed_job = scheduler.get_job(job.job_id)
    assert failed_job is not None
    assert failed_job.status == BackgroundJobStatus.SCHEDULED
    assert failed_job.metadata.get("last_error") == "Connection timeout"


def test_execution_engine_dependency_injection() -> None:
    """Verifies ExecutionEngine accepts custom BackgroundJobScheduler in constructor."""
    scheduler = BackgroundJobScheduler()
    engine = ExecutionEngine(job_scheduler=scheduler)

    assert engine.job_scheduler is scheduler


def test_execute_ready_scheduled_jobs_success() -> None:
    """Verifies execute_ready_scheduled_jobs runs ready jobs and updates their completion status."""
    scheduler = BackgroundJobScheduler()
    engine = ExecutionEngine(job_scheduler=scheduler)
    dispatcher = MockDispatcher()

    job = scheduler.create_job(
        name="Ready Job Test",
        trigger_type=BackgroundJobTriggerType.ONCE,
        parameters={"delay_seconds": -10},
    )
    assert job is not None

    results = engine.execute_ready_scheduled_jobs(dispatcher=dispatcher)
    assert len(results) == 1

    done = scheduler.get_job(job.job_id)
    assert done is not None
    assert done.status == BackgroundJobStatus.COMPLETED


def test_execute_ready_scheduled_jobs_failure() -> None:
    """Verifies execute_ready_scheduled_jobs handles execution failure gracefully."""
    scheduler = BackgroundJobScheduler()
    engine = ExecutionEngine(job_scheduler=scheduler)
    failing_dispatcher = MockDispatcher(should_fail=True)

    job = scheduler.create_job(
        name="Failing Job Test",
        trigger_type=BackgroundJobTriggerType.ONCE,
        parameters={"delay_seconds": -5},
    )
    assert job is not None

    results = engine.execute_ready_scheduled_jobs(dispatcher=failing_dispatcher)
    assert len(results) == 1

    failed = scheduler.get_job(job.job_id)
    assert failed is not None
    assert failed.status == BackgroundJobStatus.FAILED


def test_long_running_task_trigger_integration() -> None:
    """Verifies scheduled job payload qualifying as long-running creates task record in LongRunningTaskManager."""
    scheduler = BackgroundJobScheduler()
    engine = ExecutionEngine(job_scheduler=scheduler)

    job = scheduler.create_job(
        name="Long Running Workspace Sync",
        trigger_type=BackgroundJobTriggerType.ONCE,
        parameters={"delay_seconds": -5, "is_long_running": True, "job_type": "indexing"},
    )
    assert job is not None

    engine.execute_ready_scheduled_jobs()
    tasks = engine.task_manager.list_tasks()
    assert len(tasks) >= 1


def test_scheduler_failure_isolation(caplog: Any) -> None:
    """Verifies scheduler exceptions during execute_ready_scheduled_jobs are logged and isolated."""
    class FailingScheduler(BackgroundJobScheduler):
        def list_ready_jobs(self, current_time: Any = None) -> List[BackgroundJob]:
            raise RuntimeError("Scheduler List Error")

    failing_scheduler = FailingScheduler()
    engine = ExecutionEngine(job_scheduler=failing_scheduler)

    with caplog.at_level(logging.WARNING):
        results = engine.execute_ready_scheduled_jobs()

    assert results == []
    assert any("Failed to list ready scheduled jobs" in r.message for r in caplog.records)


def test_execution_monitor_scheduled_metrics() -> None:
    """Verifies ExecutionMonitor includes scheduled job metrics in get_statistics()."""
    scheduler = BackgroundJobScheduler()
    monitor = ExecutionMonitor(job_scheduler=scheduler)

    job = scheduler.create_job(
        name="Monitored Job",
        trigger_type=BackgroundJobTriggerType.ONCE,
        parameters={"delay_seconds": -10},
    )
    assert job is not None

    scheduler.list_ready_jobs()
    scheduler.start_job_execution(job.job_id)
    scheduler.complete_job_execution(job.job_id)

    stats = monitor.get_statistics()
    assert stats.scheduled_jobs_executed >= 1
    assert hasattr(stats, "ready_job_count")


def test_structured_logging(caplog: Any) -> None:
    """Verifies structured logging outputs for scheduled job lifecycle events."""
    scheduler = BackgroundJobScheduler()
    engine = ExecutionEngine(job_scheduler=scheduler)

    job = scheduler.create_job(
        name="Log Test Job",
        trigger_type=BackgroundJobTriggerType.INTERVAL,
        parameters={"interval_seconds": -10},
    )
    assert job is not None

    dispatcher = MockDispatcher()
    future_time = datetime.now(timezone.utc) + timedelta(seconds=10)

    with caplog.at_level(logging.INFO):
        engine.execute_ready_scheduled_jobs(dispatcher=dispatcher, current_time=future_time)



    messages = [r.message for r in caplog.records]
    assert any("Scheduled Job Ready" in m for m in messages)
    assert any("Scheduled Job Started" in m for m in messages)
    assert any("Scheduled Job Completed" in m for m in messages)
    assert any("Recurring Job Rescheduled" in m for m in messages)


def test_backward_compatibility() -> None:
    """Verifies default ExecutionEngine works seamlessly without passing job_scheduler."""
    engine = ExecutionEngine()
    assert isinstance(engine.job_scheduler, BackgroundJobScheduler)

    results = engine.execute_ready_scheduled_jobs()
    assert results == []
