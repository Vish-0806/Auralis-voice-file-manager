"""Task Persistence for the Auralis Task Management Runtime (Phase 12.5).

Provides abstract persistence for task state context, metadata snapshots, and recovery checkpoints.
Provider-independent with zero DB-specific dependencies.
"""

import threading
from typing import Any, Dict, Optional

from brain.execution.task.interfaces import ITaskPersistence
from brain.execution.task.task_models import TaskContext


class TaskPersistence(ITaskPersistence):
    """Thread-safe task state context and checkpoint persistence manager."""

    def __init__(self) -> None:
        """Initializes TaskPersistence store."""
        self._lock = threading.RLock()
        self._snapshots: Dict[str, TaskContext] = {}
        self._checkpoints: Dict[str, Dict[str, Any]] = {}

    def save_snapshot(self, context: TaskContext) -> bool:
        """Save a TaskContext state snapshot.

        Args:
            context: TaskContext object.

        Returns:
            True always.
        """
        with self._lock:
            self._snapshots[context.request.task_id] = context
            return True

    def load_snapshot(self, task_id: str) -> Optional[TaskContext]:
        """Load a TaskContext state snapshot.

        Args:
            task_id: Task identifier.

        Returns:
            TaskContext or None if not found.
        """
        with self._lock:
            return self._snapshots.get(task_id)

    def save_checkpoint(self, task_id: str, checkpoint_data: Dict[str, Any]) -> bool:
        """Save recovery checkpoint data for a task.

        Args:
            task_id: Task identifier.
            checkpoint_data: Checkpoint metadata dictionary.

        Returns:
            True always.
        """
        with self._lock:
            self._checkpoints[task_id] = dict(checkpoint_data)
            return True

    def get_checkpoint(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get recovery checkpoint data for a task.

        Args:
            task_id: Task identifier.

        Returns:
            Checkpoint dictionary or None if not found.
        """
        with self._lock:
            chk = self._checkpoints.get(task_id)
            return dict(chk) if chk is not None else None

    def clear(self) -> None:
        """Clear all stored task snapshots and checkpoints."""
        with self._lock:
            self._snapshots.clear()
            self._checkpoints.clear()
