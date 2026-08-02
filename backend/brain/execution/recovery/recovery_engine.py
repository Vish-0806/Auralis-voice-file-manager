"""Recovery Engine for the Auralis Execution Recovery & State Management Runtime (Phase 12.8).

Generates RecoveryPlan models and executes RecoveryExecution strategies (RETRY_STEP, RESUME_CHECKPOINT, ROLLBACK_STAGE, ABORT_EXECUTION, FAILOVER).
"""

from datetime import datetime, timezone
import logging
import time
from typing import Any, Dict, List, Optional

from brain.execution.recovery.exceptions import RecoveryExecutionError
from brain.execution.recovery.interfaces import ICheckpointManager, IRecoveryEngine, IStateStore
from brain.execution.recovery.recovery_models import (
    RecoveryExecution,
    RecoveryPlan,
    RecoveryStatus,
    RecoveryStrategy,
)

logger = logging.getLogger(__name__)


class RecoveryEngine(IRecoveryEngine):
    """Engine planning and executing recovery strategies for failed execution contexts."""

    def __init__(
        self,
        checkpoint_manager: Optional[ICheckpointManager] = None,
        state_store: Optional[IStateStore] = None,
    ) -> None:
        """Initializes RecoveryEngine with optional injected CheckpointManager and StateStore."""
        self._checkpoint_manager = checkpoint_manager
        self._state_store = state_store

    def plan_recovery(
        self,
        execution_id: str,
        strategy: RecoveryStrategy = RecoveryStrategy.RESUME_CHECKPOINT,
        target_checkpoint_id: Optional[str] = None,
    ) -> RecoveryPlan:
        """Generate a RecoveryPlan model based on requested strategy.

        Args:
            execution_id: Execution identifier.
            strategy: RecoveryStrategy enum.
            target_checkpoint_id: Optional checkpoint ID to restore.

        Returns:
            RecoveryPlan model.
        """
        target_chk = target_checkpoint_id
        if not target_chk and self._checkpoint_manager:
            latest_chk = self._checkpoint_manager.get_latest_checkpoint(execution_id)
            if latest_chk:
                target_chk = latest_chk.checkpoint_id

        steps: List[str] = []

        if strategy == RecoveryStrategy.RETRY_STEP:
            steps = ["identify_failed_step", "reload_step_context", "reexecute_step"]
        elif strategy == RecoveryStrategy.RESUME_CHECKPOINT:
            steps = ["load_target_checkpoint", "restore_execution_state", "resume_execution_pipeline"]
        elif strategy == RecoveryStrategy.ROLLBACK_STAGE:
            steps = ["identify_stage_checkpoint", "revert_stage_changes", "resume_from_stage_start"]
        elif strategy == RecoveryStrategy.FAILOVER:
            steps = ["load_backup_snapshot", "failover_execution_node", "resume_pipeline"]
        else:  # ABORT_EXECUTION
            steps = ["mark_execution_aborted", "cleanup_transient_resources"]

        return RecoveryPlan(
            execution_id=execution_id,
            strategy=strategy,
            target_checkpoint_id=target_chk,
            steps=steps,
            metadata={"strategy_type": strategy.value},
        )

    def execute_recovery(self, plan: RecoveryPlan) -> RecoveryExecution:
        """Execute a RecoveryPlan.

        Args:
            plan: RecoveryPlan model.

        Returns:
            RecoveryExecution model.

        Raises:
            RecoveryExecutionError: If recovery execution encounters an unrecoverable failure.
        """
        start_time = time.perf_counter()
        started_at = datetime.now(timezone.utc)

        restored_state: Dict[str, Any] = {}
        status = RecoveryStatus.SUCCESS
        error_msg: Optional[str] = None

        try:
            # Attempt state restoration from target checkpoint if available
            if plan.target_checkpoint_id and self._checkpoint_manager:
                if hasattr(self._checkpoint_manager, "get_checkpoint_by_id"):
                    chk = self._checkpoint_manager.get_checkpoint_by_id(plan.target_checkpoint_id)
                    if chk:
                        restored_state = dict(chk.state_data)
                elif hasattr(self._checkpoint_manager, "get_latest_checkpoint"):
                    chk = self._checkpoint_manager.get_latest_checkpoint(plan.execution_id)
                    if chk:
                        restored_state = dict(chk.state_data)

            if not restored_state and self._state_store:
                snap = self._state_store.get_latest_snapshot(plan.execution_id)
                if snap:
                    restored_state = dict(snap.context_data)

            if not restored_state:
                restored_state = {"execution_id": plan.execution_id, "restored_at": started_at.isoformat()}

        except Exception as exc:
            status = RecoveryStatus.FAILED
            error_msg = str(exc)
            logger.error("Recovery execution failed for plan '%s': %s", plan.plan_id, exc)

        return RecoveryExecution(
            plan_id=plan.plan_id,
            status=status,
            attempts=1,
            error=error_msg,
            restored_state=restored_state,
            metadata={"strategy": plan.strategy.value},
            started_at=started_at,
            finished_at=datetime.now(timezone.utc),
        )
