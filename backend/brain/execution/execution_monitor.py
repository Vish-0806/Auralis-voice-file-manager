"""Execution Monitoring & History tracking for Auralis."""

from __future__ import annotations

from datetime import datetime, timezone
import logging
import threading
from typing import Any, Dict, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field

from brain.execution.execution_state import (
    ExecutionStatus,
    ExecutionProgress,
    ExecutionState,
)

logger = logging.getLogger(__name__)


class ExecutionMetrics(BaseModel):
    """Runtime execution metrics computed at completion/termination."""

    execution_id: str = Field(description="Unique execution session identifier")
    total_steps: int = Field(description="Total steps in the execution plan")
    completed_steps: int = Field(description="Number of steps successfully executed")
    failed_steps: int = Field(description="Number of steps that failed")
    retry_count: int = Field(description="Total number of retry attempts made")
    duration_seconds: float = Field(description="Total execution duration in seconds")
    average_step_duration: float = Field(description="Average duration per step in seconds")
    start_time: Optional[datetime] = Field(None, description="Start timestamp")
    end_time: Optional[datetime] = Field(None, description="Completion/termination timestamp")
    success: bool = Field(description="Whether the execution was successful")


class ExecutionSummary(BaseModel):
    """Historical execution summary record."""

    execution_id: str = Field(description="Unique execution session identifier")
    workflow_id: Optional[str] = Field(None, description="Workflow ID if executing a workflow")
    user_id: int = Field(description="User ID associated with this execution")
    status: ExecutionStatus = Field(description="Terminal status of the execution")
    duration_seconds: float = Field(description="Duration in seconds")
    steps_executed: int = Field(description="Total number of steps processed")
    steps_failed: int = Field(description="Number of steps that failed")
    retry_count: int = Field(description="Number of retries attempted")
    completion_percentage: float = Field(description="Final completion percentage achieved")
    started_at: Optional[datetime] = Field(None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion/termination timestamp")
    
    # Recovery additions
    recovery_attempts: int = Field(default=0, description="Total count of active recovery attempts")
    successful_recoveries: int = Field(default=0, description="Total successful recovery count")
    failed_recoveries: int = Field(default=0, description="Total failed recovery count")
    fallback_usage: int = Field(default=0, description="Total fallback resource usages count")
    skipped_steps: int = Field(default=0, description="Total skipped steps count")


class ExecutionStatistics(BaseModel):
    """Aggregated statistics across all logged historical runs."""

    total_executions: int = Field(description="Total executions recorded (active + terminal)")
    running: int = Field(description="Count of currently running executions")
    completed: int = Field(description="Count of successfully completed executions")
    failed: int = Field(description="Count of failed executions")
    cancelled: int = Field(description="Count of cancelled executions")
    average_duration: float = Field(description="Average duration of terminal executions in seconds")
    success_rate: float = Field(description="Percentage of completed executions (0.0 to 1.0)")
    retry_rate: float = Field(description="Percentage of executions with retries (0.0 to 1.0)")
    
    # Recovery additions
    recovery_attempts: int = Field(default=0, description="Total recovery attempts count")
    successful_recoveries: int = Field(default=0, description="Total successful recovery count")
    failed_recoveries: int = Field(default=0, description="Total failed recovery count")
    fallback_usage: int = Field(default=0, description="Total fallback resource usages count")
    skipped_steps: int = Field(default=0, description="Total skipped steps count")
    retry_counts: int = Field(default=0, description="Total count of all retries made")

    # Long-running task additions
    long_running_task_count: int = Field(default=0, description="Total count of long-running tasks recorded")
    long_running_average_duration: float = Field(default=0.0, description="Average completion time of long-running tasks in seconds")
    long_running_failed_count: int = Field(default=0, description="Count of failed long-running tasks")
    long_running_cancelled_count: int = Field(default=0, description="Count of cancelled long-running tasks")
    long_running_completion_percentage: float = Field(default=0.0, description="Average completion percentage of long-running tasks")


class ExecutionMonitor:
    """Monitors execution lifecycles, aggregates metrics, and tracks historical summaries."""

    def __init__(self, max_history_size: int = 1000, state_manager: Optional[Any] = None, task_manager: Optional[Any] = None) -> None:
        """Initializes the ExecutionMonitor.

        Args:
            max_history_size: Maximum size of the history list (FIFO eviction).
            state_manager: Optional ExecutionStateManager instance.
            task_manager: Optional LongRunningTaskManager instance.
        """
        self._max_history_size = max_history_size
        self._state_manager = state_manager
        self._task_manager = task_manager
        self._lock = threading.RLock()
        self._completed_history: List[ExecutionSummary] = []
        self._event_counts: Dict[str, int] = {}
        self._total_events_received: int = 0
        self._event_completion_count: int = 0
        self._event_failure_count: int = 0
        self._event_timeout_count: int = 0
        self._task_latest_progress: Dict[str, float] = {}

        if self._task_manager and hasattr(self._task_manager, "event_dispatcher"):
            try:
                self._task_manager.event_dispatcher.register_listener(self)
            except Exception:
                pass

    def on_event(self, event: Any) -> None:
        """TaskEventListener callback receiving dispatched TaskEvent instances.

        Args:
            event: Dispatched TaskEvent payload.
        """
        if not event:
            return

        with self._lock:
            type_val = getattr(event, "event_type", "")
            type_str = type_val.value if hasattr(type_val, "value") else str(type_val)

            self._event_counts[type_str] = self._event_counts.get(type_str, 0) + 1
            self._total_events_received += 1

            if "COMPLETED" in type_str:
                self._event_completion_count += 1
            elif "FAILED" in type_str:
                self._event_failure_count += 1
            elif "TIMED_OUT" in type_str:
                self._event_timeout_count += 1

            progress = float(getattr(event, "progress", 0.0))
            task_id = str(getattr(event, "task_id", ""))
            if task_id:
                self._task_latest_progress[task_id] = progress

    def get_event_statistics(self) -> Dict[str, Any]:
        """Returns aggregated event statistics collected by ExecutionMonitor listener.

        Returns:
            Dictionary containing event counts, rates, and progress metrics.
        """
        with self._lock:
            total = self._total_events_received
            comp = self._event_completion_count
            fail = self._event_failure_count
            tout = self._event_timeout_count
            rate = (comp / total) if total > 0 else 0.0
            avg_prog = (sum(self._task_latest_progress.values()) / len(self._task_latest_progress)) if self._task_latest_progress else 0.0

            return {
                "total_events": total,
                "completion_events": comp,
                "failure_events": fail,
                "timeout_events": tout,
                "event_completion_rate": rate,
                "average_task_progress": avg_prog,
                "event_counts_by_type": dict(self._event_counts),
            }



    def calculate_metrics(self, state: ExecutionState) -> ExecutionMetrics:
        """Computes runtime performance metrics for an ExecutionState.

        Args:
            state: The ExecutionState to analyze.

        Returns:
            The computed ExecutionMetrics.
        """
        total_steps = len(state.completed_steps) + len(state.failed_steps) + len(state.pending_steps)
        completed_steps = len(state.completed_steps)
        failed_steps = len(state.failed_steps)

        duration = 0.0
        if state.progress.started_at and state.progress.completed_at:
            duration = (state.progress.completed_at - state.progress.started_at).total_seconds()

        avg_step_duration = 0.0
        if completed_steps > 0:
            avg_step_duration = duration / completed_steps

        return ExecutionMetrics(
            execution_id=state.execution_id,
            total_steps=total_steps,
            completed_steps=completed_steps,
            failed_steps=failed_steps,
            retry_count=state.retry_count,
            duration_seconds=duration,
            average_step_duration=avg_step_duration,
            start_time=state.progress.started_at,
            end_time=state.progress.completed_at,
            success=(state.status == ExecutionStatus.COMPLETED),
        )

    def record_completion(self, state: ExecutionState) -> None:
        """Records a successful execution completion summary to history.

        Args:
            state: The ExecutionState to summarize.
        """
        self._add_to_history(state)
        logger.info("Execution Summary Recorded", extra={"execution_id": state.execution_id, "status": "COMPLETED"})
        logger.info("Execution Metrics Updated", extra={"execution_id": state.execution_id})

    def record_failure(self, state: ExecutionState) -> None:
        """Records a failed execution summary to history.

        Args:
            state: The ExecutionState to summarize.
        """
        self._add_to_history(state)
        logger.info("Execution Summary Recorded", extra={"execution_id": state.execution_id, "status": "FAILED"})
        logger.info("Execution Metrics Updated", extra={"execution_id": state.execution_id})

    def record_cancellation(self, state: ExecutionState) -> None:
        """Records a cancelled execution summary to history.

        Args:
            state: The ExecutionState to summarize.
        """
        self._add_to_history(state)
        logger.info("Execution Summary Recorded", extra={"execution_id": state.execution_id, "status": "CANCELLED"})
        logger.info("Execution Metrics Updated", extra={"execution_id": state.execution_id})

    def get_summary(self, execution_id: str) -> Optional[ExecutionSummary]:
        """Retrieves the summary for a given execution ID from history.

        Args:
            execution_id: Unique identifier for the execution.

        Returns:
            The ExecutionSummary or None if not found in history.
        """
        with self._lock:
            for summary in self._completed_history:
                if summary.execution_id == execution_id:
                    return summary
            return None

    def list_history(self, limit: Optional[int] = None) -> List[ExecutionSummary]:
        """Lists historical execution summaries in chronological order (oldest first).

        Args:
            limit: Optional maximum number of summaries to return.

        Returns:
            A list of ExecutionSummary records.
        """
        with self._lock:
            if limit is not None:
                return self._completed_history[-limit:]
            return list(self._completed_history)

    def get_statistics(
        self,
        state_manager: Optional[Any] = None,
        task_manager: Optional[Any] = None,
    ) -> ExecutionStatistics:
        """Calculates runtime statistics across active and finished executions.

        Args:
            state_manager: Optional state manager instance to fetch active/running count.
            task_manager: Optional task manager instance to fetch long-running task metrics.

        Returns:
            The compiled ExecutionStatistics.
        """
        with self._lock:
            mgr = state_manager or self._state_manager
            tm = task_manager or self._task_manager
            running_count = 0
            total_recovery_attempts = sum(s.recovery_attempts for s in self._completed_history)
            total_successful_recoveries = sum(s.successful_recoveries for s in self._completed_history)
            total_failed_recoveries = sum(s.failed_recoveries for s in self._completed_history)
            total_fallback_usage = sum(s.fallback_usage for s in self._completed_history)
            total_skipped_steps = sum(s.skipped_steps for s in self._completed_history)
            total_retry_counts = sum(s.retry_count for s in self._completed_history)

            long_running_count = 0
            long_running_avg_dur = 0.0
            long_running_failed = 0
            long_running_cancelled = 0
            long_running_comp_pct = 0.0

            if tm is not None:
                try:
                    tasks = tm.list_tasks()
                    long_running_count = len(tasks)
                    long_running_failed = sum(
                        1 for t in tasks
                        if str(t.status) == "FAILED" or getattr(t.status, "value", None) == "FAILED"
                    )
                    long_running_cancelled = sum(
                        1 for t in tasks
                        if str(t.status) == "CANCELLED" or getattr(t.status, "value", None) == "CANCELLED"
                    )

                    durations = []
                    for t in tasks:
                        if t.started_at and t.completed_at:
                            durations.append((t.completed_at - t.started_at).total_seconds())
                    if durations:
                        long_running_avg_dur = sum(durations) / len(durations)

                    if tasks:
                        long_running_comp_pct = sum(t.progress for t in tasks) / len(tasks)
                except Exception:
                    pass

            if mgr is not None:
                try:
                    active_list = mgr.list_active()
                    running_count = sum(1 for s in active_list if s.status == ExecutionStatus.RUNNING)
                    total_recovery_attempts += sum(s.recovery_attempts for s in active_list)
                    total_skipped_steps += sum(len(s.skipped_steps) for s in active_list)
                    total_retry_counts += sum(s.retry_count for s in active_list)
                    total_successful_recoveries += sum(s.metadata.get("successful_recoveries", 0) for s in active_list)
                    total_failed_recoveries += sum(s.metadata.get("failed_recoveries", 0) for s in active_list)
                    total_fallback_usage += sum(s.metadata.get("fallback_usage", 0) for s in active_list)
                except Exception:
                    pass

            total_completed = sum(1 for s in self._completed_history if s.status == ExecutionStatus.COMPLETED)
            total_failed = sum(1 for s in self._completed_history if s.status == ExecutionStatus.FAILED)
            total_cancelled = sum(1 for s in self._completed_history if s.status == ExecutionStatus.CANCELLED)

            total_terminal = len(self._completed_history)
            total_all = total_terminal + running_count

            avg_duration = 0.0
            if total_terminal > 0:
                avg_duration = sum(s.duration_seconds for s in self._completed_history) / total_terminal

            success_rate = 0.0
            if total_terminal > 0:
                success_rate = total_completed / total_terminal

            retry_rate = 0.0
            if total_terminal > 0:
                retry_rate = sum(1 for s in self._completed_history if s.retry_count > 0) / total_terminal

            logger.info("Execution Statistics Generated")

            return ExecutionStatistics(
                total_executions=total_all,
                running=running_count,
                completed=total_completed,
                failed=total_failed,
                cancelled=total_cancelled,
                average_duration=avg_duration,
                success_rate=success_rate,
                retry_rate=retry_rate,
                recovery_attempts=total_recovery_attempts,
                successful_recoveries=total_successful_recoveries,
                failed_recoveries=total_failed_recoveries,
                fallback_usage=total_fallback_usage,
                skipped_steps=total_skipped_steps,
                retry_counts=total_retry_counts,
                long_running_task_count=long_running_count,
                long_running_average_duration=long_running_avg_dur,
                long_running_failed_count=long_running_failed,
                long_running_cancelled_count=long_running_cancelled,
                long_running_completion_percentage=long_running_comp_pct,
            )


    def clear_history(self) -> None:
        """Clears all historical summaries from memory."""
        with self._lock:
            self._completed_history.clear()

    def _add_to_history(self, state: ExecutionState) -> None:
        """Helper to build and append an ExecutionSummary to history thread-safely."""
        with self._lock:
            duration = 0.0
            if state.progress.started_at and state.progress.completed_at:
                duration = (state.progress.completed_at - state.progress.started_at).total_seconds()

            summary = ExecutionSummary(
                execution_id=state.execution_id,
                workflow_id=state.workflow_id,
                user_id=state.user_id,
                status=state.status,
                duration_seconds=duration,
                steps_executed=len(state.completed_steps) + len(state.failed_steps),
                steps_failed=len(state.failed_steps),
                retry_count=state.retry_count,
                completion_percentage=state.progress.percentage,
                started_at=state.progress.started_at,
                completed_at=state.progress.completed_at,
                recovery_attempts=state.recovery_attempts,
                successful_recoveries=state.metadata.get("successful_recoveries", 0),
                failed_recoveries=state.metadata.get("failed_recoveries", 0),
                fallback_usage=state.metadata.get("fallback_usage", 0),
                skipped_steps=len(state.skipped_steps),
            )

            self._completed_history.append(summary)

            # Evict oldest if limit exceeded (FIFO)
            if len(self._completed_history) > self._max_history_size:
                self._completed_history.pop(0)
