"""Abstract Base Class interfaces for the Auralis Task Management Runtime (Phase 12.5).

Defines canonical interfaces for task scheduler, executor, monitor, persistence, provider, and runtime.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from brain.execution.task.task_models import (
    TaskContext,
    TaskExecution,
    TaskHealth,
    TaskProgress,
    TaskRequest,
    TaskResult,
    TaskStatistics,
)


class ITaskScheduler(ABC):
    """Interface for priority-aware task queuing, delay handling, and recurring task scheduling."""

    @abstractmethod
    def enqueue(self, request: TaskRequest) -> TaskExecution:
        """Enqueue task into priority queue."""
        pass

    @abstractmethod
    def dequeue(self) -> Optional[TaskExecution]:
        """Dequeue highest priority ready task."""
        pass

    @abstractmethod
    def peek_queue(self) -> List[TaskExecution]:
        """View active priority queue items."""
        pass


class ITaskExecutor(ABC):
    """Interface for executing long-running background tasks with pause/resume/cancel/timeout controls."""

    @abstractmethod
    def execute_task(
        self,
        request: TaskRequest,
        context: Optional[Dict[str, Any]] = None,
    ) -> TaskResult:
        """Execute task request long-running lifecycle."""
        pass

    @abstractmethod
    def pause_task(self, task_id: str) -> bool:
        """Pause running task."""
        pass

    @abstractmethod
    def resume_task(self, task_id: str) -> bool:
        """Resume paused task."""
        pass

    @abstractmethod
    def cancel_task(self, task_id: str) -> bool:
        """Cancel task execution."""
        pass


class ITaskMonitor(ABC):
    """Interface for tracking task progress metrics and duration."""

    @abstractmethod
    def update_progress(
        self,
        task_id: str,
        completed_steps: int,
        total_steps: int,
        status_message: str = "",
    ) -> TaskProgress:
        """Update progress metrics for active task."""
        pass

    @abstractmethod
    def get_progress(self, task_id: str) -> Optional[TaskProgress]:
        """Get latest progress metrics for task."""
        pass


class ITaskPersistence(ABC):
    """Interface for persisting task state, execution snapshots, and recovery checkpoints."""

    @abstractmethod
    def save_snapshot(self, context: TaskContext) -> bool:
        """Save task state context snapshot."""
        pass

    @abstractmethod
    def load_snapshot(self, task_id: str) -> Optional[TaskContext]:
        """Load task state context snapshot."""
        pass

    @abstractmethod
    def save_checkpoint(self, task_id: str, checkpoint_data: Dict[str, Any]) -> bool:
        """Save recovery checkpoint data."""
        pass

    @abstractmethod
    def get_checkpoint(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get recovery checkpoint data."""
        pass


class ITaskProvider(ABC):
    """Interface for aggregate Task Provider."""

    @abstractmethod
    def submit_task(
        self,
        request_or_payload: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> TaskResult:
        """Submit background task for processing."""
        pass

    @abstractmethod
    def cancel_task(self, task_id: str) -> bool:
        """Cancel background task."""
        pass

    @abstractmethod
    def get_task_progress(self, task_id: str) -> Optional[TaskProgress]:
        """Fetch real-time progress for task."""
        pass

    @abstractmethod
    def health_check(self) -> TaskHealth:
        """Report overall component health."""
        pass

    @abstractmethod
    def get_statistics(self) -> TaskStatistics:
        """Return snapshot of aggregate task statistics."""
        pass


class ITaskRuntime(ABC):
    """Interface for the thread-safe singleton lifecycle manager."""

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize task runtime lifecycle."""
        pass

    @abstractmethod
    def shutdown(self) -> bool:
        """Gracefully shut down task runtime lifecycle."""
        pass

    @abstractmethod
    def process_task(
        self,
        request_or_payload: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> TaskResult:
        """Process background task through provider."""
        pass

    @abstractmethod
    def health_check(self) -> TaskHealth:
        """Fetch real-time health diagnostic status."""
        pass

    @abstractmethod
    def get_statistics(self) -> TaskStatistics:
        """Fetch snapshot of task execution statistics."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Reset task execution statistics and transient state."""
        pass
