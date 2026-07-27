"""Execution State Manager managing active execution lifecycles in-memory and thread-safely."""

from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
import threading
from typing import Any, Dict, List, Optional

from brain.execution.execution_state import (
    ExecutionStatus,
    ExecutionProgress,
    ExecutionState,
    ExecutionSnapshot,
    ExecutionStateConfig,
)


class ExecutionStateManager:
    """Manages active executions and their snapshots in-memory with thread safety."""

    def __init__(self, config: Optional[ExecutionStateConfig] = None) -> None:
        """Initializes the manager with in-memory stores and a reentrant lock."""
        self._config = config or ExecutionStateConfig()
        self._lock = threading.RLock()
        self._active_executions: Dict[str, ExecutionState] = {}
        self._snapshot_history: Dict[str, deque[ExecutionSnapshot]] = {}

    def create_execution(
        self,
        execution_id: str,
        user_id: int,
        workflow_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExecutionState:
        """Creates a new execution, registers it, and returns the state.

        Args:
            execution_id: Unique identifier for the execution.
            user_id: User ID associated with this run.
            workflow_id: Optional ID of the parent workflow.
            metadata: Optional metadata dict.

        Returns:
            The created ExecutionState.
        """
        with self._lock:
            state = ExecutionState(
                execution_id=execution_id,
                user_id=user_id,
                workflow_id=workflow_id,
                metadata=metadata or {},
            )
            self._active_executions[execution_id] = state
            self._snapshot_history[execution_id] = deque(
                maxlen=self._config.snapshot_history_size
            )
            # Create an initial snapshot
            self._create_snapshot(state)
            return state

    def get_execution(self, execution_id: str) -> Optional[ExecutionState]:
        """Retrieves the execution state for a given ID.

        Args:
            execution_id: Unique identifier for the execution.

        Returns:
            ExecutionState or None if not found.
        """
        with self._lock:
            return self._active_executions.get(execution_id)

    def list_active(self) -> List[ExecutionState]:
        """Lists all executions currently in an active state.

        Returns:
            List of active ExecutionState objects.
        """
        with self._lock:
            return [
                state for state in self._active_executions.values()
                if state.is_active()
            ]

    def list_finished(self) -> List[ExecutionState]:
        """Lists all executions currently in a finished state.

        Returns:
            List of finished ExecutionState objects.
        """
        with self._lock:
            return [
                state for state in self._active_executions.values()
                if state.is_finished()
            ]

    def update_progress(
        self,
        execution_id: str,
        percentage: float,
        current_step: int,
        total_steps: int,
        current_operation: Optional[str] = None,
        estimated_remaining_seconds: Optional[float] = None,
    ) -> bool:
        """Updates execution progress parameters and creates a snapshot.

        Args:
            execution_id: Unique identifier for the execution.
            percentage: Completion percentage (0.0 to 100.0).
            current_step: Current step number.
            total_steps: Total steps count.
            current_operation: Description of the active operation.
            estimated_remaining_seconds: Seconds remaining estimation.

        Returns:
            True if progress was successfully updated, False if ID is unknown.
        """
        with self._lock:
            state = self._active_executions.get(execution_id)
            if not state:
                return False

            state.progress.update_progress(
                percentage=percentage,
                current_step=current_step,
                total_steps=total_steps,
                current_operation=current_operation,
                estimated_remaining_seconds=estimated_remaining_seconds,
            )
            state._touch()
            self._create_snapshot(state)
            return True

    def mark_running(self, execution_id: str) -> bool:
        """Transitions execution state to RUNNING.

        Args:
            execution_id: Unique identifier for the execution.

        Returns:
            True if transitioned, False if ID is unknown.
        """
        with self._lock:
            state = self._active_executions.get(execution_id)
            if not state:
                return False
            state.mark_running()
            self._create_snapshot(state)
            return True

    def mark_paused(self, execution_id: str) -> bool:
        """Transitions execution state to PAUSED.

        Args:
            execution_id: Unique identifier for the execution.

        Returns:
            True if transitioned, False if ID is unknown.
        """
        with self._lock:
            state = self._active_executions.get(execution_id)
            if not state:
                return False
            state.mark_paused()
            self._create_snapshot(state)
            return True

    def mark_retrying(self, execution_id: str) -> bool:
        """Transitions execution state to RETRYING and increments retry count.

        Args:
            execution_id: Unique identifier for the execution.

        Returns:
            True if transitioned, False if ID is unknown.
        """
        with self._lock:
            state = self._active_executions.get(execution_id)
            if not state:
                return False
            state.mark_retrying()
            self._create_snapshot(state)
            return True

    def mark_completed(self, execution_id: str) -> bool:
        """Transitions execution state to COMPLETED and records final snapshot.

        Args:
            execution_id: Unique identifier for the execution.

        Returns:
            True if transitioned, False if ID is unknown.
        """
        with self._lock:
            state = self._active_executions.get(execution_id)
            if not state:
                return False
            state.mark_completed()
            self._create_snapshot(state)
            return True

    def mark_failed(self, execution_id: str, error_message: str) -> bool:
        """Transitions execution state to FAILED and records error message.

        Args:
            execution_id: Unique identifier for the execution.
            error_message: Error details.

        Returns:
            True if transitioned, False if ID is unknown.
        """
        with self._lock:
            state = self._active_executions.get(execution_id)
            if not state:
                return False
            state.mark_failed(error_message)
            self._create_snapshot(state)
            return True

    def mark_cancelled(self, execution_id: str) -> bool:
        """Transitions execution state to CANCELLED.

        Args:
            execution_id: Unique identifier for the execution.

        Returns:
            True if transitioned, False if ID is unknown.
        """
        with self._lock:
            state = self._active_executions.get(execution_id)
            if not state:
                return False
            state.mark_cancelled()
            self._create_snapshot(state)
            return True

    def remove_execution(self, execution_id: str) -> bool:
        """Deletes execution record and its history.

        Args:
            execution_id: Unique identifier for the execution.

        Returns:
            True if removed, False if ID is unknown.
        """
        with self._lock:
            if execution_id not in self._active_executions:
                return False
            self._active_executions.pop(execution_id)
            self._snapshot_history.pop(execution_id, None)
            return True

    def get_snapshot_history(self, execution_id: str) -> List[ExecutionSnapshot]:
        """Returns chronological list of snapshots for the given execution ID.

        Args:
            execution_id: Unique identifier for the execution.

        Returns:
            List of ExecutionSnapshot objects, or empty list if ID is unknown.
        """
        with self._lock:
            history = self._snapshot_history.get(execution_id)
            if history is None:
                return []
            return list(history)

    def clear(self) -> None:
        """Removes every execution and snapshot record in-memory."""
        with self._lock:
            self._active_executions.clear()
            self._snapshot_history.clear()

    def _create_snapshot(self, state: ExecutionState) -> None:
        """Appends a new ExecutionSnapshot of the active state to the history."""
        snapshot = ExecutionSnapshot(
            execution_id=state.execution_id,
            status=state.status,
            percentage=state.progress.percentage,
            current_operation=state.progress.current_operation,
            timestamp=datetime.now(timezone.utc),
        )
        history = self._snapshot_history.get(state.execution_id)
        if history is not None:
            history.append(snapshot)
