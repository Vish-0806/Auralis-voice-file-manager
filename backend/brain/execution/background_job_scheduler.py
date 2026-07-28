import calendar
from collections import deque
from datetime import datetime, timedelta, timezone
from enum import Enum
import logging
import threading
import uuid
from typing import Any, Dict, List, Optional, Tuple, Union
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



class TriggerValidationResult(BaseModel):
    """Outcome of background job trigger parameter validation."""

    is_valid: bool = Field(description="True if trigger configuration is valid")
    error: Optional[str] = Field(default=None, description="Descriptive error message if invalid")
    details: Dict[str, Any] = Field(default_factory=dict, description="Detailed validation breakdown")


class RecurringTriggerValidator:
    """Validates recurring background job trigger parameters and schedules."""

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        """Initializes the RecurringTriggerValidator.

        Args:
            logger: Optional custom logger for diagnostics.
        """
        self._logger = logger or logging.getLogger(__name__)

    def validate_trigger(
        self,
        trigger_type: Union[BackgroundJobTriggerType, str],
        parameters: Optional[Dict[str, Any]] = None,
    ) -> TriggerValidationResult:
        """Validates trigger mechanism and parameter settings.

        Args:
            trigger_type: Trigger type Enum or string representation.
            parameters: Dictionary of trigger parameters.

        Returns:
            TriggerValidationResult indicating validation outcome and details.
        """
        params = parameters or {}
        t_str = trigger_type.value if hasattr(trigger_type, "value") else str(trigger_type).upper()

        try:
            tt = BackgroundJobTriggerType(t_str)
        except Exception:
            err = f"Unknown trigger type: '{trigger_type}'"
            self._logger.warning("Trigger Validation Failed", extra={"trigger_type": str(trigger_type), "error": err})
            self._logger.warning("Invalid Schedule", extra={"trigger_type": str(trigger_type), "error": err})
            return TriggerValidationResult(is_valid=False, error=err, details={"trigger_type": str(trigger_type)})

        if tt == BackgroundJobTriggerType.MANUAL:
            self._logger.info("Trigger Validated", extra={"trigger_type": tt.value})
            return TriggerValidationResult(is_valid=True, details={"trigger_type": tt.value})

        if tt == BackgroundJobTriggerType.ONCE:
            res = self._validate_once(params)
        elif tt == BackgroundJobTriggerType.INTERVAL:
            res = self._validate_interval(params)
        elif tt == BackgroundJobTriggerType.DAILY:
            res = self._validate_daily(params)
        elif tt == BackgroundJobTriggerType.WEEKLY:
            res = self._validate_weekly(params)
        elif tt == BackgroundJobTriggerType.MONTHLY:
            res = self._validate_monthly(params)
        else:
            res = TriggerValidationResult(is_valid=False, error=f"Unsupported trigger type '{tt.value}'")

        if res.is_valid:
            self._logger.info("Trigger Validated", extra={"trigger_type": tt.value})
        else:
            self._logger.warning("Trigger Validation Failed", extra={"trigger_type": tt.value, "error": res.error})
            self._logger.warning("Invalid Schedule", extra={"trigger_type": tt.value, "error": res.error})

        return res

    def _validate_once(self, params: Dict[str, Any]) -> TriggerValidationResult:
        if "delay_seconds" in params:
            try:
                float(params["delay_seconds"])
            except (ValueError, TypeError):
                return TriggerValidationResult(is_valid=False, error="delay_seconds must be a numeric value")


        if "run_at" in params:
            run_at = params["run_at"]
            if not isinstance(run_at, datetime):
                if isinstance(run_at, str):
                    try:
                        datetime.fromisoformat(run_at)
                    except Exception:
                        return TriggerValidationResult(is_valid=False, error="run_at string must be ISO format")
                else:
                    return TriggerValidationResult(is_valid=False, error="run_at must be datetime or ISO string")

        return TriggerValidationResult(is_valid=True, details={"trigger": "ONCE"})

    def _validate_interval(self, params: Dict[str, Any]) -> TriggerValidationResult:
        if "interval_seconds" not in params:
            return TriggerValidationResult(is_valid=False, error="Missing required parameter 'interval_seconds'")

        try:
            val = float(params["interval_seconds"])
            if val <= 0:
                return TriggerValidationResult(is_valid=False, error="interval_seconds must be greater than zero")
        except (ValueError, TypeError):
            return TriggerValidationResult(is_valid=False, error="interval_seconds must be a numeric value")

        for conflict_key in ("day_of_week", "day_of_month"):
            if conflict_key in params:
                return TriggerValidationResult(is_valid=False, error=f"Conflicting parameter '{conflict_key}' for INTERVAL trigger")

        return TriggerValidationResult(is_valid=True, details={"trigger": "INTERVAL", "interval_seconds": val})



    def _validate_daily(self, params: Dict[str, Any]) -> TriggerValidationResult:
        time_str = params.get("time_of_day", "00:00")
        time_err = self._validate_time_of_day(time_str)
        if time_err:
            return TriggerValidationResult(is_valid=False, error=time_err)

        for conflict_key in ("interval_seconds", "day_of_week", "day_of_month"):
            if conflict_key in params:
                return TriggerValidationResult(is_valid=False, error=f"Conflicting parameter '{conflict_key}' for DAILY trigger")

        return TriggerValidationResult(is_valid=True, details={"trigger": "DAILY", "time_of_day": str(time_str)})

    def _validate_weekly(self, params: Dict[str, Any]) -> TriggerValidationResult:
        if "day_of_week" not in params:
            return TriggerValidationResult(is_valid=False, error="Missing required parameter 'day_of_week'")

        dow = params["day_of_week"]
        if isinstance(dow, str):
            day_map = {
                "monday": 0, "mon": 0,
                "tuesday": 1, "tue": 1,
                "wednesday": 2, "wed": 2,
                "thursday": 3, "thu": 3,
                "friday": 4, "fri": 4,
                "saturday": 5, "sat": 5,
                "sunday": 6, "sun": 6,
            }
            if dow.lower() not in day_map:
                return TriggerValidationResult(is_valid=False, error=f"Invalid day_of_week string '{dow}'")
        else:
            try:
                val = int(dow)
                if val < 0 or val > 6:
                    return TriggerValidationResult(is_valid=False, error="day_of_week must be between 0 and 6")
            except (ValueError, TypeError):
                return TriggerValidationResult(is_valid=False, error="day_of_week must be an integer (0-6) or weekday name")

        time_str = params.get("time_of_day", "00:00")
        time_err = self._validate_time_of_day(time_str)
        if time_err:
            return TriggerValidationResult(is_valid=False, error=time_err)

        for conflict_key in ("interval_seconds", "day_of_month"):
            if conflict_key in params:
                return TriggerValidationResult(is_valid=False, error=f"Conflicting parameter '{conflict_key}' for WEEKLY trigger")

        return TriggerValidationResult(is_valid=True, details={"trigger": "WEEKLY", "day_of_week": dow})

    def _validate_monthly(self, params: Dict[str, Any]) -> TriggerValidationResult:
        if "day_of_month" not in params:
            return TriggerValidationResult(is_valid=False, error="Missing required parameter 'day_of_month'")

        dom = params["day_of_month"]
        try:
            val = int(dom)
            if val < 1 or val > 31:
                return TriggerValidationResult(is_valid=False, error="day_of_month must be between 1 and 31")
        except (ValueError, TypeError):
            return TriggerValidationResult(is_valid=False, error="day_of_month must be an integer between 1 and 31")

        time_str = params.get("time_of_day", "00:00")
        time_err = self._validate_time_of_day(time_str)
        if time_err:
            return TriggerValidationResult(is_valid=False, error=time_err)

        for conflict_key in ("interval_seconds", "day_of_week"):
            if conflict_key in params:
                return TriggerValidationResult(is_valid=False, error=f"Conflicting parameter '{conflict_key}' for MONTHLY trigger")

        return TriggerValidationResult(is_valid=True, details={"trigger": "MONTHLY", "day_of_month": dom})

    def _validate_time_of_day(self, time_str: Any) -> Optional[str]:
        if not isinstance(time_str, str):
            return "time_of_day must be a string formatted as HH:MM"
        parts = time_str.split(":")
        if len(parts) != 2:
            return f"Invalid time_of_day format '{time_str}', expected HH:MM"
        try:
            h, m = int(parts[0]), int(parts[1])
            if h < 0 or h > 23:
                return f"Hour out of range (0-23): {h}"
            if m < 0 or m > 59:
                return f"Minute out of range (0-59): {m}"
        except ValueError:
            return f"Non-numeric time_of_day values in '{time_str}'"
        return None


class RecurringScheduleCalculator:
    """Calculates deterministic next_run timestamps for background job schedules."""

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        """Initializes the RecurringScheduleCalculator.

        Args:
            logger: Optional custom logger for diagnostics.
        """
        self._logger = logger or logging.getLogger(__name__)

    def calculate_next_run(
        self,
        trigger_type: Union[BackgroundJobTriggerType, str],
        parameters: Optional[Dict[str, Any]] = None,
        from_time: Optional[datetime] = None,
        last_run: Optional[datetime] = None,
    ) -> Optional[datetime]:
        """Calculates the deterministic next run datetime in UTC.

        Args:
            trigger_type: Trigger type Enum or string.
            parameters: Trigger parameters dictionary.
            from_time: Reference start timestamp (defaults to UTC now).
            last_run: Optional last execution timestamp.

        Returns:
            Calculated next run datetime in UTC, or None if MANUAL or finished.
        """
        params = parameters or {}
        ref_time = from_time or datetime.now(timezone.utc)
        if not ref_time.tzinfo:
            ref_time = ref_time.replace(tzinfo=timezone.utc)

        t_str = trigger_type.value if hasattr(trigger_type, "value") else str(trigger_type).upper()
        try:
            tt = BackgroundJobTriggerType(t_str)
        except Exception:
            return None

        if tt == BackgroundJobTriggerType.MANUAL:
            return None

        next_run: Optional[datetime] = None

        if tt == BackgroundJobTriggerType.ONCE:
            next_run = self._calculate_once(params, ref_time, last_run)
        elif tt == BackgroundJobTriggerType.INTERVAL:
            next_run = self._calculate_interval(params, ref_time, last_run)
        elif tt == BackgroundJobTriggerType.DAILY:
            next_run = self._calculate_daily(params, ref_time)
        elif tt == BackgroundJobTriggerType.WEEKLY:
            next_run = self._calculate_weekly(params, ref_time)
        elif tt == BackgroundJobTriggerType.MONTHLY:
            next_run = self._calculate_monthly(params, ref_time)

        if next_run:
            self._logger.info("Recurring Job Calculated", extra={"trigger_type": tt.value})
            self._logger.info("Next Run Calculated", extra={"trigger_type": tt.value, "next_run": next_run.isoformat()})

        return next_run

    def _calculate_once(
        self,
        params: Dict[str, Any],
        ref_time: datetime,
        last_run: Optional[datetime] = None,
    ) -> Optional[datetime]:
        if last_run is not None:
            return None

        run_at = params.get("run_at")
        if isinstance(run_at, datetime):
            return run_at if run_at.tzinfo else run_at.replace(tzinfo=timezone.utc)
        if isinstance(run_at, str):
            try:
                dt = datetime.fromisoformat(run_at)
                return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
            except Exception:
                pass

        delay_seconds = float(params.get("delay_seconds", 0))
        return ref_time + timedelta(seconds=max(0.0, delay_seconds))

    def _calculate_interval(
        self,
        params: Dict[str, Any],
        ref_time: datetime,
        last_run: Optional[datetime] = None,
    ) -> Optional[datetime]:
        try:
            interval = float(params.get("interval_seconds", 60))
            if interval <= 0:
                interval = 60.0
        except (ValueError, TypeError):
            interval = 60.0

        base_time = last_run or ref_time
        if not base_time.tzinfo:
            base_time = base_time.replace(tzinfo=timezone.utc)

        target = base_time + timedelta(seconds=interval)
        while target <= ref_time:
            target += timedelta(seconds=interval)
        return target

    def _calculate_daily(self, params: Dict[str, Any], ref_time: datetime) -> Optional[datetime]:
        h, m = self._parse_time_of_day(params.get("time_of_day", "00:00"))
        target = ref_time.replace(hour=h, minute=m, second=0, microsecond=0)
        if target <= ref_time:
            target += timedelta(days=1)
        return target

    def _calculate_weekly(self, params: Dict[str, Any], ref_time: datetime) -> Optional[datetime]:
        dow = self._parse_day_of_week(params.get("day_of_week", 0))
        h, m = self._parse_time_of_day(params.get("time_of_day", "00:00"))

        days_ahead = (dow - ref_time.weekday()) % 7
        target = ref_time.replace(hour=h, minute=m, second=0, microsecond=0) + timedelta(days=days_ahead)
        if target <= ref_time:
            target += timedelta(days=7)
        return target

    def _calculate_monthly(self, params: Dict[str, Any], ref_time: datetime) -> Optional[datetime]:
        dom = self._parse_day_of_month(params.get("day_of_month", 1))
        h, m = self._parse_time_of_day(params.get("time_of_day", "00:00"))

        _, max_days_curr = calendar.monthrange(ref_time.year, ref_time.month)
        target_day_curr = min(dom, max_days_curr)
        target = ref_time.replace(day=target_day_curr, hour=h, minute=m, second=0, microsecond=0)

        if target <= ref_time:
            next_month = ref_time.month + 1
            next_year = ref_time.year
            if next_month > 12:
                next_month = 1
                next_year += 1
            _, max_days_next = calendar.monthrange(next_year, next_month)
            target_day_next = min(dom, max_days_next)
            target = datetime(next_year, next_month, target_day_next, h, m, 0, 0, tzinfo=timezone.utc)

        return target

    def _parse_time_of_day(self, val: Any) -> Tuple[int, int]:
        if isinstance(val, str) and ":" in val:
            try:
                parts = val.split(":")
                return int(parts[0]) % 24, int(parts[1]) % 60
            except Exception:
                pass
        return 0, 0

    def _parse_day_of_week(self, val: Any) -> int:
        if isinstance(val, str):
            day_map = {
                "monday": 0, "mon": 0,
                "tuesday": 1, "tue": 1,
                "wednesday": 2, "wed": 2,
                "thursday": 3, "thu": 3,
                "friday": 4, "fri": 4,
                "saturday": 5, "sat": 5,
                "sunday": 6, "sun": 6,
            }
            return day_map.get(val.lower(), 0)
        try:
            return int(val) % 7
        except Exception:
            return 0

    def _parse_day_of_month(self, val: Any) -> int:
        try:
            return max(1, min(31, int(val)))
        except Exception:
            return 1


def calculate_next_run(
    trigger_type: Union[BackgroundJobTriggerType, str],
    parameters: Optional[Dict[str, Any]] = None,
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
    calculator = RecurringScheduleCalculator()
    return calculator.calculate_next_run(trigger_type, parameters, from_time=from_time)



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
        self._validator = RecurringTriggerValidator(logger=self._logger)
        self._calculator = RecurringScheduleCalculator(logger=self._logger)

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

        params = dict(parameters or {})
        t_str = trigger_type.value if hasattr(trigger_type, "value") else str(trigger_type).upper()
        if t_str == "INTERVAL":
            params.setdefault("interval_seconds", self._config.default_check_interval)

        val_result = self._validator.validate_trigger(trigger_type, params)
        if not val_result.is_valid:
            return None


        with self._lock:
            if len(self._active_jobs) >= self._config.maximum_jobs:
                self.cleanup()
                if len(self._active_jobs) >= self._config.maximum_jobs:
                    return None

            jid = job_id or f"job_{uuid.uuid4().hex[:12]}"
            now = datetime.now(timezone.utc)
            next_run = self._calculator.calculate_next_run(trigger_type, params, from_time=now)

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

            new_tt = trigger_type if trigger_type is not None else job.trigger_type
            new_params = parameters if parameters is not None else job.parameters

            if trigger_type is not None or parameters is not None:
                val_result = self._validator.validate_trigger(new_tt, new_params)
                if not val_result.is_valid:
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
                job.next_run = self._calculator.calculate_next_run(job.trigger_type, job.parameters, from_time=now)

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
                job.next_run = self._calculator.calculate_next_run(job.trigger_type, job.parameters, from_time=now, last_run=now)
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
                job.next_run = self._calculator.calculate_next_run(job.trigger_type, job.parameters, from_time=now, last_run=now)
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


