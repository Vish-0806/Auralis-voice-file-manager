"""Recovery Provider for the Auralis Execution Recovery & State Management Runtime (Phase 12.8).

Aggregates CheckpointManager, StateStore, RecoveryEngine, and RollbackManager into a unified, thread-safe gateway provider.
"""

from datetime import datetime, timezone
import logging
import threading
import time
from typing import Any, Dict, List, Optional

from brain.execution.recovery.interfaces import (
    ICheckpointManager,
    IRecoveryEngine,
    IRecoveryProvider,
    IRollbackManager,
    IStateStore,
)
from brain.execution.recovery.checkpoint_manager import CheckpointManager
from brain.execution.recovery.recovery_engine import RecoveryEngine
from brain.execution.recovery.recovery_models import (
    CheckpointType,
    ExecutionCheckpoint,
    RecoveryExecution,
    RecoveryHealth,
    RecoveryStatus,
    RecoveryStatistics,
    RecoveryStrategy,
    RollbackExecution,
    RollbackStatus,
    SnapshotType,
    StateSnapshot,
)
from brain.execution.recovery.rollback_manager import RollbackManager
from brain.execution.recovery.state_store import StateStore

logger = logging.getLogger(__name__)


class RecoveryProvider(IRecoveryProvider):
    """Thread-safe provider aggregating checkpoint manager, state store, recovery engine, and rollback manager."""

    def __init__(
        self,
        checkpoint_manager: Optional[ICheckpointManager] = None,
        state_store: Optional[IStateStore] = None,
        recovery_engine: Optional[IRecoveryEngine] = None,
        rollback_manager: Optional[IRollbackManager] = None,
    ) -> None:
        """Initializes RecoveryProvider with injected or default components."""
        self._lock = threading.RLock()
        self._checkpoint_manager = checkpoint_manager or CheckpointManager()
        self._state_store = state_store or StateStore()
        self._recovery_engine = recovery_engine or RecoveryEngine(
            checkpoint_manager=self._checkpoint_manager,
            state_store=self._state_store,
        )
        self._rollback_manager = rollback_manager or RollbackManager(
            checkpoint_manager=self._checkpoint_manager,
        )

        self._total_recoveries = 0
        self._successful_recoveries = 0
        self._failed_recoveries = 0
        self._total_rollbacks = 0
        self._successful_rollbacks = 0

    def create_checkpoint(
        self,
        execution_id: str,
        state_data: Dict[str, Any],
        checkpoint_type: CheckpointType = CheckpointType.AUTOMATIC,
        step_index: int = 0,
    ) -> ExecutionCheckpoint:
        """Create and store execution checkpoint."""
        return self._checkpoint_manager.create_checkpoint(
            execution_id=execution_id,
            checkpoint_type=checkpoint_type,
            state_data=state_data,
            step_index=step_index,
        )

    def get_latest_checkpoint(self, execution_id: str) -> Optional[ExecutionCheckpoint]:
        """Fetch latest checkpoint for execution_id."""
        return self._checkpoint_manager.get_latest_checkpoint(execution_id)

    def save_snapshot(
        self,
        execution_id: str,
        context_data: Dict[str, Any],
        snapshot_type: SnapshotType = SnapshotType.FULL,
    ) -> StateSnapshot:
        """Save a state snapshot."""
        return self._state_store.save_snapshot(
            execution_id=execution_id,
            context_data=context_data,
            snapshot_type=snapshot_type,
        )

    def recover_execution(
        self,
        execution_id: str,
        strategy: RecoveryStrategy = RecoveryStrategy.RESUME_CHECKPOINT,
    ) -> RecoveryExecution:
        """Recover a failed execution context.

        Args:
            execution_id: Execution identifier.
            strategy: RecoveryStrategy enum.

        Returns:
            RecoveryExecution model.
        """
        plan = self._recovery_engine.plan_recovery(
            execution_id=execution_id,
            strategy=strategy,
        )
        result = self._recovery_engine.execute_recovery(plan)

        with self._lock:
            self._total_recoveries += 1
            if result.status == RecoveryStatus.SUCCESS:
                self._successful_recoveries += 1
            else:
                self._failed_recoveries += 1

        return result

    def rollback_execution(
        self,
        execution_id: str,
        target_checkpoint_id: str,
    ) -> RollbackExecution:
        """Rollback execution state to target checkpoint.

        Args:
            execution_id: Execution identifier.
            target_checkpoint_id: Checkpoint ID to roll back to.

        Returns:
            RollbackExecution model.
        """
        plan = self._rollback_manager.plan_rollback(
            execution_id=execution_id,
            target_checkpoint_id=target_checkpoint_id,
        )
        result = self._rollback_manager.execute_rollback(plan)

        with self._lock:
            self._total_rollbacks += 1
            if result.status == RollbackStatus.COMPLETED:
                self._successful_rollbacks += 1

        return result

    def health_check(self) -> RecoveryHealth:
        """Report component health statuses."""
        with self._lock:
            registered = {
                "CheckpointManager": self._checkpoint_manager is not None,
                "StateStore": self._state_store is not None,
                "RecoveryEngine": self._recovery_engine is not None,
                "RollbackManager": self._rollback_manager is not None,
            }
            all_ok = all(registered.values())

            return RecoveryHealth(
                status="READY" if all_ok else "ERROR",
                healthy=all_ok,
                components=registered,
                statistics=self.get_statistics().model_dump(),
                detected_issues=[] if all_ok else ["One or more recovery sub-components are unavailable"],
                metadata={"thread_safety": "PROTECTED"},
            )

    def get_statistics(self) -> RecoveryStatistics:
        """Return snapshot of aggregate recovery statistics."""
        with self._lock:
            chks_count = getattr(self._checkpoint_manager, "count_checkpoints", lambda: 0)()
            return RecoveryStatistics(
                total_checkpoints=chks_count,
                total_recoveries=self._total_recoveries,
                successful_recoveries=self._successful_recoveries,
                failed_recoveries=self._failed_recoveries,
                total_rollbacks=self._total_rollbacks,
                successful_rollbacks=self._successful_rollbacks,
                metadata={"thread_safety": "PROTECTED"},
            )

    def clear(self) -> None:
        """Clear recovery provider state."""
        with self._lock:
            self._total_recoveries = 0
            self._successful_recoveries = 0
            self._failed_recoveries = 0
            self._total_rollbacks = 0
            self._successful_rollbacks = 0
            if hasattr(self._checkpoint_manager, "clear"):
                self._checkpoint_manager.clear()
            if hasattr(self._state_store, "clear"):
                self._state_store.clear()
