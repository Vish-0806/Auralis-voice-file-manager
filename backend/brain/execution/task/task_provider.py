"""Task Provider for the Auralis Task Management Runtime (Phase 12.5).

Aggregates Scheduler, Executor, Monitor, and Persistence into a unified, thread-safe provider.
Supports task submission, priority queuing, pause/resume, cancellation, health monitoring, and statistics.
"""

from datetime import datetime, timezone
import logging
import threading
import time
from typing import Any, Dict, List, Optional

from brain.execution.task.interfaces import (
    ITaskExecutor,
    ITaskMonitor,
    ITaskPersistence,
    ITaskProvider,
    ITaskScheduler,
)
from brain.execution.task.task_executor import TaskExecutor
from brain.execution.task.task_models import (
    TaskHealth,
    TaskProgress,
    TaskRequest,
    TaskResult,
    TaskStatistics,
    TaskStatus,
)
from brain.execution.task.task_monitor import TaskMonitor
from brain.execution.task.task_persistence import TaskPersistence
from brain.execution.task.task_scheduler import TaskScheduler

logger = logging.getLogger(__name__)


class TaskProvider(ITaskProvider):
    """Thread-safe provider aggregating task scheduler, executor, monitor, and persistence."""

    def __init__(
        self,
        scheduler: Optional[ITaskScheduler] = None,
        executor: Optional[ITaskExecutor] = None,
        monitor: Optional[ITaskMonitor] = None,
        persistence: Optional[ITaskPersistence] = None,
    ) -> None:
        """Initializes TaskProvider with injected or default components."""
        self._lock = threading.RLock()
        self._scheduler = scheduler or TaskScheduler()
        self._monitor = monitor or TaskMonitor()
        self._persistence = persistence or TaskPersistence()
        self._executor = executor or TaskExecutor(
            monitor=self._monitor if isinstance(self._monitor, TaskMonitor) else None,
            persistence=self._persistence if isinstance(self._persistence, TaskPersistence) else None,
        )

        self._total_tasks = 0
        self._completed_count = 0
        self._failed_count = 0
        self._cancelled_count = 0
        self._paused_count = 0
        self._total_duration_seconds = 0.0

    def submit_task(
        self,
        request_or_payload: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> TaskResult:
        """Submit background task for processing.

        Args:
            request_or_payload: TaskRequest, payload object, or dict.
            context: Optional contextual parameters.

        Returns:
            TaskResult model.
        """
        start_time = time.perf_counter()
        with self._lock:
            self._total_tasks += 1

        if isinstance(request_or_payload, TaskRequest):
            task_req = request_or_payload
        elif isinstance(request_or_payload, dict):
            task_req = TaskRequest(
                name=request_or_payload.get("name", "Untitled Task"),
                payload=request_or_payload.get("payload", ""),
                context=context or request_or_payload.get("context", {}),
            )
        else:
            task_req = TaskRequest(
                name="Dynamic Task",
                payload=request_or_payload,
                context=context or {},
            )

        # Enqueue in scheduler
        self._scheduler.enqueue(task_req)

        # Dequeue highest priority ready task
        execution = self._scheduler.dequeue()
        if not execution:
            execution_req = task_req
        else:
            execution_req = task_req

        result = self._executor.execute_task(execution_req, context=context)
        elapsed_sec = time.perf_counter() - start_time

        with self._lock:
            if result.status == TaskStatus.COMPLETED:
                self._completed_count += 1
            elif result.status == TaskStatus.CANCELLED:
                self._cancelled_count += 1
            elif result.status == TaskStatus.PAUSED:
                self._paused_count += 1
            else:
                self._failed_count += 1

            self._total_duration_seconds += elapsed_sec

        return result

    def pause_task(self, task_id: str) -> bool:
        """Pause running task by task_id."""
        with self._lock:
            self._paused_count += 1
        return self._executor.pause_task(task_id)

    def resume_task(self, task_id: str) -> bool:
        """Resume paused task by task_id."""
        return self._executor.resume_task(task_id)

    def cancel_task(self, task_id: str) -> bool:
        """Cancel background task by task_id."""
        return self._executor.cancel_task(task_id)

    def get_task_progress(self, task_id: str) -> Optional[TaskProgress]:
        """Fetch current task progress for task_id."""
        return self._monitor.get_progress(task_id)

    def health_check(self) -> TaskHealth:
        """Report overall component health statuses."""
        with self._lock:
            registered = {
                "TaskScheduler": self._scheduler is not None,
                "TaskExecutor": self._executor is not None,
                "TaskMonitor": self._monitor is not None,
                "TaskPersistence": self._persistence is not None,
            }
            all_ok = all(registered.values())

            return TaskHealth(
                status="READY" if all_ok else "ERROR",
                healthy=all_ok,
                components=registered,
                statistics=self.get_statistics().model_dump(),
                detected_issues=[] if all_ok else ["One or more task sub-components are unavailable"],
                metadata={"thread_safety": "PROTECTED"},
            )

    def get_statistics(self) -> TaskStatistics:
        """Return snapshot of aggregate task execution statistics."""
        with self._lock:
            avg_duration = (self._total_duration_seconds / self._total_tasks) if self._total_tasks > 0 else 0.0
            return TaskStatistics(
                total_tasks=self._total_tasks,
                completed_count=self._completed_count,
                failed_count=self._failed_count,
                cancelled_count=self._cancelled_count,
                paused_count=self._paused_count,
                average_duration_seconds=round(avg_duration, 3),
                active_tasks=0,
                metadata={"thread_safety": "PROTECTED"},
            )

    def clear(self) -> None:
        """Reset task statistics counters."""
        with self._lock:
            self._total_tasks = 0
            self._completed_count = 0
            self._failed_count = 0
            self._cancelled_count = 0
            self._paused_count = 0
            self._total_duration_seconds = 0.0
