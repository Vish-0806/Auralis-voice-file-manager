"""Task Monitor for the Auralis Task Management Runtime (Phase 12.5).

Tracks task execution progress metrics, completion percentages, running durations, and estimated remaining time.
"""

from datetime import datetime, timezone
import threading
import time
from typing import Dict, Optional

from brain.execution.task.interfaces import ITaskMonitor
from brain.execution.task.task_models import TaskProgress


class TaskMonitor(ITaskMonitor):
    """Thread-safe task progress tracker calculating metrics and remaining duration estimates."""

    def __init__(self) -> None:
        """Initializes TaskMonitor with thread-safe progress store."""
        self._lock = threading.RLock()
        self._progress_map: Dict[str, TaskProgress] = {}
        self._start_times: Dict[str, float] = {}

    def start_monitoring(self, task_id: str, total_steps: int = 1) -> TaskProgress:
        """Initialize progress tracking for a new task.

        Args:
            task_id: Task identifier.
            total_steps: Total number of steps in task.

        Returns:
            Initial TaskProgress object.
        """
        with self._lock:
            self._start_times[task_id] = time.perf_counter()
            prog = TaskProgress(
                task_id=task_id,
                progress_percentage=0.0,
                completed_steps=0,
                total_steps=max(1, total_steps),
                running_duration_seconds=0.0,
                estimated_remaining_seconds=0.0,
                status_message="Started monitoring",
                updated_at=datetime.now(timezone.utc),
            )
            self._progress_map[task_id] = prog
            return prog

    def update_progress(
        self,
        task_id: str,
        completed_steps: int,
        total_steps: int,
        status_message: str = "",
    ) -> TaskProgress:
        """Update progress metrics for an active task.

        Args:
            task_id: Task identifier.
            completed_steps: Count of completed steps.
            total_steps: Total expected steps.
            status_message: Descriptive status update string.

        Returns:
            Updated TaskProgress object.
        """
        with self._lock:
            start_t = self._start_times.get(task_id, time.perf_counter())
            running_sec = time.perf_counter() - start_t

            tot_steps = max(1, total_steps)
            comp_steps = min(tot_steps, max(0, completed_steps))
            percentage = round((comp_steps / tot_steps) * 100.0, 2)

            est_remaining = 0.0
            if comp_steps > 0 and comp_steps < tot_steps:
                avg_time_per_step = running_sec / comp_steps
                est_remaining = round(avg_time_per_step * (tot_steps - comp_steps), 2)

            prog = TaskProgress(
                task_id=task_id,
                progress_percentage=percentage,
                completed_steps=comp_steps,
                total_steps=tot_steps,
                running_duration_seconds=round(running_sec, 2),
                estimated_remaining_seconds=est_remaining,
                status_message=status_message or f"Completed {comp_steps}/{tot_steps} steps",
                updated_at=datetime.now(timezone.utc),
            )
            self._progress_map[task_id] = prog
            return prog

    def get_progress(self, task_id: str) -> Optional[TaskProgress]:
        """Fetch current TaskProgress for task_id.

        Args:
            task_id: Task identifier.

        Returns:
            TaskProgress or None if not monitored.
        """
        with self._lock:
            return self._progress_map.get(task_id)

    def stop_monitoring(self, task_id: str) -> None:
        """Stop tracking task progress.

        Args:
            task_id: Task identifier.
        """
        with self._lock:
            self._progress_map.pop(task_id, None)
            self._start_times.pop(task_id, None)
