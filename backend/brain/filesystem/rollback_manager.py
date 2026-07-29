"""Rollback Manager for the Auralis Filesystem Engine (Phase 9.5).

Provides thread-safe, deterministic rollback of completed filesystem transactions.
Inverts each completed operation in reverse order.
Does NOT perform reasoning, planning, or session management.
"""

import logging
import os
import shutil
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from brain.filesystem.filesystem_models import (
    FilesystemOperationType,
    OperationResult,
    OperationStatus,
    RollbackOperation,
    RollbackResult,
    TransactionResult,
    TransactionStatus,
)

logger = logging.getLogger(__name__)


class RollbackManager:
    """Thread-safe rollback executor for filesystem transactions.

    Inverts each :class:`OperationResult` from a :class:`TransactionResult`
    in reverse order.  Partial rollback is supported: if one rollback step
    fails the manager continues with the remaining steps unless
    ``stop_on_failure`` is True.
    """

    def __init__(self, stop_on_failure: bool = False) -> None:
        """Initializes RollbackManager.

        Args:
            stop_on_failure: If True, abort remaining rollback steps on first failure.
        """
        self._lock = threading.RLock()
        self._stop_on_failure = stop_on_failure
        logger.debug("RollbackManager initialized stop_on_failure=%s", stop_on_failure)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def rollback(self, transaction_result: TransactionResult) -> RollbackResult:
        """Roll back all successfully completed operations in *transaction_result*.

        Operations are reversed in **reverse** execution order.

        Args:
            transaction_result: Completed (or partially-failed) transaction.

        Returns:
            Immutable :class:`RollbackResult`.
        """
        with self._lock:
            tx_id = transaction_result.transaction_id
            started = datetime.now(timezone.utc)
            t0 = time.monotonic()
            logger.info("Rollback Started: transaction_id=%s", tx_id)

            # Build rollback plan from completed operations in reverse order
            rollback_ops = self._build_rollback_plan(transaction_result)

            op_results: List[OperationResult] = []
            completed = 0
            failed = 0
            partial = False

            for rb_op in rollback_ops:
                result = self.rollback_operation(rb_op)
                op_results.append(result)
                if result.status == OperationStatus.COMPLETED:
                    completed += 1
                else:
                    failed += 1
                    partial = True
                    if self._stop_on_failure:
                        break

            duration = (time.monotonic() - t0) * 1000
            overall_status = (
                OperationStatus.COMPLETED if failed == 0
                else (OperationStatus.FAILED if completed == 0 else OperationStatus.FAILED)
            )

            logger.info(
                "Rollback Completed: transaction_id=%s completed=%d failed=%d",
                tx_id, completed, failed,
            )
            return RollbackResult(
                transaction_id=tx_id,
                status=overall_status,
                rollback_operations=rollback_ops,
                operation_results=op_results,
                completed_rollbacks=completed,
                failed_rollbacks=failed,
                partial=partial,
                duration_ms=duration,
                started_at=started,
                finished_at=datetime.now(timezone.utc),
            )

    def rollback_operation(self, rollback_op: RollbackOperation) -> OperationResult:
        """Execute a single rollback operation.

        Args:
            rollback_op: The inverse operation to execute.

        Returns:
            Immutable :class:`OperationResult`.
        """
        op_id = rollback_op.rollback_id or _new_id()
        started = datetime.now(timezone.utc)
        t0 = time.monotonic()
        op_type = rollback_op.operation_type

        try:
            result = self._dispatch_rollback(rollback_op)
            duration = (time.monotonic() - t0) * 1000
            return OperationResult(
                operation_id=op_id,
                operation_type=op_type,
                status=OperationStatus.COMPLETED if result else OperationStatus.FAILED,
                source_path=rollback_op.source_path,
                destination_path=rollback_op.destination_path,
                error=None if result else "Rollback dispatch returned False",
                duration_ms=duration,
                started_at=started,
                finished_at=datetime.now(timezone.utc),
            )
        except Exception as exc:
            duration = (time.monotonic() - t0) * 1000
            logger.error("Rollback operation failed op_id=%s error=%s", op_id, exc)
            return OperationResult(
                operation_id=op_id,
                operation_type=op_type,
                status=OperationStatus.FAILED,
                source_path=rollback_op.source_path,
                destination_path=rollback_op.destination_path,
                error=str(exc),
                duration_ms=duration,
                started_at=started,
                finished_at=datetime.now(timezone.utc),
            )

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    def _build_rollback_plan(self, transaction_result: TransactionResult) -> List[RollbackOperation]:
        """Build an ordered list of inverse operations from the transaction result.

        Only COMPLETED (and SKIPPED) operations need rollback.
        Operations are processed in reverse order.

        Args:
            transaction_result: Completed transaction result.

        Returns:
            Ordered list of :class:`RollbackOperation` objects.
        """
        rollback_ops: List[RollbackOperation] = []

        # Reverse to undo in LIFO order
        completed_results = [
            r for r in transaction_result.operation_results
            if r.status in (OperationStatus.COMPLETED,)
        ]

        for result in reversed(completed_results):
            inverse = self._invert_operation(result)
            if inverse is not None:
                rollback_ops.append(inverse)

        return rollback_ops

    def _invert_operation(self, result: OperationResult) -> Optional[RollbackOperation]:
        """Return the inverse rollback operation for a completed result.

        Args:
            result: Original operation result.

        Returns:
            :class:`RollbackOperation` or None if not invertible.
        """
        op_type = result.operation_type
        rb_id = _new_id()

        # COPY → DELETE the destination
        if op_type == FilesystemOperationType.COPY:
            if result.destination_path:
                return RollbackOperation(
                    rollback_id=rb_id,
                    original_operation_id=result.operation_id,
                    operation_type=FilesystemOperationType.ROLLBACK,
                    source_path=result.destination_path,
                    parameters={"rollback_type": "delete_copy"},
                )

        # MOVE → MOVE back (swap source/destination)
        elif op_type == FilesystemOperationType.MOVE:
            if result.destination_path:
                return RollbackOperation(
                    rollback_id=rb_id,
                    original_operation_id=result.operation_id,
                    operation_type=FilesystemOperationType.ROLLBACK,
                    source_path=result.destination_path,
                    destination_path=result.source_path,
                    parameters={"rollback_type": "move_back"},
                )

        # RENAME → RENAME back
        elif op_type == FilesystemOperationType.RENAME:
            if result.destination_path:
                original_name = Path(result.source_path).name
                return RollbackOperation(
                    rollback_id=rb_id,
                    original_operation_id=result.operation_id,
                    operation_type=FilesystemOperationType.ROLLBACK,
                    source_path=result.destination_path,
                    destination_path=result.source_path,
                    parameters={"rollback_type": "rename_back", "original_name": original_name},
                )

        # DELETE → cannot restore (log warning)
        elif op_type == FilesystemOperationType.DELETE:
            logger.warning(
                "RollbackManager: cannot restore deleted file %s (no backup available)",
                result.source_path,
            )
            return None

        # CREATE → DELETE the created file
        elif op_type == FilesystemOperationType.CREATE:
            return RollbackOperation(
                rollback_id=rb_id,
                original_operation_id=result.operation_id,
                operation_type=FilesystemOperationType.ROLLBACK,
                source_path=result.source_path,
                parameters={"rollback_type": "delete_created"},
            )

        # COPY_DIRECTORY → DELETE_DIRECTORY the destination
        elif op_type == FilesystemOperationType.COPY_DIRECTORY:
            if result.destination_path:
                return RollbackOperation(
                    rollback_id=rb_id,
                    original_operation_id=result.operation_id,
                    operation_type=FilesystemOperationType.ROLLBACK,
                    source_path=result.destination_path,
                    parameters={"rollback_type": "delete_copied_dir"},
                )

        # MOVE_DIRECTORY → MOVE back
        elif op_type == FilesystemOperationType.MOVE_DIRECTORY:
            if result.destination_path:
                return RollbackOperation(
                    rollback_id=rb_id,
                    original_operation_id=result.operation_id,
                    operation_type=FilesystemOperationType.ROLLBACK,
                    source_path=result.destination_path,
                    destination_path=result.source_path,
                    parameters={"rollback_type": "move_dir_back"},
                )

        # CREATE_DIRECTORY → DELETE_DIRECTORY
        elif op_type == FilesystemOperationType.CREATE_DIRECTORY:
            return RollbackOperation(
                rollback_id=rb_id,
                original_operation_id=result.operation_id,
                operation_type=FilesystemOperationType.ROLLBACK,
                source_path=result.source_path,
                parameters={"rollback_type": "delete_created_dir"},
            )

        return None

    def _dispatch_rollback(self, rb_op: RollbackOperation) -> bool:
        """Execute the physical inverse operation.

        Args:
            rb_op: Rollback operation to execute.

        Returns:
            True on success, False on failure.
        """
        rollback_type = rb_op.parameters.get("rollback_type", "")
        src = Path(rb_op.source_path)
        dst = Path(rb_op.destination_path) if rb_op.destination_path else None

        try:
            # delete_copy / delete_created — delete a file
            if rollback_type in ("delete_copy", "delete_created"):
                if src.exists() and src.is_file():
                    src.unlink()
                return True

            # move_back — move file back to original location
            if rollback_type == "move_back" and dst is not None:
                if src.exists():
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(src), str(dst))
                return True

            # rename_back — rename file back to original name
            if rollback_type == "rename_back" and dst is not None:
                if src.exists():
                    src.rename(dst)
                return True

            # delete_copied_dir — delete a copied directory
            if rollback_type == "delete_copied_dir":
                if src.exists() and src.is_dir():
                    shutil.rmtree(str(src))
                return True

            # move_dir_back — move directory back
            if rollback_type == "move_dir_back" and dst is not None:
                if src.exists() and src.is_dir():
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(src), str(dst))
                return True

            # delete_created_dir — delete a created directory
            if rollback_type == "delete_created_dir":
                if src.exists() and src.is_dir():
                    shutil.rmtree(str(src))
                return True

            logger.warning("RollbackManager: unknown rollback_type='%s'", rollback_type)
            return False

        except Exception as exc:
            logger.error("RollbackManager._dispatch_rollback failed type=%s: %s", rollback_type, exc)
            return False


# ---------------------------------------------------------------------------
# Private Utilities
# ---------------------------------------------------------------------------

def _new_id() -> str:
    return f"rb-{uuid.uuid4().hex[:8]}"
