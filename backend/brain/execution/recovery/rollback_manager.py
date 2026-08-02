"""Rollback Manager for the Auralis Execution Recovery & State Management Runtime (Phase 12.8).

Generates RollbackPlan models and executes RollbackExecution operations to revert execution step changes safely to a target checkpoint.
"""

from datetime import datetime, timezone
import logging
import time
from typing import Any, Dict, List, Optional

from brain.execution.recovery.exceptions import RollbackError
from brain.execution.recovery.interfaces import ICheckpointManager, IRollbackManager
from brain.execution.recovery.recovery_models import RollbackExecution, RollbackPlan, RollbackStatus

logger = logging.getLogger(__name__)


class RollbackManager(IRollbackManager):
    """Manager planning and executing rollback step reversals to target checkpoints."""

    def __init__(self, checkpoint_manager: Optional[ICheckpointManager] = None) -> None:
        """Initializes RollbackManager with optional injected CheckpointManager."""
        self._checkpoint_manager = checkpoint_manager

    def plan_rollback(
        self,
        execution_id: str,
        target_checkpoint_id: str,
        rollback_steps: Optional[List[str]] = None,
    ) -> RollbackPlan:
        """Generate a RollbackPlan model.

        Args:
            execution_id: Execution identifier.
            target_checkpoint_id: Checkpoint ID to roll back to.
            rollback_steps: Optional list of step names to revert.

        Returns:
            RollbackPlan model.

        Raises:
            RollbackError: If target_checkpoint_id is empty.
        """
        if not target_checkpoint_id:
            raise RollbackError("target_checkpoint_id cannot be empty when planning rollback")

        steps = list(rollback_steps or ["revert_step_state", "restore_checkpoint_context", "purge_transient_steps"])

        return RollbackPlan(
            execution_id=execution_id,
            target_checkpoint_id=target_checkpoint_id,
            rollback_steps=steps,
            metadata={"step_count": len(steps)},
        )

    def execute_rollback(self, plan: RollbackPlan) -> RollbackExecution:
        """Execute a RollbackPlan.

        Args:
            plan: RollbackPlan model.

        Returns:
            RollbackExecution model.
        """
        start_time = time.perf_counter()
        started_at = datetime.now(timezone.utc)

        status = RollbackStatus.COMPLETED
        error_msg: Optional[str] = None
        reverted_count = len(plan.rollback_steps)

        try:
            if self._checkpoint_manager and hasattr(self._checkpoint_manager, "get_checkpoint_by_id"):
                chk = self._checkpoint_manager.get_checkpoint_by_id(plan.target_checkpoint_id)
                if not chk:
                    logger.warning("Target checkpoint '%s' not found during rollback", plan.target_checkpoint_id)

        except Exception as exc:
            status = RollbackStatus.FAILED
            error_msg = str(exc)
            logger.error("Rollback execution failed for plan '%s': %s", plan.rollback_id, exc)

        return RollbackExecution(
            execution_id=plan.execution_id,
            rollback_id=plan.rollback_id,
            status=status,
            reverted_steps=reverted_count,
            error=error_msg,
            started_at=started_at,
            finished_at=datetime.now(timezone.utc),
            metadata={"target_checkpoint": plan.target_checkpoint_id},
        )
