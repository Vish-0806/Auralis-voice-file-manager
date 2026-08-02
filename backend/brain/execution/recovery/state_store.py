"""State Store for the Auralis Execution Recovery & State Management Runtime (Phase 12.8).

Responsible for storing, updating, and querying state snapshots per execution_id.
"""

from datetime import datetime, timezone
import threading
from typing import Any, Dict, List, Optional

from brain.execution.recovery.exceptions import StateStoreError
from brain.execution.recovery.interfaces import IStateStore
from brain.execution.recovery.recovery_models import SnapshotType, StateSnapshot


class StateStore(IStateStore):
    """Thread-safe state store storing StateSnapshot models."""

    def __init__(self) -> None:
        """Initializes StateStore with internal snapshot map."""
        self._lock = threading.RLock()
        self._snapshots: Dict[str, List[StateSnapshot]] = {}

    def save_snapshot(
        self,
        execution_id: str,
        context_data: Dict[str, Any],
        snapshot_type: SnapshotType = SnapshotType.FULL,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> StateSnapshot:
        """Save a StateSnapshot.

        Args:
            execution_id: Execution identifier.
            context_data: Execution state context dictionary.
            snapshot_type: SnapshotType enum (FULL, DELTA, INCREMENTAL).
            metadata: Optional metadata dictionary.

        Returns:
            StateSnapshot model.

        Raises:
            StateStoreError: If execution_id is empty.
        """
        if not execution_id:
            raise StateStoreError("execution_id cannot be empty when saving snapshot")

        with self._lock:
            snapshot = StateSnapshot(
                execution_id=execution_id,
                snapshot_type=snapshot_type,
                context_data=dict(context_data or {}),
                metadata=dict(metadata or {}),
                created_at=datetime.now(timezone.utc),
            )

            if execution_id not in self._snapshots:
                self._snapshots[execution_id] = []

            self._snapshots[execution_id].append(snapshot)
            return snapshot

    def get_latest_snapshot(self, execution_id: str) -> Optional[StateSnapshot]:
        """Fetch latest StateSnapshot for execution_id.

        Args:
            execution_id: Execution identifier.

        Returns:
            StateSnapshot or None if not found.
        """
        with self._lock:
            snaps = self._snapshots.get(execution_id, [])
            return snaps[-1] if snaps else None

    def list_snapshots(self, execution_id: str) -> List[StateSnapshot]:
        """List all snapshots for execution_id."""
        with self._lock:
            return list(self._snapshots.get(execution_id, []))

    def clear(self) -> None:
        """Clear all stored state snapshots."""
        with self._lock:
            self._snapshots.clear()
