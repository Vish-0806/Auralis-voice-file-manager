"""Task Events and Progress Monitoring Dispatcher for Auralis Long-Running Task Subsystem."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
import logging
import threading
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable
import uuid

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


class TaskEventType(str, Enum):
    """Event types representing lifecycle transitions and progress milestones of long-running tasks."""

    TASK_CREATED = "TASK_CREATED"
    TASK_QUEUED = "TASK_QUEUED"
    TASK_STARTED = "TASK_STARTED"
    TASK_PROGRESS = "TASK_PROGRESS"
    TASK_PAUSED = "TASK_PAUSED"
    TASK_RESUMED = "TASK_RESUMED"
    TASK_COMPLETED = "TASK_COMPLETED"
    TASK_FAILED = "TASK_FAILED"
    TASK_CANCELLED = "TASK_CANCELLED"
    TASK_TIMED_OUT = "TASK_TIMED_OUT"


class TaskEvent(BaseModel):
    """Encapsulates a task lifecycle or progress event notification payload."""

    event_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique event notification ID",
    )
    task_id: str = Field(description="Associated task ID")
    event_type: TaskEventType = Field(description="Type of task event")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Event creation timestamp",
    )
    progress: float = Field(default=0.0, ge=0.0, le=100.0, description="Completion percentage (0-100)")
    current_step: int = Field(default=0, ge=0, description="Current step index")
    total_steps: int = Field(default=0, ge=0, description="Total expected step count")
    message: Optional[str] = Field(default=None, description="Human readable event message or summary")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context metadata payload")


@runtime_checkable
class TaskEventListener(Protocol):
    """Protocol interface for objects subscribing to long-running task events."""

    def on_event(self, event: TaskEvent) -> None:
        """Callback invoked when a TaskEvent is dispatched.

        Args:
            event: The dispatched TaskEvent instance.
        """
        ...


class TaskEventDispatcher:
    """Thread-safe event dispatcher for broadcasting task lifecycle and progress events."""

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        """Initializes the TaskEventDispatcher.

        Args:
            logger: Optional custom logger.
        """
        self._logger = logger or logging.getLogger(__name__)
        self._lock = threading.RLock()
        self._listeners: List[TaskEventListener] = []

    def register_listener(self, listener: Any) -> bool:
        """Registers an event listener to receive TaskEvent broadcasts.

        Args:
            listener: An object implementing TaskEventListener or callable on_event method.

        Returns:
            True if registered, False if already registered or invalid.
        """
        if listener is None:
            return False

        with self._lock:
            if listener in self._listeners:
                return False
            self._listeners.append(listener)
            self._logger.info("Listener Registered", extra={"listener": str(listener), "total_listeners": len(self._listeners)})
            return True

    def remove_listener(self, listener: Any) -> bool:
        """Unregisters an event listener.

        Args:
            listener: Target listener instance to remove.

        Returns:
            True if removed, False if not found.
        """
        if listener is None:
            return False

        with self._lock:
            if listener not in self._listeners:
                return False
            self._listeners.remove(listener)
            self._logger.info("Listener Removed", extra={"listener": str(listener), "remaining_listeners": len(self._listeners)})
            return True

    def listener_count(self) -> int:
        """Returns current active listener count.

        Returns:
            Number of registered listeners.
        """
        with self._lock:
            return len(self._listeners)

    def clear(self) -> None:
        """Removes all registered listeners."""
        with self._lock:
            self._listeners.clear()
            self._logger.info("All Listeners Cleared")

    def dispatch(self, event: TaskEvent) -> int:
        """Dispatches a TaskEvent to all registered listeners safely.

        Args:
            event: TaskEvent payload to broadcast.

        Returns:
            Number of listeners notified. Never raises exceptions.
        """
        if not event:
            return 0

        with self._lock:
            listeners_snapshot = list(self._listeners)

        type_str = event.event_type.value if hasattr(event.event_type, "value") else str(event.event_type)
        self._logger.info(
            "Task Event Dispatched",
            extra={
                "event_id": event.event_id,
                "task_id": event.task_id,
                "event_type": type_str,
            },
        )

        if event.event_type == TaskEventType.TASK_PROGRESS:
            self._logger.info(
                "Progress Event",
                extra={
                    "task_id": event.task_id,
                    "progress": event.progress,
                    "current_step": event.current_step,
                    "total_steps": event.total_steps,
                },
            )
        elif event.event_type == TaskEventType.TASK_COMPLETED:
            self._logger.info("Completion Event", extra={"task_id": event.task_id})
        elif event.event_type in (TaskEventType.TASK_FAILED, TaskEventType.TASK_CANCELLED, TaskEventType.TASK_TIMED_OUT):
            self._logger.info(
                "Failure Event",
                extra={
                    "task_id": event.task_id,
                    "event_type": type_str,
                    "error": event.message or "Task failed or cancelled",
                },
            )

        notified_count = 0
        for listener in listeners_snapshot:
            try:
                if hasattr(listener, "on_event") and callable(listener.on_event):
                    listener.on_event(event)
                elif callable(listener):
                    listener(event)
                notified_count += 1
            except Exception as e:
                self._logger.warning(
                    "Listener Error",
                    extra={"listener": str(listener), "task_id": event.task_id, "event_type": type_str},
                    exc_info=e,
                )

        return notified_count
