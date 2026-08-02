"""Task Runtime for the Auralis Task Management Runtime (Phase 12.5).

Thread-safe singleton lifecycle manager orchestrating the TaskProvider.
Manages status transitions, process_task delegation, health monitoring, and statistics.
"""

from enum import Enum
import logging
import threading
from typing import Any, Dict, Optional

from brain.execution.task.interfaces import ITaskRuntime
from brain.execution.task.task_models import (
    TaskHealth,
    TaskProgress,
    TaskResult,
    TaskStatistics,
)
from brain.execution.task.task_provider import TaskProvider

logger = logging.getLogger(__name__)


class TaskRuntimeStatus(str, Enum):
    """Lifecycle status states for the Task Management Runtime."""

    INITIALIZING = "INITIALIZING"
    READY = "READY"
    RUNNING = "RUNNING"
    DEGRADED = "DEGRADED"
    ERROR = "ERROR"
    SHUTDOWN = "SHUTDOWN"


class TaskRuntime(ITaskRuntime):
    """Thread-safe singleton runtime managing the TaskProvider lifecycle."""

    def __init__(self, provider: Optional[TaskProvider] = None) -> None:
        """Initializes TaskRuntime with optional provider instance."""
        self._lock = threading.RLock()
        self._status = TaskRuntimeStatus.INITIALIZING
        self._provider = provider or TaskProvider()

    @property
    def status(self) -> TaskRuntimeStatus:
        with self._lock:
            return self._status

    @property
    def provider(self) -> TaskProvider:
        return self._provider

    def initialize(self) -> bool:
        """Initialize the Task Management Runtime.

        Returns:
            True if initialized successfully.
        """
        with self._lock:
            if self._status == TaskRuntimeStatus.READY:
                return True

            try:
                self._status = TaskRuntimeStatus.READY
                logger.info("Task Management Runtime Initialized")
                return True
            except Exception as exc:
                self._status = TaskRuntimeStatus.ERROR
                logger.error("TaskRuntime initialization failed: %s", exc)
                return False

    def shutdown(self) -> bool:
        """Gracefully shut down task runtime.

        Returns:
            True always.
        """
        with self._lock:
            self._status = TaskRuntimeStatus.SHUTDOWN
            logger.info("Task Management Runtime Shutdown")
            return True

    def process_task(
        self,
        request_or_payload: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> TaskResult:
        """Process background task through the TaskProvider.

        Args:
            request_or_payload: TaskRequest, payload object, or dict.
            context: Optional contextual parameters.

        Returns:
            Immutable TaskResult model.
        """
        with self._lock:
            if self._status in (TaskRuntimeStatus.INITIALIZING, TaskRuntimeStatus.SHUTDOWN):
                self.initialize()

            prev_status = self._status
            self._status = TaskRuntimeStatus.RUNNING

        try:
            return self._provider.submit_task(request_or_payload, context=context)
        finally:
            with self._lock:
                if self._status == TaskRuntimeStatus.RUNNING:
                    self._status = prev_status if prev_status != TaskRuntimeStatus.INITIALIZING else TaskRuntimeStatus.READY

    def pause_task(self, task_id: str) -> bool:
        """Pause running task by task_id."""
        return self._provider.pause_task(task_id)

    def resume_task(self, task_id: str) -> bool:
        """Resume paused task by task_id."""
        return self._provider.resume_task(task_id)

    def cancel_task(self, task_id: str) -> bool:
        """Cancel background task by task_id."""
        return self._provider.cancel_task(task_id)

    def get_task_progress(self, task_id: str) -> Optional[TaskProgress]:
        """Fetch progress for task_id."""
        return self._provider.get_task_progress(task_id)

    def health_check(self) -> TaskHealth:
        """Fetch health check diagnostic status."""
        with self._lock:
            provider_health = self._provider.health_check()
            is_healthy = (self._status in (TaskRuntimeStatus.READY, TaskRuntimeStatus.RUNNING)) and provider_health.healthy

            issues = list(provider_health.detected_issues)
            if self._status == TaskRuntimeStatus.ERROR:
                issues.append("Task runtime is in ERROR status")

            return TaskHealth(
                status=self._status.value if is_healthy else "ERROR",
                healthy=is_healthy,
                components=provider_health.components,
                statistics=self.get_statistics().model_dump(),
                detected_issues=issues,
                metadata={"thread_safety": "PROTECTED"},
            )

    def get_statistics(self) -> TaskStatistics:
        """Fetch task execution statistics snapshot."""
        with self._lock:
            return self._provider.get_statistics()

    def clear(self) -> None:
        """Reset task statistics and transient state."""
        with self._lock:
            self._provider.clear()
            if self._status != TaskRuntimeStatus.SHUTDOWN:
                self._status = TaskRuntimeStatus.READY
            logger.info("TaskRuntime cleared")
