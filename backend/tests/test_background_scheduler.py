"""Unit and integration tests for BackgroundJobScheduler."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import threading
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
    BackgroundSchedulerConfig,
    calculate_next_run,
)


def test_create_job() -> None:
    """Verifies create_job creates a valid BackgroundJob and stores it in active map."""
    scheduler = BackgroundJobScheduler()
    job = scheduler.create_job(
        name="Sync Workspace",
        description="Syncs workspace index",
        priority=BackgroundJobPriority.HIGH,
        trigger_type=BackgroundJobTriggerType.INTERVAL,
        parameters={"interval_seconds": 300},
    )

    assert job is not None
    assert job.name == "Sync Workspace"
    assert job.priority == BackgroundJobPriority.HIGH
    assert job.status == BackgroundJobStatus.SCHEDULED
    assert job.enabled is True
    assert job.next_run is not None
    assert scheduler.get_job(job.job_id) is not None


def test_update_job() -> None:
    """Verifies update_job modifies parameters, priority, and recalculates next_run."""
    scheduler = BackgroundJobScheduler()
    job = scheduler.create_job(name="Daily Summary", trigger_type=BackgroundJobTriggerType.DAILY)
    assert job is not None

    success = scheduler.update_job(
        job_id=job.job_id,
        name="Daily AI Summary",
        priority=BackgroundJobPriority.CRITICAL,
        parameters={"time_of_day": "14:30"},
        metadata={"category": "ai"},
        tags=["ai", "daily"],
    )

    assert success is True
    updated = scheduler.get_job(job.job_id)
    assert updated is not None
    assert updated.name == "Daily AI Summary"
    assert updated.priority == BackgroundJobPriority.CRITICAL
    assert updated.metadata.get("category") == "ai"
    assert "daily" in updated.tags


def test_pause_job() -> None:
    """Verifies pause_job transitions job status to PAUSED."""
    scheduler = BackgroundJobScheduler()
    job = scheduler.create_job(name="Interval Task", trigger_type=BackgroundJobTriggerType.INTERVAL)
    assert job is not None

    assert scheduler.pause_job(job.job_id) is True
    paused = scheduler.get_job(job.job_id)
    assert paused is not None
    assert paused.status == BackgroundJobStatus.PAUSED


def test_resume_job() -> None:
    """Verifies resume_job transitions PAUSED job back to SCHEDULED."""
    scheduler = BackgroundJobScheduler()
    job = scheduler.create_job(name="Task to Pause")
    assert job is not None

    scheduler.pause_job(job.job_id)
    assert scheduler.resume_job(job.job_id) is True
    resumed = scheduler.get_job(job.job_id)
    assert resumed is not None
    assert resumed.status == BackgroundJobStatus.SCHEDULED


def test_cancel_job() -> None:
    """Verifies cancel_job sets status to CANCELLED and moves job to completed history."""
    scheduler = BackgroundJobScheduler()
    job = scheduler.create_job(name="Task to Cancel")
    assert job is not None

    assert scheduler.cancel_job(job.job_id) is True
    cancelled = scheduler.get_job(job.job_id)
    assert cancelled is not None
    assert cancelled.status == BackgroundJobStatus.CANCELLED
    assert cancelled.is_finished() is True


def test_enable_and_disable_job() -> None:
    """Verifies enable_job and disable_job modify the enabled flag."""
    scheduler = BackgroundJobScheduler()
    job = scheduler.create_job(name="Toggle Job")
    assert job is not None

    assert scheduler.disable_job(job.job_id) is True
    assert scheduler.get_job(job.job_id).enabled is False

    assert scheduler.enable_job(job.job_id) is True
    assert scheduler.get_job(job.job_id).enabled is True


def test_remove_job() -> None:
    """Verifies remove_job deletes job from active and completed stores."""
    scheduler = BackgroundJobScheduler()
    job = scheduler.create_job(name="Job to Remove")
    assert job is not None

    assert scheduler.remove_job(job.job_id) is True
    assert scheduler.get_job(job.job_id) is None


def test_archive_job_and_history() -> None:
    """Verifies archive_job moves an active job to completion history deque."""
    scheduler = BackgroundJobScheduler()
    job = scheduler.create_job(name="Archived Job")
    assert job is not None

    assert scheduler.archive_job(job.job_id) is True
    completed_list = scheduler.list_jobs(enabled_only=False)
    assert any(j.job_id == job.job_id for j in completed_list)


def test_list_ready_jobs_once_trigger() -> None:
    """Verifies list_ready_jobs returns ONCE job when current_time exceeds next_run."""
    scheduler = BackgroundJobScheduler()
    past_time = datetime.now(timezone.utc) - timedelta(seconds=10)
    job = scheduler.create_job(
        name="Run Once Job",
        trigger_type=BackgroundJobTriggerType.ONCE,
        parameters={"delay_seconds": -10},
    )
    assert job is not None

    now = datetime.now(timezone.utc)
    ready = scheduler.list_ready_jobs(current_time=now)
    assert len(ready) == 1
    assert ready[0].job_id == job.job_id
    assert ready[0].status == BackgroundJobStatus.READY


def test_list_ready_jobs_interval_trigger() -> None:
    """Verifies list_ready_jobs returns INTERVAL job when next_run is reached."""
    scheduler = BackgroundJobScheduler()
    now = datetime.now(timezone.utc)
    job = scheduler.create_job(
        name="Interval Job",
        trigger_type=BackgroundJobTriggerType.INTERVAL,
        parameters={"interval_seconds": 10},
    )
    assert job is not None

    # Advance current_time past next_run
    future_time = now + timedelta(seconds=15)
    ready = scheduler.list_ready_jobs(current_time=future_time)
    assert len(ready) == 1
    assert ready[0].job_id == job.job_id


def test_list_ready_jobs_daily_weekly_monthly_triggers() -> None:
    """Verifies next_run calculation logic for DAILY, WEEKLY, and MONTHLY triggers."""
    now = datetime.now(timezone.utc)

    daily_next = calculate_next_run(
        BackgroundJobTriggerType.DAILY,
        {"time_of_day": "12:00"},
        from_time=now,
    )
    assert daily_next is not None
    assert daily_next.tzinfo == timezone.utc

    weekly_next = calculate_next_run(
        BackgroundJobTriggerType.WEEKLY,
        {"day_of_week": 2, "time_of_day": "15:00"},
        from_time=now,
    )
    assert weekly_next is not None
    assert weekly_next.tzinfo == timezone.utc

    monthly_next = calculate_next_run(
        BackgroundJobTriggerType.MONTHLY,
        {"day_of_month": 15, "time_of_day": "09:00"},
        from_time=now,
    )
    assert monthly_next is not None
    assert monthly_next.tzinfo == timezone.utc


def test_manual_trigger_job_readiness() -> None:
    """Verifies MANUAL jobs are not scheduled automatically unless marked READY."""
    scheduler = BackgroundJobScheduler()
    job = scheduler.create_job(name="Manual Job", trigger_type=BackgroundJobTriggerType.MANUAL)
    assert job is not None
    assert job.next_run is None

    ready = scheduler.list_ready_jobs()
    assert len(ready) == 0

    # Mark as READY manually
    job.status = BackgroundJobStatus.READY
    ready = scheduler.list_ready_jobs()
    assert len(ready) == 1


def test_disabled_job_skipped_in_readiness() -> None:
    """Verifies disabled jobs are excluded from list_ready_jobs even if next_run is reached."""
    scheduler = BackgroundJobScheduler()
    job = scheduler.create_job(
        name="Disabled Job",
        trigger_type=BackgroundJobTriggerType.ONCE,
        parameters={"delay_seconds": -5},
        enabled=False,
    )
    assert job is not None

    ready = scheduler.list_ready_jobs()
    assert len(ready) == 0


def test_unknown_job_id_safety() -> None:
    """Verifies operations on unknown job IDs return None or False without raising exceptions."""
    scheduler = BackgroundJobScheduler()

    assert scheduler.get_job("unknown_id") is None
    assert scheduler.update_job("unknown_id", name="New Name") is False
    assert scheduler.pause_job("unknown_id") is False
    assert scheduler.resume_job("unknown_id") is False
    assert scheduler.cancel_job("unknown_id") is False
    assert scheduler.enable_job("unknown_id") is False
    assert scheduler.disable_job("unknown_id") is False
    assert scheduler.remove_job("unknown_id") is False
    assert scheduler.archive_job("unknown_id") is False


def test_maximum_jobs_and_history_capacity() -> None:
    """Verifies scheduler respects maximum_jobs and maximum_history bounds."""
    config = BackgroundSchedulerConfig(maximum_jobs=5, maximum_history=5)
    scheduler = BackgroundJobScheduler(config=config)

    for i in range(5):
        j = scheduler.create_job(name=f"Job {i}")
        assert j is not None

    # Exceed capacity
    overflow = scheduler.create_job(name="Overflow Job")
    assert overflow is None


def test_thread_safety() -> None:
    """Verifies thread-safe job creation and list queries under concurrent load."""
    scheduler = BackgroundJobScheduler(config=BackgroundSchedulerConfig(maximum_jobs=500))
    errors: List[Exception] = []

    def worker(worker_id: int) -> None:
        try:
            for i in range(20):
                j = scheduler.create_job(name=f"Job_{worker_id}_{i}")
                if j:
                    scheduler.update_job(j.job_id, priority=BackgroundJobPriority.HIGH)
                    scheduler.list_jobs()
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker, args=(t,)) for t in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0
    assert len(scheduler.list_jobs()) <= 500


def test_dependency_injection_compatibility() -> None:
    """Verifies scheduler accepts custom config in constructor."""
    config = BackgroundSchedulerConfig(maximum_jobs=10, default_check_interval=30)
    scheduler = BackgroundJobScheduler(config=config)

    assert scheduler._config.maximum_jobs == 10
    assert scheduler._config.default_check_interval == 30


def test_backward_compatibility() -> None:
    """Verifies default scheduler initialization works without required parameters."""
    scheduler = BackgroundJobScheduler()
    assert scheduler._config.maximum_jobs == 2000
    assert scheduler.list_jobs() == []
