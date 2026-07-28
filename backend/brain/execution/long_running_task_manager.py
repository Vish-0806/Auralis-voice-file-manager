"""Long-Running Task Manager for managing asynchronous and long-running task lifecycles."""

from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from enum import Enum
import logging
import threading
import uuid
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field

from .task_events import TaskEvent, TaskEventType, TaskEventDispatcher


@runtime_checkable
class TaskPersistenceHook(Protocol):
    """Abstract interface for persistent storage integration of long-running tasks."""

    def save_task(self, task: LongRunningTask) -> None:
        """Saves a newly created task record to persistent storage."""
        ...

    def update_task(self, task: LongRunningTask) -> None:
        """Updates an existing task record in persistent storage."""
        ...

    def delete_task(self, task_id: str) -> None:
        """Deletes a task record from persistent storage."""
        ...

    def load_tasks(self) -> List[LongRunningTask]:
        """Loads all persisted task records from persistent storage."""
        ...


class NullTaskPersistenceHook:
    """Default no-op implementation of TaskPersistenceHook."""

    def save_task(self, task: LongRunningTask) -> None:
        pass

    def update_task(self, task: LongRunningTask) -> None:
        pass

    def delete_task(self, task_id: str) -> None:
        pass

    def load_tasks(self) -> List[LongRunningTask]:
        return []


class LongRunningTaskStatus(str, Enum):


    """Lifecycle status states for a long-running task."""

    PENDING = "PENDING"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    WAITING = "WAITING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    TIMED_OUT = "TIMED_OUT"


class LongRunningTaskPriority(str, Enum):
    """Priority levels for long-running task scheduling."""

    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class LongRunningTask(BaseModel):
    """Domain model representing a long-running background execution task record."""

    task_id: str = Field(description="Unique identifier for the task")
    execution_id: Optional[str] = Field(default=None, description="Associated execution run ID if applicable")
    workflow_id: Optional[str] = Field(default=None, description="Associated workflow ID if applicable")
    name: str = Field(description="Human readable name of the task")
    description: Optional[str] = Field(default=None, description="Optional detailed task description")
    status: LongRunningTaskStatus = Field(
        default=LongRunningTaskStatus.PENDING,
        description="Current operational lifecycle status",
    )
    priority: LongRunningTaskPriority = Field(
        default=LongRunningTaskPriority.NORMAL,
        description="Priority scheduling level",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last update timestamp",
    )
    started_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when task started running",
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when task completed or terminated",
    )
    progress: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Completion progress percentage (0.0 to 100.0)",
    )
    estimated_progress: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Estimated completion progress percentage",
    )
    current_step: int = Field(default=0, ge=0, description="Active step index")
    total_steps: int = Field(default=0, ge=0, description="Total number of steps")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Custom task metadata dictionary",
    )
    error: Optional[str] = Field(
        default=None,
        description="Failure exception or error message trace",
    )
    tags: List[str] = Field(
        default_factory=list,
        description="List of tag labels for filtering",
    )

    def is_active(self) -> bool:
        """Determines if the task is in an active non-terminal state."""
        return self.status in (
            LongRunningTaskStatus.PENDING,
            LongRunningTaskStatus.QUEUED,
            LongRunningTaskStatus.RUNNING,
            LongRunningTaskStatus.PAUSED,
            LongRunningTaskStatus.WAITING,
        )

    def is_finished(self) -> bool:
        """Determines if the task is in a terminal state."""
        return self.status in (
            LongRunningTaskStatus.COMPLETED,
            LongRunningTaskStatus.FAILED,
            LongRunningTaskStatus.CANCELLED,
            LongRunningTaskStatus.TIMED_OUT,
        )


class LongRunningTaskConfig(BaseModel):
    """Configuration parameters for LongRunningTaskManager."""

    maximum_tasks: int = Field(
        default=1000,
        ge=1,
        description="Maximum active/pending long-running tasks stored concurrently",
    )
    default_timeout: int = Field(
        default=3600,
        ge=1,
        description="Default timeout limit in seconds for tasks",
    )
    cleanup_after_completion: bool = Field(
        default=True,
        description="Automatically move finalized tasks to completion history",
    )
    maximum_history: int = Field(
        default=5000,
        ge=1,
        description="Maximum finalized task history records retained in memory",
    )


class LongRunningTaskManager:
    """Manages the state and lifecycle of long-running tasks thread-safely."""

    def __init__(
        self,
        config: Optional[LongRunningTaskConfig] = None,
        logger: Optional[logging.Logger] = None,
        event_dispatcher: Optional[TaskEventDispatcher] = None,
        persistence_hook: Optional[TaskPersistenceHook] = None,
    ) -> None:
        """Initializes the manager with configuration options and internal storage.

        Args:
            config: Optional LongRunningTaskConfig settings.
            logger: Optional custom logger.
            event_dispatcher: Optional injected TaskEventDispatcher.
            persistence_hook: Optional injected TaskPersistenceHook.
        """
        self._config = config or LongRunningTaskConfig()
        self._logger = logger or logging.getLogger(__name__)
        self._lock = threading.RLock()
        self._active_tasks: Dict[str, LongRunningTask] = {}
        self._completed_tasks: deque[LongRunningTask] = deque(
            maxlen=self._config.maximum_history
        )
        self._event_dispatcher = event_dispatcher or TaskEventDispatcher(logger=self._logger)
        self._persistence_hook = persistence_hook or NullTaskPersistenceHook()

    @property
    def event_dispatcher(self) -> TaskEventDispatcher:
        """Returns the internal TaskEventDispatcher instance."""
        return self._event_dispatcher

    @property
    def persistence_hook(self) -> TaskPersistenceHook:
        """Returns the internal TaskPersistenceHook instance."""
        return self._persistence_hook

    def _emit_event(
        self,
        task: LongRunningTask,
        event_type: TaskEventType,
        message: Optional[str] = None,
    ) -> None:
        """Safely dispatches a TaskEvent for the task."""
        try:
            event = TaskEvent(
                task_id=task.task_id,
                event_type=event_type,
                timestamp=datetime.now(timezone.utc),
                progress=task.progress,
                current_step=task.current_step,
                total_steps=task.total_steps,
                message=message or task.error or f"Task {event_type.value}",
                metadata=dict(task.metadata),
            )
            self._event_dispatcher.dispatch(event)
        except Exception as e:
            self._logger.warning("Failed to emit task event", exc_info=e)

    def _safe_save_task(self, task: LongRunningTask) -> None:
        """Safely saves a task using the persistence hook without raising exceptions."""
        try:
            self._persistence_hook.save_task(task)
            self._logger.info("Persistence Hook Invoked", extra={"action": "save_task", "task_id": task.task_id})
        except Exception as e:
            self._logger.warning("Persistence Hook Failed", extra={"action": "save_task", "task_id": task.task_id}, exc_info=e)

    def _safe_update_task(self, task: LongRunningTask) -> None:
        """Safely updates a task using the persistence hook without raising exceptions."""
        try:
            self._persistence_hook.update_task(task)
            self._logger.info("Persistence Hook Invoked", extra={"action": "update_task", "task_id": task.task_id})
        except Exception as e:
            self._logger.warning("Persistence Hook Failed", extra={"action": "update_task", "task_id": task.task_id}, exc_info=e)

    def _safe_delete_task(self, task_id: str) -> None:
        """Safely deletes a task using the persistence hook without raising exceptions."""
        try:
            self._persistence_hook.delete_task(task_id)
            self._logger.info("Persistence Hook Invoked", extra={"action": "delete_task", "task_id": task_id})
        except Exception as e:
            self._logger.warning("Persistence Hook Failed", extra={"action": "delete_task", "task_id": task_id}, exc_info=e)

    def _safe_load_tasks(self) -> List[LongRunningTask]:
        """Safely loads tasks using the persistence hook without raising exceptions."""
        try:
            tasks = self._persistence_hook.load_tasks() or []
            self._logger.info("Persistence Hook Invoked", extra={"action": "load_tasks", "count": len(tasks)})
            return tasks
        except Exception as e:
            self._logger.warning("Persistence Hook Failed", extra={"action": "load_tasks"}, exc_info=e)
            return []



    def create_task(
        self,
        name: str,
        description: Optional[str] = None,
        execution_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        priority: LongRunningTaskPriority = LongRunningTaskPriority.NORMAL,
        total_steps: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        task_id: Optional[str] = None,
    ) -> Optional[LongRunningTask]:
        """Creates a new long-running task record.

        Args:
            name: Title or name of the task.
            description: Optional detailed summary description.
            execution_id: Optional linked execution ID.
            workflow_id: Optional linked workflow ID.
            priority: Scheduling priority level.
            total_steps: Total step count.
            metadata: Custom metadata dictionary.
            tags: Category tags.
            task_id: Explicit task ID or None to auto-generate.

        Returns:
            Created LongRunningTask or None if capacity is exceeded. Never raises exceptions.
        """
        if not name:
            return None

        with self._lock:
            if len(self._active_tasks) >= self._config.maximum_tasks:
                self.cleanup()
                if len(self._active_tasks) >= self._config.maximum_tasks:
                    return None

            tid = task_id or f"task_{uuid.uuid4().hex[:12]}"
            now = datetime.now(timezone.utc)

            task = LongRunningTask(
                task_id=tid,
                execution_id=execution_id,
                workflow_id=workflow_id,
                name=name,
                description=description,
                status=LongRunningTaskStatus.PENDING,
                priority=priority,
                created_at=now,
                updated_at=now,
                total_steps=total_steps,
                metadata=metadata or {},
                tags=tags or [],
            )

            self._active_tasks[tid] = task
            self._logger.info("Task Created", extra={"task_id": tid, "task_name": name})
            self._safe_save_task(task)
            self._emit_event(task, TaskEventType.TASK_CREATED)
            return task


    def queue_task(self, task_id: str) -> bool:
        """Transitions a PENDING task to QUEUED status.

        Args:
            task_id: Target task ID.

        Returns:
            True if status transitioned, False otherwise.
        """
        if not task_id or not isinstance(task_id, str):
            return False

        with self._lock:
            task = self._active_tasks.get(task_id)
            if not task or task.status != LongRunningTaskStatus.PENDING:
                return False

            task.status = LongRunningTaskStatus.QUEUED
            task.updated_at = datetime.now(timezone.utc)
            self._logger.info("Task Queued", extra={"task_id": task_id})
            self._safe_update_task(task)
            self._emit_event(task, TaskEventType.TASK_QUEUED)
            return True

    def start_task(self, task_id: str) -> bool:
        """Transitions a task to RUNNING status.

        Args:
            task_id: Target task ID.

        Returns:
            True if status transitioned, False otherwise.
        """
        if not task_id or not isinstance(task_id, str):
            return False

        with self._lock:
            task = self._active_tasks.get(task_id)
            if not task or task.status not in (
                LongRunningTaskStatus.PENDING,
                LongRunningTaskStatus.QUEUED,
                LongRunningTaskStatus.PAUSED,
            ):
                return False

            now = datetime.now(timezone.utc)
            task.status = LongRunningTaskStatus.RUNNING
            task.updated_at = now
            if task.started_at is None:
                task.started_at = now

            self._logger.info("Task Started", extra={"task_id": task_id})
            self._safe_update_task(task)
            self._emit_event(task, TaskEventType.TASK_STARTED)
            return True

    def pause_task(self, task_id: str) -> bool:
        """Pauses a currently RUNNING task.

        Args:
            task_id: Target task ID.

        Returns:
            True if status transitioned to PAUSED, False otherwise.
        """
        if not task_id or not isinstance(task_id, str):
            return False

        with self._lock:
            task = self._active_tasks.get(task_id)
            if not task or task.status != LongRunningTaskStatus.RUNNING:
                return False

            task.status = LongRunningTaskStatus.PAUSED
            task.updated_at = datetime.now(timezone.utc)
            self._logger.info("Task Paused", extra={"task_id": task_id})
            self._safe_update_task(task)
            self._emit_event(task, TaskEventType.TASK_PAUSED)
            return True

    def resume_task(self, task_id: str) -> bool:
        """Resumes a PAUSED task back to RUNNING status.

        Args:
            task_id: Target task ID.

        Returns:
            True if status transitioned to RUNNING, False otherwise.
        """
        if not task_id or not isinstance(task_id, str):
            return False

        with self._lock:
            task = self._active_tasks.get(task_id)
            if not task or task.status != LongRunningTaskStatus.PAUSED:
                return False

            task.status = LongRunningTaskStatus.RUNNING
            task.updated_at = datetime.now(timezone.utc)
            self._logger.info("Task Resumed", extra={"task_id": task_id})
            self._safe_update_task(task)
            self._emit_event(task, TaskEventType.TASK_RESUMED)
            return True


    def cancel_task(self, task_id: str) -> bool:
        """Cancels an active task.

        Args:
            task_id: Target task ID.

        Returns:
            True if cancelled, False if unknown or already in terminal state.
        """
        if not task_id or not isinstance(task_id, str):
            return False

        with self._lock:
            task = self._active_tasks.get(task_id)
            if not task or task.is_finished():
                return False

            now = datetime.now(timezone.utc)
            task.status = LongRunningTaskStatus.CANCELLED
            task.updated_at = now
            task.completed_at = now

            if self._config.cleanup_after_completion:
                self._archive_task_locked(task)

            self._logger.info("Task Cancelled", extra={"task_id": task_id})
            self._safe_update_task(task)
            self._emit_event(task, TaskEventType.TASK_CANCELLED)
            return True

    def complete_task(
        self,
        task_id: str,
        result_metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Marks a task as COMPLETED with 100% progress.

        Args:
            task_id: Target task ID.
            result_metadata: Optional final metadata to merge.

        Returns:
            True if completed, False if unknown or already finished.
        """
        if not task_id or not isinstance(task_id, str):
            return False

        with self._lock:
            task = self._active_tasks.get(task_id)
            if not task or task.is_finished():
                return False

            now = datetime.now(timezone.utc)
            task.status = LongRunningTaskStatus.COMPLETED
            task.progress = 100.0
            task.updated_at = now
            task.completed_at = now

            if result_metadata:
                task.metadata.update(result_metadata)

            if self._config.cleanup_after_completion:
                self._archive_task_locked(task)

            self._logger.info("Task Completed", extra={"task_id": task_id})
            self._safe_update_task(task)
            self._emit_event(task, TaskEventType.TASK_COMPLETED)
            return True

    def fail_task(self, task_id: str, error_message: str) -> bool:
        """Marks a task as FAILED with an error message trace.

        Args:
            task_id: Target task ID.
            error_message: Error details.

        Returns:
            True if state updated, False if unknown or finished.
        """
        if not task_id or not isinstance(task_id, str):
            return False

        with self._lock:
            task = self._active_tasks.get(task_id)
            if not task or task.is_finished():
                return False

            now = datetime.now(timezone.utc)
            task.status = LongRunningTaskStatus.FAILED
            task.error = error_message
            task.updated_at = now
            task.completed_at = now

            if self._config.cleanup_after_completion:
                self._archive_task_locked(task)

            self._logger.info(
                "Task Failed",
                extra={"task_id": task_id, "error": error_message},
            )
            self._safe_update_task(task)
            self._emit_event(task, TaskEventType.TASK_FAILED, message=error_message)
            return True

    def timeout_task(self, task_id: str) -> bool:
        """Marks a task as TIMED_OUT.

        Args:
            task_id: Target task ID.

        Returns:
            True if timed out, False if unknown or finished.
        """
        if not task_id or not isinstance(task_id, str):
            return False

        with self._lock:
            task = self._active_tasks.get(task_id)
            if not task or task.is_finished():
                return False

            now = datetime.now(timezone.utc)
            task.status = LongRunningTaskStatus.TIMED_OUT
            task.error = "Task execution timed out"
            task.updated_at = now
            task.completed_at = now

            if self._config.cleanup_after_completion:
                self._archive_task_locked(task)

            self._logger.info("Task Timed Out", extra={"task_id": task_id})
            self._safe_update_task(task)
            self._emit_event(task, TaskEventType.TASK_TIMED_OUT, message="Task execution timed out")
            return True


    def update_progress(
        self,
        task_id: str,
        progress: float,
        current_step: Optional[int] = None,
        total_steps: Optional[int] = None,
        estimated_progress: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Updates progress parameters and metadata for an active task.

        Args:
            task_id: Target task ID.
            progress: Percentage completed (0.0 to 100.0).
            current_step: Optional current step index.
            total_steps: Optional total step count.
            estimated_progress: Optional estimated percentage progress.
            metadata: Optional metadata to merge into task metadata.

        Returns:
            True if updated, False if unknown or finished.
        """
        if not task_id or not isinstance(task_id, str):
            return False

        with self._lock:
            task = self._active_tasks.get(task_id)
            if not task or task.is_finished():
                return False

            task.progress = max(0.0, min(100.0, float(progress)))
            if current_step is not None:
                task.current_step = current_step
            if total_steps is not None:
                task.total_steps = total_steps
            if estimated_progress is not None:
                task.estimated_progress = max(0.0, min(100.0, float(estimated_progress)))
            if metadata:
                task.metadata.update(metadata)

            task.updated_at = datetime.now(timezone.utc)
            self._logger.info(
                "Progress Updated",
                extra={"task_id": task_id, "progress": task.progress},
            )
            self._safe_update_task(task)
            self._emit_event(task, TaskEventType.TASK_PROGRESS)
            return True



    def get_task(self, task_id: str) -> Optional[LongRunningTask]:
        """Retrieves a task by ID from active or completed stores.

        Args:
            task_id: Unique task identifier.

        Returns:
            LongRunningTask instance or None. Never throws exceptions.
        """
        if not task_id or not isinstance(task_id, str):
            return None

        with self._lock:
            if task_id in self._active_tasks:
                return self._active_tasks[task_id]

            for task in self._completed_tasks:
                if task.task_id == task_id:
                    return task

            return None

    def list_tasks(
        self,
        status: Optional[LongRunningTaskStatus] = None,
    ) -> List[LongRunningTask]:
        """Lists tasks across active and completed stores.

        Args:
            status: Optional filter by status.

        Returns:
            List of matching LongRunningTask objects.
        """
        with self._lock:
            all_tasks = list(self._active_tasks.values()) + list(self._completed_tasks)
            if status is not None:
                return [t for t in all_tasks if t.status == status]
            return all_tasks

    def list_running(self) -> List[LongRunningTask]:
        """Lists all tasks currently in RUNNING state.

        Returns:
            List of running LongRunningTask objects.
        """
        with self._lock:
            return [
                t for t in self._active_tasks.values()
                if t.status == LongRunningTaskStatus.RUNNING
            ]

    def list_completed(self) -> List[LongRunningTask]:
        """Lists all tasks currently in terminal states.

        Returns:
            List of completed/terminated LongRunningTask objects.
        """
        with self._lock:
            return list(self._completed_tasks) + [
                t for t in self._active_tasks.values()
                if t.is_finished()
            ]

    def cleanup(self) -> int:
        """Moves terminal active tasks to completed history store.

        Returns:
            Number of tasks moved to completion history.
        """
        with self._lock:
            moved_count = 0
            for task_id, task in list(self._active_tasks.items()):
                if task.is_finished():
                    self._archive_task_locked(task)
                    moved_count += 1

            self._logger.info("History Cleaned", extra={"cleaned_count": moved_count})
            return moved_count

    def clear(self) -> None:
        """Clears all active and completed tasks from memory."""
        with self._lock:
            self._active_tasks.clear()
            self._completed_tasks.clear()

    def recover_tasks(self) -> int:
        """Restores persisted task records into active and completed in-memory stores.

        Returns:
            Count of active tasks successfully recovered into memory.
        """
        loaded_tasks = self._safe_load_tasks()
        if not loaded_tasks:
            return 0

        recovered_active = 0
        with self._lock:
            for task in loaded_tasks:
                if not isinstance(task, LongRunningTask) or not getattr(task, "task_id", None) or not getattr(task, "status", None):
                    self._logger.warning("Corrupted task skipped during recovery", extra={"task": str(task)})
                    continue

                status_val = task.status.value if hasattr(task.status, "value") else str(task.status)
                if task.is_finished():
                    if task not in self._completed_tasks:
                        self._completed_tasks.append(task)
                else:
                    self._active_tasks[task.task_id] = task
                    recovered_active += 1
                    self._logger.info("Task Recovered", extra={"task_id": task.task_id, "status": status_val})
                    self._emit_event(task, TaskEventType.TASK_RECOVERED, message="Task state recovered from persistence")

        return recovered_active

    def cleanup_expired_tasks(self, retention_seconds: Optional[int] = None) -> int:
        """Removes expired completed, timed-out, or cancelled tasks from history and storage.

        Args:
            retention_seconds: Optional custom retention limit in seconds (defaults to config limit).

        Returns:
            Total count of tasks cleaned.
        """
        retention = retention_seconds if retention_seconds is not None else 86400
        now = datetime.now(timezone.utc)
        cleaned_count = 0

        with self._lock:
            # First move any terminal active tasks to completed history
            self.cleanup()

            # Evict history beyond maximum_history
            while len(self._completed_tasks) > self._config.maximum_history:
                oldest = self._completed_tasks.popleft()
                self._safe_delete_task(oldest.task_id)
                self._emit_event(oldest, TaskEventType.TASK_CLEANED, message="Maximum history capacity exceeded")
                cleaned_count += 1

            # Evict tasks exceeding retention period
            fresh_history: deque[LongRunningTask] = deque(maxlen=self._config.maximum_history)
            for task in list(self._completed_tasks):
                comp_at = task.completed_at or task.updated_at or task.created_at
                if comp_at and (now - comp_at).total_seconds() > retention:
                    self._safe_delete_task(task.task_id)
                    self._emit_event(task, TaskEventType.TASK_CLEANED, message="Retention period expired")
                    cleaned_count += 1
                else:
                    fresh_history.append(task)

            self._completed_tasks = fresh_history
            self._logger.info("Task Cleanup", extra={"cleaned_count": cleaned_count})

        return cleaned_count

    def check_timeouts(self) -> int:
        """Checks active tasks against timeout limits and marks expired tasks TIMED_OUT.

        Returns:
            Count of tasks timed out.
        """
        now = datetime.now(timezone.utc)
        timed_out_count = 0

        with self._lock:
            for task in list(self._active_tasks.values()):
                if task.is_active():
                    timeout_val = task.metadata.get("timeout") or self._config.default_timeout
                    if (now - task.created_at).total_seconds() > timeout_val:
                        self.timeout_task(task.task_id)
                        self._logger.info("Timeout Cleanup", extra={"task_id": task.task_id})
                        timed_out_count += 1

        return timed_out_count

    def _archive_task_locked(self, task: LongRunningTask) -> None:
        """Internal helper to move a task from active map to completed deque under lock."""
        self._active_tasks.pop(task.task_id, None)
        if task not in self._completed_tasks:
            self._completed_tasks.append(task)
            self._logger.info("Task Archived", extra={"task_id": task.task_id})
            self._emit_event(task, TaskEventType.TASK_ARCHIVED, message="Task archived to completion history")

