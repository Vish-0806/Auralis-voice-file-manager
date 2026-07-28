"""Background Job Scheduler for managing scheduled job lifecycles and readiness."""

from __future__ import annotations

from collections import deque
from datetime import datetime, timedelta, timezone
from enum import Enum
import logging
import threading
import uuid
from typing import Any, Dict, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


class BackgroundJobStatus(str, Enum):
    """Lifecycle status states for a background scheduled job."""

    SCHEDULED = "SCHEDULED"
    READY = "READY"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class BackgroundJobPriority(str, Enum):
    """Priority levels for scheduled background jobs."""

    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class BackgroundJobTriggerType(str, Enum):
    """Supported trigger types for calculating job run readiness."""

    ONCE = "ONCE"
    INTERVAL = "INTERVAL"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    MANUAL = "MANUAL"


class BackgroundJob(BaseModel):
    """Domain model representing a scheduled background execution job."""

    job_id: str = Field(description="Unique identifier for the scheduled job")
    name: str = Field(description="Human readable title or name of the job")
    description: Optional[str] = Field(default=None, description="Optional job description")
    status: BackgroundJobStatus = Field(
        default=BackgroundJobStatus.SCHEDULED,
        description="Current lifecycle status of the job",
    )
    priority: BackgroundJobPriority = Field(
        default=BackgroundJobPriority.NORMAL,
        description="Scheduling priority level",
    )
    trigger_type: BackgroundJobTriggerType = Field(
        default=BackgroundJobTriggerType.MANUAL,
        description="Trigger schedule mechanism",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp in UTC",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last update timestamp in UTC",
    )
    next_run: Optional[datetime] = Field(
        default=None,
        description="Calculated next run timestamp in UTC",
    )
    last_run: Optional[datetime] = Field(
        default=None,
        description="Timestamp when job was last executed or triggered",
    )
    execution_plan: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Execution plan specification payload for the job",
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Trigger parameters (e.g. interval_seconds, time_of_day, day_of_week)",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Custom job metadata dictionary",
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Categorization tags",
    )
    enabled: bool = Field(
        default=True,
        description="Flag indicating whether job scheduling is active",
    )

    def is_finished(self) -> bool:
        """Determines whether job is in a terminal state."""
        return self.status in (
            BackgroundJobStatus.COMPLETED,
            BackgroundJobStatus.FAILED,
            BackgroundJobStatus.CANCELLED,
            BackgroundJobStatus.EXPIRED,
        )


class BackgroundSchedulerConfig(BaseModel):
    """Configuration container for BackgroundJobScheduler."""

    maximum_jobs: int = Field(
        default=2000,
        ge=1,
        description="Maximum active/scheduled jobs allowed in memory",
    )
    cleanup_history: bool = Field(
        default=True,
        description="Automatically move terminal jobs to completed history",
    )
    maximum_history: int = Field(
        default=5000,
        ge=1,
        description="Maximum completed job history records retained",
    )
    default_check_interval: int = Field(
        default=60,
        ge=1,
        description="Default check interval in seconds for interval triggers",
    )


def calculate_next_run(
    trigger_type: BackgroundJobTriggerType,
    parameters: Dict[str, Any],
    from_time: Optional[datetime] = None,
) -> Optional[datetime]:
    """Calculates next run timestamp based on trigger type and parameters.

    Args:
        trigger_type: Scheduling trigger mechanism.
        parameters: Trigger parameters dictionary.
        from_time: Reference timestamp (defaults to UTC now).

    Returns:
        Calculated next run datetime in UTC, or None if trigger is MANUAL.
    """
    ref_time = from_time or datetime.now(timezone.utc)
    if not ref_time.tzinfo:
        ref_time = ref_time.replace(tzinfo=timezone.utc)

    if trigger_type == BackgroundJobTriggerType.MANUAL:
        return None

    if trigger_type == BackgroundJobTriggerType.ONCE:
        run_at = parameters.get("run_at")
        if isinstance(run_at, datetime):
            return run_at if run_at.tzinfo else run_at.replace(tzinfo=timezone.utc)
        if isinstance(run_at, str):
            try:
                dt = datetime.fromisoformat(run_at)
                return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
            except Exception:
                pass
        delay_seconds = float(parameters.get("delay_seconds", 0))
        return ref_time + timedelta(seconds=delay_seconds)

    if trigger_type == BackgroundJobTriggerType.INTERVAL:
        interval = float(parameters.get("interval_seconds", 60))
        return ref_time + timedelta(seconds=max(1.0, interval))

    if trigger_type == BackgroundJobTriggerType.DAILY:
        time_str = str(parameters.get("time_of_day", "00:00"))
        try:
            parts = time_str.split(":")
            hour, minute = int(parts[0]), int(parts[1])
        except Exception:
            hour, minute = 0, 0
        target = ref_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target <= ref_time:
            target += timedelta(days=1)
        return target

    if trigger_type == BackgroundJobTriggerType.WEEKLY:
        day_of_week = int(parameters.get("day_of_week", 0)) % 7
        time_str = str(parameters.get("time_of_day", "00:00"))
        try:
            parts = time_str.split(":")
            hour, minute = int(parts[0]), int(parts[1])
        except Exception:
            hour, minute = 0, 0
        days_ahead = (day_of_week - ref_time.weekday()) % 7
        target = ref_time.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=days_ahead)
        if target <= ref_time:
            target += timedelta(days=7)
        return target

    if trigger_type == BackgroundJobTriggerType.MONTHLY:
        day_of_month = max(1, min(28, int(parameters.get("day_of_month", 1))))
        time_str = str(parameters.get("time_of_day", "00:00"))
        try:
            parts = time_str.split(":")
            hour, minute = int(parts[0]), int(parts[1])
        except Exception:
            hour, minute = 0, 0
        target = ref_time.replace(day=day_of_month, hour=hour, minute=minute, second=0, microsecond=0)
        if target <= ref_time:
            target = target + timedelta(days=30)
        return target

    return None


def convert_to_execution_request(job: BackgroundJob) -> Any:
    """Converts a BackgroundJob instance into an execution plan request.

    Args:
        job: Source BackgroundJob instance.

    Returns:
        RoutedExecutionPlan or dictionary payload suitable for ExecutionEngine plan execution.
    """
    if not job or not isinstance(job, BackgroundJob):
        return {}

    plan_payload = dict(job.execution_plan) if job.execution_plan else {}
    intent_val = plan_payload.get("intent") or job.name
    target_val = plan_payload.get("target") or job.name

    params = dict(job.parameters)
    params.update(plan_payload.get("parameters", {}))
    params["job_id"] = job.job_id
    params["job_priority"] = job.priority.value if hasattr(job.priority, "value") else str(job.priority)
    params.setdefault("auto_approved", True)
    params.setdefault("dangerous_operation", False)


    metadata = dict(job.metadata)
    metadata.update(plan_payload.get("metadata", {}))
    metadata["job_id"] = job.job_id
    metadata["trigger_type"] = job.trigger_type.value if hasattr(job.trigger_type, "value") else str(job.trigger_type)
    params["metadata"] = metadata

    tags = list(set(job.tags + plan_payload.get("tags", [])))

    try:
        from brain.capability.models import CapabilityRoute, RoutedExecutionPlan
        from core.intents import Intent

        intent_enum = Intent.SEARCH_FILE
        if isinstance(intent_val, Intent):
            intent_enum = intent_val
        elif isinstance(intent_val, str):
            for member in Intent:
                if member.value.lower() == intent_val.lower() or member.name.lower() == intent_val.lower():
                    intent_enum = member
                    break


        cap_name = str(plan_payload.get("capability_name") or "mock_file")
        route = CapabilityRoute(step_id="step_1", intent=intent_enum, capability_name=cap_name)

        return RoutedExecutionPlan(
            intent=intent_enum,
            target=str(target_val),
            parameters=params,
            confidence=float(plan_payload.get("confidence", 1.0)),
            routes=[route],
        )
    except Exception as err:
        logging.getLogger(__name__).warning("convert_to_execution_request failed to create RoutedExecutionPlan", exc_info=err)




    plan_payload["execution_id"] = job.job_id
    plan_payload["intent"] = intent_val
    plan_payload["target"] = target_val
    plan_payload["parameters"] = params
    plan_payload["metadata"] = metadata
    plan_payload["tags"] = tags
    return plan_payload



class BackgroundJobScheduler:
    """Manages scheduled background jobs thread-safely."""


    def __init__(
        self,
        config: Optional[BackgroundSchedulerConfig] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """Initializes the scheduler with configuration options and internal storage.

        Args:
            config: Optional BackgroundSchedulerConfig settings.
            logger: Optional custom logger.
        """
        self._config = config or BackgroundSchedulerConfig()
        self._logger = logger or logging.getLogger(__name__)
        self._lock = threading.RLock()
        self._active_jobs: Dict[str, BackgroundJob] = {}
        self._completed_jobs: deque[BackgroundJob] = deque(
            maxlen=self._config.maximum_history
        )

    def create_job(
        self,
        name: str,
        description: Optional[str] = None,
        priority: BackgroundJobPriority = BackgroundJobPriority.NORMAL,
        trigger_type: BackgroundJobTriggerType = BackgroundJobTriggerType.MANUAL,
        execution_plan: Optional[Dict[str, Any]] = None,
        parameters: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        enabled: bool = True,
        job_id: Optional[str] = None,
    ) -> Optional[BackgroundJob]:
        """Creates a new scheduled background job record.

        Args:
            name: Job title or name.
            description: Optional summary description.
            priority: Scheduling priority level.
            trigger_type: Schedule trigger mechanism.
            execution_plan: Execution plan payload.
            parameters: Trigger parameters.
            metadata: Custom metadata dictionary.
            tags: Category tags.
            enabled: Initial enabled state.
            job_id: Explicit job ID or None to auto-generate.

        Returns:
            Created BackgroundJob or None if capacity exceeded or invalid arguments.
        """
        if not name:
            return None

        with self._lock:
            if len(self._active_jobs) >= self._config.maximum_jobs:
                self.cleanup()
                if len(self._active_jobs) >= self._config.maximum_jobs:
                    return None

            jid = job_id or f"job_{uuid.uuid4().hex[:12]}"
            now = datetime.now(timezone.utc)
            params = parameters or {}
            next_run = calculate_next_run(trigger_type, params, now)

            job = BackgroundJob(
                job_id=jid,
                name=name,
                description=description,
                status=BackgroundJobStatus.SCHEDULED,
                priority=priority,
                trigger_type=trigger_type,
                created_at=now,
                updated_at=now,
                next_run=next_run,
                execution_plan=execution_plan,
                parameters=params,
                metadata=metadata or {},
                tags=tags or [],
                enabled=enabled,
            )

            self._active_jobs[jid] = job
            self._logger.info("Job Created", extra={"job_id": jid, "job_name": name})
            return job

    def update_job(
        self,
        job_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[BackgroundJobPriority] = None,
        trigger_type: Optional[BackgroundJobTriggerType] = None,
        parameters: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> bool:
        """Updates parameters and metadata of an active job.

        Args:
            job_id: Target job ID.
            name: Optional new name.
            description: Optional new description.
            priority: Optional new priority.
            trigger_type: Optional new trigger type.
            parameters: Optional new parameters.
            metadata: Optional metadata updates to merge.
            tags: Optional new tags list.

        Returns:
            True if updated, False if unknown or in terminal state.
        """
        if not job_id or not isinstance(job_id, str):
            return False

        with self._lock:
            job = self._active_jobs.get(job_id)
            if not job or job.is_finished():
                return False

            now = datetime.now(timezone.utc)
            if name is not None:
                job.name = name
            if description is not None:
                job.description = description
            if priority is not None:
                job.priority = priority
            if parameters is not None:
                job.parameters = parameters
            if trigger_type is not None:
                job.trigger_type = trigger_type

            if trigger_type is not None or parameters is not None:
                job.next_run = calculate_next_run(job.trigger_type, job.parameters, now)

            if metadata:
                job.metadata.update(metadata)
            if tags is not None:
                job.tags = tags

            job.updated_at = now
            self._logger.info("Job Updated", extra={"job_id": job_id})
            return True

    def pause_job(self, job_id: str) -> bool:
        """Transitions a job to PAUSED status.

        Args:
            job_id: Target job ID.

        Returns:
            True if paused, False if unknown or in terminal state.
        """
        if not job_id or not isinstance(job_id, str):
            return False

        with self._lock:
            job = self._active_jobs.get(job_id)
            if not job or job.is_finished():
                return False

            job.status = BackgroundJobStatus.PAUSED
            job.updated_at = datetime.now(timezone.utc)
            self._logger.info("Job Paused", extra={"job_id": job_id})
            return True

    def resume_job(self, job_id: str) -> bool:
        """Resumes a PAUSED job back to SCHEDULED status.

        Args:
            job_id: Target job ID.

        Returns:
            True if resumed, False if unknown or not paused.
        """
        if not job_id or not isinstance(job_id, str):
            return False

        with self._lock:
            job = self._active_jobs.get(job_id)
            if not job or job.status != BackgroundJobStatus.PAUSED:
                return False

            job.status = BackgroundJobStatus.SCHEDULED
            job.updated_at = datetime.now(timezone.utc)
            self._logger.info("Job Resumed", extra={"job_id": job_id})
            return True

    def cancel_job(self, job_id: str) -> bool:
        """Cancels a scheduled job.

        Args:
            job_id: Target job ID.

        Returns:
            True if cancelled, False if unknown or already finished.
        """
        if not job_id or not isinstance(job_id, str):
            return False

        with self._lock:
            job = self._active_jobs.get(job_id)
            if not job or job.is_finished():
                return False

            now = datetime.now(timezone.utc)
            job.status = BackgroundJobStatus.CANCELLED
            job.updated_at = now

            if self._config.cleanup_history:
                self._archive_job_locked(job)

            self._logger.info("Job Cancelled", extra={"job_id": job_id})
            return True

    def remove_job(self, job_id: str) -> bool:
        """Removes a job completely from active and completed stores.

        Args:
            job_id: Target job ID.

        Returns:
            True if removed, False if job not found.
        """
        if not job_id or not isinstance(job_id, str):
            return False

        with self._lock:
            removed_active = self._active_jobs.pop(job_id, None)
            filtered_history = [j for j in self._completed_jobs if j.job_id != job_id]
            removed_history = len(filtered_history) < len(self._completed_jobs)
            if removed_history:
                self._completed_jobs = deque(filtered_history, maxlen=self._config.maximum_history)

            return (removed_active is not None) or removed_history

    def enable_job(self, job_id: str) -> bool:
        """Enables job scheduling execution.

        Args:
            job_id: Target job ID.

        Returns:
            True if enabled, False if unknown or finished.
        """
        if not job_id or not isinstance(job_id, str):
            return False

        with self._lock:
            job = self._active_jobs.get(job_id)
            if not job or job.is_finished():
                return False

            job.enabled = True
            job.updated_at = datetime.now(timezone.utc)
            self._logger.info("Job Enabled", extra={"job_id": job_id})
            return True

    def disable_job(self, job_id: str) -> bool:
        """Disables job scheduling execution without cancelling it.

        Args:
            job_id: Target job ID.

        Returns:
            True if disabled, False if unknown or finished.
        """
        if not job_id or not isinstance(job_id, str):
            return False

        with self._lock:
            job = self._active_jobs.get(job_id)
            if not job or job.is_finished():
                return False

            job.enabled = False
            job.updated_at = datetime.now(timezone.utc)
            self._logger.info("Job Disabled", extra={"job_id": job_id})
            return True

    def get_job(self, job_id: str) -> Optional[BackgroundJob]:
        """Retrieves a job by ID from active or completed stores.

        Args:
            job_id: Target job ID.

        Returns:
            Matching BackgroundJob or None if not found.
        """
        if not job_id or not isinstance(job_id, str):
            return None

        with self._lock:
            if job_id in self._active_jobs:
                return self._active_jobs[job_id]

            for job in self._completed_jobs:
                if job.job_id == job_id:
                    return job

            return None

    def list_jobs(
        self,
        status: Optional[BackgroundJobStatus] = None,
        enabled_only: bool = False,
    ) -> List[BackgroundJob]:
        """Lists jobs across active and completed stores.

        Args:
            status: Optional filter by job status.
            enabled_only: Optional filter for enabled jobs only.

        Returns:
            List of matching BackgroundJob records.
        """
        with self._lock:
            all_jobs = list(self._active_jobs.values()) + list(self._completed_jobs)
            if status is not None:
                all_jobs = [j for j in all_jobs if j.status == status]
            if enabled_only:
                all_jobs = [j for j in all_jobs if j.enabled]
            return all_jobs

    def list_ready_jobs(
        self,
        current_time: Optional[datetime] = None,
    ) -> List[BackgroundJob]:
        """Calculates and returns all enabled jobs currently ready for execution.

        Args:
            current_time: Reference timestamp (defaults to UTC now).

        Returns:
            List of ready BackgroundJob instances.
        """
        ref_time = current_time or datetime.now(timezone.utc)
        if not ref_time.tzinfo:
            ref_time = ref_time.replace(tzinfo=timezone.utc)

        ready_jobs: List[BackgroundJob] = []
        with self._lock:
            for job in list(self._active_jobs.values()):
                if not job.enabled or job.is_finished() or job.status == BackgroundJobStatus.PAUSED:
                    continue

                if job.status == BackgroundJobStatus.READY:
                    ready_jobs.append(job)
                    continue

                if job.status == BackgroundJobStatus.SCHEDULED:
                    if job.next_run and ref_time >= job.next_run:
                        job.status = BackgroundJobStatus.READY
                        job.updated_at = ref_time
                        ready_jobs.append(job)
                        self._logger.info("Scheduled Job Ready", extra={"job_id": job.job_id})



        return ready_jobs

    def start_job_execution(self, job_id: str) -> bool:
        """Transitions a READY/SCHEDULED job to RUNNING and sets last_run timestamp.

        Args:
            job_id: Target job ID.

        Returns:
            True if status transitioned, False otherwise.
        """
        if not job_id or not isinstance(job_id, str):
            return False

        with self._lock:
            job = self._active_jobs.get(job_id)
            if not job or job.is_finished() or job.status == BackgroundJobStatus.PAUSED or not job.enabled:
                return False

            now = datetime.now(timezone.utc)
            job.status = BackgroundJobStatus.RUNNING
            job.last_run = now
            job.updated_at = now

            self._logger.info("Scheduled Job Started", extra={"job_id": job_id})
            return True

    def complete_job_execution(
        self,
        job_id: str,
        result_metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Marks execution completed and reschedules recurring jobs or archives one-time jobs.

        Args:
            job_id: Target job ID.
            result_metadata: Optional final metadata to merge into job.

        Returns:
            True if state updated, False if unknown job.
        """
        if not job_id or not isinstance(job_id, str):
            return False

        with self._lock:
            job = self._active_jobs.get(job_id)
            if not job:
                return False

            now = datetime.now(timezone.utc)
            job.updated_at = now
            if result_metadata:
                job.metadata.update(result_metadata)

            self._logger.info("Scheduled Job Completed", extra={"job_id": job_id})

            if job.trigger_type in (BackgroundJobTriggerType.ONCE, BackgroundJobTriggerType.MANUAL):
                job.status = BackgroundJobStatus.COMPLETED
                if self._config.cleanup_history:
                    self._archive_job_locked(job)
                    self._logger.info("One-Time Job Archived", extra={"job_id": job_id})
            else:
                job.next_run = calculate_next_run(job.trigger_type, job.parameters, now)
                job.status = BackgroundJobStatus.SCHEDULED
                self._logger.info("Recurring Job Rescheduled", extra={"job_id": job_id})

            return True

    def fail_job_execution(self, job_id: str, error_message: str) -> bool:
        """Marks execution as failed and updates state and error tracing.

        Args:
            job_id: Target job ID.
            error_message: Failure error trace message.

        Returns:
            True if updated, False if unknown job.
        """
        if not job_id or not isinstance(job_id, str):
            return False

        with self._lock:
            job = self._active_jobs.get(job_id)
            if not job:
                return False

            now = datetime.now(timezone.utc)
            job.metadata["last_error"] = error_message
            job.updated_at = now

            self._logger.info("Scheduled Job Failed", extra={"job_id": job_id, "error": error_message})

            if job.trigger_type in (BackgroundJobTriggerType.ONCE, BackgroundJobTriggerType.MANUAL):
                job.status = BackgroundJobStatus.FAILED
                if self._config.cleanup_history:
                    self._archive_job_locked(job)
            else:
                job.next_run = calculate_next_run(job.trigger_type, job.parameters, now)
                job.status = BackgroundJobStatus.SCHEDULED

            return True

    def archive_job(self, job_id: str) -> bool:
        """Moves an active job to completion history deque.

        Args:
            job_id: Target job ID.

        Returns:
            True if archived, False if job not found in active store.
        """
        if not job_id or not isinstance(job_id, str):
            return False

        with self._lock:
            job = self._active_jobs.get(job_id)
            if not job:
                return False

            self._archive_job_locked(job)
            return True

    def cleanup(self) -> int:
        """Moves all terminal active jobs to completed history deque.

        Returns:
            Number of jobs archived to completion history.
        """
        with self._lock:
            moved_count = 0
            for job_id, job in list(self._active_jobs.items()):
                if job.is_finished():
                    self._archive_job_locked(job)
                    moved_count += 1

            self._logger.info("Scheduler Cleaned", extra={"cleaned_count": moved_count})
            return moved_count

    def clear(self) -> None:
        """Clears all active and completed jobs from memory."""
        with self._lock:
            self._active_jobs.clear()
            self._completed_jobs.clear()

    def _archive_job_locked(self, job: BackgroundJob) -> None:
        """Internal helper to move a job from active map to completed deque under lock."""
        self._active_jobs.pop(job.job_id, None)
        if job not in self._completed_jobs:
            self._completed_jobs.append(job)
            self._logger.info("Job Archived", extra={"job_id": job.job_id})


