"""Checkpoint Manager for the Auralis Execution Recovery & State Management Runtime (Phase 12.8).

Responsible for creating, storing, querying, and sorting execution checkpoints per execution_id.
"""

from datetime import datetime, timezone
import threading
from typing import Any, Dict, List, Optional

from brain.execution.recovery.exceptions import CheckpointError
from brain.execution.recovery.interfaces import ICheckpointManager
from brain.execution.recovery.recovery_models import CheckpointType, ExecutionCheckpoint


class CheckpointManager(ICheckpointManager):
    """Thread-safe checkpoint manager creating and storing ExecutionCheckpoint models."""

    def __init__(self) -> None:
        """Initializes CheckpointManager with internal checkpoint store."""
        self._lock = threading.RLock()
        self._checkpoints: Dict[str, List[ExecutionCheckpoint]] = {}
        self._all_checkpoints: Dict[str, ExecutionCheckpoint] = {}

    def create_checkpoint(
        self,
        execution_id: str,
        checkpoint_type: CheckpointType = CheckpointType.AUTOMATIC,
        state_data: Optional[Dict[str, Any]] = None,
        step_index: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExecutionCheckpoint:
        """Create and store an ExecutionCheckpoint.

        Args:
            execution_id: Execution identifier.
            checkpoint_type: CheckpointType enum (AUTOMATIC, MANUAL, STAGE, STEP, EMERGENCY).
            state_data: Dictionary of state data.
            step_index: Integer index of execution step.
            metadata: Optional metadata dictionary.

        Returns:
            ExecutionCheckpoint model.

        Raises:
            CheckpointError: If execution_id is empty.
        """
        if not execution_id:
            raise CheckpointError("execution_id cannot be empty when creating checkpoint")

        with self._lock:
            chk = ExecutionCheckpoint(
                execution_id=execution_id,
                checkpoint_type=checkpoint_type,
                state_data=dict(state_data or {}),
                step_index=step_index,
                metadata=dict(metadata or {}),
                timestamp=datetime.now(timezone.utc),
            )

            if execution_id not in self._checkpoints:
                self._checkpoints[execution_id] = []

            self._checkpoints[execution_id].append(chk)
            self._all_checkpoints[chk.checkpoint_id] = chk
            return chk

    def get_latest_checkpoint(self, execution_id: str) -> Optional[ExecutionCheckpoint]:
        """Fetch the latest ExecutionCheckpoint for execution_id.

        Args:
            execution_id: Execution identifier.

        Returns:
            ExecutionCheckpoint or None if no checkpoints exist.
        """
        with self._lock:
            chks = self._checkpoints.get(execution_id, [])
            return chks[-1] if chks else None

    def get_checkpoint_by_id(self, checkpoint_id: str) -> Optional[ExecutionCheckpoint]:
        """Fetch checkpoint by checkpoint_id."""
        with self._lock:
            return self._all_checkpoints.get(checkpoint_id)

    def list_checkpoints(self, execution_id: str) -> List[ExecutionCheckpoint]:
        """List all checkpoints for execution_id."""
        with self._lock:
            return list(self._checkpoints.get(execution_id, []))

    def count_checkpoints(self) -> int:
        """Count total checkpoints stored."""
        with self._lock:
            return len(self._all_checkpoints)

    def clear(self) -> None:
        """Clear all stored checkpoints."""
        with self._lock:
            self._checkpoints.clear()
            self._all_checkpoints.clear()
