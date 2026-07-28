"""Unit tests for BackgroundJobPersistenceHook, NullBackgroundJobPersistenceHook, scheduler recovery, expiration, cleanup policies, and execution monitoring."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
import threading
from typing import Any, Dict, List

from brain.execution.background_job_scheduler import (
    BackgroundJob,
    BackgroundJobPriority,
    BackgroundJobScheduler,
    BackgroundJobStatus,
    BackgroundJobTriggerType,
    BackgroundSchedulerConfig,
    NullBackgroundJobPersistenceHook,
)
from brain.execution.execution_monitor import ExecutionMonitor


class MemoryTestPersistenceHook:
    """In-memory persistence hook implementation for testing."""

    def __init__(self) -> None:
        self.store: Dict[str, BackgroundJob] = {}
        self.save_calls: List[str] = []
        self.update_calls: List[str] = []
        self.delete_calls: List[str] = []
        self.load_calls: int = 0
        self.should_fail: bool = False

    def save_job(self, job: BackgroundJob) -> bool:
        if self.should_fail:
            raise RuntimeError("Database connection lost during save")
        self.save_calls.append(job.job_id)
        self.store[job.job_id] = job
        return True

    def update_job(self, job: BackgroundJob) -> bool:
        if self.should_fail:
            raise RuntimeError("Database connection lost during update")
        self.update_calls.append(job.job_id)
        self.store[job.job_id] = job
        return True

    def delete_job(self, job_id: str) -> bool:
        if self.should_fail:
            raise RuntimeError("Database connection lost during delete")
        self.delete_calls.append(job_id)
        self.store.pop(job_id, None)
        return True

    def load_jobs(self) -> List[BackgroundJob]:
        if self.should_fail:
            raise RuntimeError("Database connection lost during load")
        self.load_calls += 1
        return list(self.store.values())


def test_null_persistence_hook() -> None:
    """Verifies NullBackgroundJobPersistenceHook methods execute safely with default return values."""
    hook = NullBackgroundJobPersistenceHook()
    job = BackgroundJob(job_id="job_null_1", name="Test Null Job")

    assert hook.save_job(job) is True
    assert hook.update_job(job) is True
    assert hook.delete_job("job_null_1") is True
    assert hook.load_jobs() == []


def test_custom_persistence_hook() -> None:
    """Verifies BackgroundJobScheduler delegates lifecycle operations to the custom persistence hook."""
    hook = MemoryTestPersistenceHook()
    scheduler = BackgroundJobScheduler(persistence_hook=hook)

    # Create
    job = scheduler.create_job(name="Persisted Job", trigger_type=BackgroundJobTriggerType.MANUAL)
    assert job is not None
    assert job.job_id in hook.save_calls

    # Update
    scheduler.update_job(job.job_id, description="Updated summary")
    assert job.job_id in hook.update_calls

    # Remove
    scheduler.remove_job(job.job_id)
    assert job.job_id in hook.delete_calls


def test_recover_jobs_valid() -> None:
    """Verifies recover_jobs loads jobs from hook, validates triggers, and restores active and terminal state."""
    hook = MemoryTestPersistenceHook()
    now = datetime.now(timezone.utc)

    active_job = BackgroundJob(
        job_id="job_active_rec",
        name="Active Recovered",
        status=BackgroundJobStatus.SCHEDULED,
        trigger_type=BackgroundJobTriggerType.INTERVAL,
        parameters={"interval_seconds": 60},
    )
    finished_job = BackgroundJob(
        job_id="job_finished_rec",
        name="Finished Recovered",
        status=BackgroundJobStatus.COMPLETED,
        trigger_type=BackgroundJobTriggerType.ONCE,
        updated_at=now,
    )
    hook.store[active_job.job_id] = active_job
    hook.store[finished_job.job_id] = finished_job

    scheduler = BackgroundJobScheduler(persistence_hook=hook)
    recovered_count = scheduler.recover_jobs()

    assert recovered_count == 2
    assert scheduler.get_job("job_active_rec") is not None
    assert scheduler.get_job("job_finished_rec") is not None


def test_recover_jobs_corrupted_jobs(caplog: Any) -> None:
    """Verifies recover_jobs skips corrupted jobs and logs warnings."""
    hook = MemoryTestPersistenceHook()

    # Valid job
    valid_job = BackgroundJob(
        job_id="job_valid",
        name="Valid Job",
        status=BackgroundJobStatus.SCHEDULED,
        trigger_type=BackgroundJobTriggerType.MANUAL,
    )
    # Corrupted trigger params
    invalid_trigger_job = BackgroundJob(
        job_id="job_invalid_trigger",
        name="Invalid Trigger Job",
        status=BackgroundJobStatus.SCHEDULED,
        trigger_type=BackgroundJobTriggerType.INTERVAL,
        parameters={"interval_seconds": -500},
    )
    hook.store[valid_job.job_id] = valid_job
    hook.store[invalid_trigger_job.job_id] = invalid_trigger_job

    scheduler = BackgroundJobScheduler(persistence_hook=hook)
    with caplog.at_level(logging.WARNING):
        recovered_count = scheduler.recover_jobs()

    assert recovered_count == 1
    assert scheduler.get_job("job_valid") is not None
    assert scheduler.get_job("job_invalid_trigger") is None
    assert any("Corrupted Job Skipped" in r.message for r in caplog.records)


def test_expire_jobs_once() -> None:
    """Verifies expire_jobs expires past ONCE jobs and archives them."""
    scheduler = BackgroundJobScheduler()
    past_time = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    future_ref = datetime(2026, 7, 28, 12, 0, 0, tzinfo=timezone.utc)

    job = scheduler.create_job(
        name="Past ONCE Job",
        trigger_type=BackgroundJobTriggerType.ONCE,
        parameters={"run_at": past_time.isoformat()},
    )
    assert job is not None

    expired_count = scheduler.expire_jobs(current_time=future_ref)
    assert expired_count == 1
    assert job.status == BackgroundJobStatus.EXPIRED


def test_expire_jobs_recurring_never_expire() -> None:
    """Verifies recurring jobs (INTERVAL, DAILY, WEEKLY, MONTHLY, MANUAL) never expire."""
    scheduler = BackgroundJobScheduler()
    past_ref = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    future_ref = datetime(2026, 7, 28, 12, 0, 0, tzinfo=timezone.utc)

    job_interval = scheduler.create_job(
        name="Past Interval Job",
        trigger_type=BackgroundJobTriggerType.INTERVAL,
        parameters={"interval_seconds": 60},
    )
    job_daily = scheduler.create_job(
        name="Daily Job",
        trigger_type=BackgroundJobTriggerType.DAILY,
        parameters={"time_of_day": "00:00"},
    )
    assert job_interval is not None
    assert job_daily is not None

    expired_count = scheduler.expire_jobs(current_time=future_ref)
    assert expired_count == 0
    assert job_interval.status != BackgroundJobStatus.EXPIRED
    assert job_daily.status != BackgroundJobStatus.EXPIRED


def test_cleanup_expired_jobs() -> None:
    """Verifies cleanup_expired_jobs removes terminal jobs older than retention_seconds."""
    hook = MemoryTestPersistenceHook()
    config = BackgroundSchedulerConfig(retention_seconds=3600)  # 1 hour
    scheduler = BackgroundJobScheduler(config=config, persistence_hook=hook)

    now = datetime(2026, 7, 28, 12, 0, 0, tzinfo=timezone.utc)
    old_time = now - timedelta(seconds=7200)  # 2 hours ago

    # Completed job older than retention
    old_completed = BackgroundJob(
        job_id="job_old_comp",
        name="Old Completed",
        status=BackgroundJobStatus.COMPLETED,
        trigger_type=BackgroundJobTriggerType.ONCE,
        updated_at=old_time,
    )
    # Recent completed job within retention
    recent_completed = BackgroundJob(
        job_id="job_recent_comp",
        name="Recent Completed",
        status=BackgroundJobStatus.COMPLETED,
        trigger_type=BackgroundJobTriggerType.ONCE,
        updated_at=now - timedelta(seconds=300),
    )
    hook.store[old_completed.job_id] = old_completed
    hook.store[recent_completed.job_id] = recent_completed
    scheduler.recover_jobs()

    stats = scheduler.cleanup_expired_jobs(current_time=now)
    assert stats["cleaned_completed"] == 1
    assert stats["total_cleaned"] == 1
    assert scheduler.get_job("job_old_comp") is None
    assert scheduler.get_job("job_recent_comp") is not None


def test_cleanup_history_retention_period() -> None:
    """Verifies recent completed jobs are preserved during cleanup."""
    config = BackgroundSchedulerConfig(retention_seconds=86400)
    scheduler = BackgroundJobScheduler(config=config)
    now = datetime.now(timezone.utc)

    job = scheduler.create_job(name="Retention Job", trigger_type=BackgroundJobTriggerType.ONCE)
    assert job is not None
    scheduler.complete_job_execution(job.job_id)

    stats = scheduler.cleanup_expired_jobs(current_time=now)
    assert stats["total_cleaned"] == 0
    assert scheduler.get_job(job.job_id) is not None


def test_persistence_failure_isolation_save(caplog: Any) -> None:
    """Verifies persistence failures in save_job raise warnings without crashing runtime."""
    hook = MemoryTestPersistenceHook()
    hook.should_fail = True
    scheduler = BackgroundJobScheduler(persistence_hook=hook)

    with caplog.at_level(logging.WARNING):
        job = scheduler.create_job(name="Failing Save Job", trigger_type=BackgroundJobTriggerType.MANUAL)

    assert job is not None
    assert any("Persistence Failure" in r.message for r in caplog.records)


def test_persistence_failure_isolation_update(caplog: Any) -> None:
    """Verifies persistence failures in update_job raise warnings without crashing runtime."""
    hook = MemoryTestPersistenceHook()
    scheduler = BackgroundJobScheduler(persistence_hook=hook)

    job = scheduler.create_job(name="Normal Job", trigger_type=BackgroundJobTriggerType.MANUAL)
    assert job is not None

    hook.should_fail = True
    with caplog.at_level(logging.WARNING):
        success = scheduler.update_job(job.job_id, name="Updated Failing Job")

    assert success is True
    assert any("Persistence Failure" in r.message for r in caplog.records)


def test_persistence_failure_isolation_delete(caplog: Any) -> None:
    """Verifies persistence failures in delete_job raise warnings without crashing runtime."""
    hook = MemoryTestPersistenceHook()
    scheduler = BackgroundJobScheduler(persistence_hook=hook)

    job = scheduler.create_job(name="Delete Test Job", trigger_type=BackgroundJobTriggerType.MANUAL)
    assert job is not None

    hook.should_fail = True
    with caplog.at_level(logging.WARNING):
        success = scheduler.remove_job(job.job_id)

    assert success is True
    assert any("Persistence Failure" in r.message for r in caplog.records)


def test_persistence_failure_isolation_load(caplog: Any) -> None:
    """Verifies persistence failures in load_jobs return empty list without crashing recover_jobs."""
    hook = MemoryTestPersistenceHook()
    hook.should_fail = True
    scheduler = BackgroundJobScheduler(persistence_hook=hook)

    with caplog.at_level(logging.WARNING):
        recovered_count = scheduler.recover_jobs()

    assert recovered_count == 0
    assert any("Persistence Failure" in r.message for r in caplog.records)


def test_execution_monitor_scheduler_statistics() -> None:
    """Verifies ExecutionMonitor get_scheduler_statistics provides accurate summary."""
    scheduler = BackgroundJobScheduler()
    monitor = ExecutionMonitor(job_scheduler=scheduler)

    job = scheduler.create_job(name="Monitored Persistence Job", trigger_type=BackgroundJobTriggerType.MANUAL)
    assert job is not None

    stats = monitor.get_scheduler_statistics()
    assert stats["active_jobs"] == 1
    assert stats["total_jobs"] == 1
    assert stats["status_counts"]["SCHEDULED"] == 1


def test_dependency_injection_persistence_hook() -> None:
    """Verifies constructor dependency injection and persistence_hook property access."""
    hook = MemoryTestPersistenceHook()
    scheduler = BackgroundJobScheduler(persistence_hook=hook)

    assert scheduler.persistence_hook is hook


def test_thread_safety_persistence() -> None:
    """Verifies recover_jobs, expire_jobs, and cleanup_expired_jobs execute safely across multiple threads."""
    hook = MemoryTestPersistenceHook()
    scheduler = BackgroundJobScheduler(persistence_hook=hook)

    for i in range(20):
        scheduler.create_job(name=f"Concurrent Job {i}", trigger_type=BackgroundJobTriggerType.MANUAL)

    errors: List[Exception] = []

    def worker() -> None:
        try:
            for _ in range(5):
                scheduler.expire_jobs()
                scheduler.cleanup_expired_jobs()
                scheduler.recover_jobs()
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0


def test_backward_compatibility_persistence() -> None:
    """Verifies default BackgroundJobScheduler instantiation defaults to NullBackgroundJobPersistenceHook."""
    scheduler = BackgroundJobScheduler()
    assert isinstance(scheduler.persistence_hook, NullBackgroundJobPersistenceHook)
