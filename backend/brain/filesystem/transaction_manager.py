"""Transaction Manager for the Auralis Filesystem Engine (Phase 9.5).

Provides thread-safe, isolated filesystem transactions with rollback plan generation.
Does NOT execute filesystem operations directly — delegates to FileOperations /
DirectoryOperations via FilesystemProvider during commit.
"""

import logging
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional

from brain.filesystem.filesystem_models import (
    FilesystemOperation,
    OperationResult,
    OperationStatus,
    Transaction,
    TransactionResult,
    TransactionStatus,
)

logger = logging.getLogger(__name__)

# Executor type: takes a FilesystemOperation and returns an OperationResult
OperationExecutor = Callable[[FilesystemOperation], OperationResult]


class TransactionManager:
    """Thread-safe filesystem transaction coordinator.

    Responsibilities:
    - ``begin()``: Open a new transaction context.
    - ``record_operation()``: Append an operation to the transaction log.
    - ``commit()``: Execute all operations and return a :class:`TransactionResult`.
    - ``abort()``: Mark a transaction as aborted without executing operations.
    - Nested transaction support via ``parent_transaction_id``.
    - Isolation: each transaction ID maintains its own private operation list.
    """

    def __init__(self, executor: Optional[OperationExecutor] = None) -> None:
        """Initializes TransactionManager.

        Args:
            executor: Optional callable that executes a ``FilesystemOperation``
                      and returns an ``OperationResult``.  If not provided a
                      default no-op stub is used (primarily for testing).
        """
        self._lock = threading.RLock()
        self._transactions: Dict[str, _TransactionState] = {}
        self._executor: OperationExecutor = executor or _noop_executor
        logger.debug("TransactionManager initialized")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def begin(
        self,
        transaction_id: Optional[str] = None,
        parent_transaction_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> Transaction:
        """Open a new transaction.

        Args:
            transaction_id: Optional explicit ID.  Auto-generated if omitted.
            parent_transaction_id: Parent transaction for nested transactions.
            metadata: Optional metadata to attach.

        Returns:
            Immutable :class:`Transaction` snapshot.

        Raises:
            ValueError: If *transaction_id* already exists and is still open.
        """
        with self._lock:
            tx_id = transaction_id or _new_id()

            if tx_id in self._transactions and self._transactions[tx_id].status == TransactionStatus.OPEN:
                raise ValueError(f"Transaction '{tx_id}' is already open")

            state = _TransactionState(
                transaction_id=tx_id,
                parent_transaction_id=parent_transaction_id,
                metadata=metadata or {},
            )
            self._transactions[tx_id] = state
            logger.info("Transaction Started: transaction_id=%s", tx_id)
            return state.to_snapshot()

    def record_operation(
        self,
        transaction_id: str,
        operation: FilesystemOperation,
    ) -> bool:
        """Append *operation* to an open transaction's log.

        Args:
            transaction_id: Target transaction ID.
            operation: Operation to record.

        Returns:
            True if recorded successfully, False if transaction not found or not open.
        """
        with self._lock:
            state = self._transactions.get(transaction_id)
            if state is None or state.status != TransactionStatus.OPEN:
                logger.warning(
                    "TransactionManager.record_operation: transaction '%s' not found or not open",
                    transaction_id,
                )
                return False

            state.operations.append(operation)
            logger.debug(
                "Operation recorded in transaction=%s type=%s",
                transaction_id,
                operation.operation_type,
            )
            return True

    def commit(self, transaction_id: str) -> TransactionResult:
        """Execute all operations in the transaction and return the result.

        Args:
            transaction_id: Transaction to commit.

        Returns:
            Immutable :class:`TransactionResult`.
        """
        with self._lock:
            state = self._transactions.get(transaction_id)
            if state is None:
                return _make_result(transaction_id, TransactionStatus.FAILED,
                                    [], f"Transaction '{transaction_id}' not found")

            if state.status != TransactionStatus.OPEN:
                return _make_result(transaction_id, TransactionStatus.FAILED,
                                    [], f"Transaction '{transaction_id}' is not open (status={state.status})")

            state.status = TransactionStatus.COMMITTING
            started = datetime.now(timezone.utc)
            t0 = time.monotonic()
            logger.info("Transaction Started commit: transaction_id=%s ops=%d", transaction_id, len(state.operations))

        op_results: List[OperationResult] = []
        completed = 0
        failed = 0
        commit_error: Optional[str] = None

        for op in state.operations:
            try:
                result = self._executor(op)
                op_results.append(result)
                if result.status == OperationStatus.COMPLETED or result.status == OperationStatus.SKIPPED:
                    completed += 1
                else:
                    failed += 1
                    commit_error = result.error or "Operation failed"
                    break
            except Exception as exc:
                failed += 1
                commit_error = str(exc)
                op_results.append(OperationResult(
                    operation_id=op.operation_id,
                    operation_type=op.operation_type,
                    status=OperationStatus.FAILED,
                    source_path=op.source_path,
                    destination_path=op.destination_path,
                    error=str(exc),
                ))
                break

        final_status = TransactionStatus.COMMITTED if not commit_error else TransactionStatus.FAILED
        duration = (time.monotonic() - t0) * 1000

        with self._lock:
            state.status = final_status
            state.operation_results = op_results

        if final_status == TransactionStatus.COMMITTED:
            logger.info("Transaction Committed: transaction_id=%s completed=%d", transaction_id, completed)
        else:
            logger.error("Transaction Failed: transaction_id=%s error=%s", transaction_id, commit_error)

        return TransactionResult(
            transaction_id=transaction_id,
            status=final_status,
            operation_results=op_results,
            completed_operations=completed,
            failed_operations=failed,
            duration_ms=duration,
            error=commit_error,
            started_at=started,
            finished_at=datetime.now(timezone.utc),
            metadata=dict(state.metadata),
        )

    def abort(self, transaction_id: str) -> TransactionResult:
        """Mark a transaction as aborted without executing any operations.

        Args:
            transaction_id: Transaction to abort.

        Returns:
            Immutable :class:`TransactionResult`.
        """
        with self._lock:
            state = self._transactions.get(transaction_id)
            if state is None:
                return _make_result(transaction_id, TransactionStatus.ABORTED, [],
                                    f"Transaction '{transaction_id}' not found")

            state.status = TransactionStatus.ABORTED
            logger.info("Transaction Rolled Back (aborted): transaction_id=%s", transaction_id)
            return _make_result(transaction_id, TransactionStatus.ABORTED, [],
                                None, dict(state.metadata))

    def get_transaction(self, transaction_id: str) -> Optional[Transaction]:
        """Return a snapshot of the transaction, or None if not found.

        Args:
            transaction_id: Transaction ID to look up.

        Returns:
            Immutable :class:`Transaction` or None.
        """
        with self._lock:
            state = self._transactions.get(transaction_id)
            return state.to_snapshot() if state else None

    def list_transactions(self) -> List[str]:
        """Return a list of all known transaction IDs.

        Returns:
            List of transaction ID strings.
        """
        with self._lock:
            return list(self._transactions.keys())

    def clear(self) -> None:
        """Remove all closed/aborted/committed transactions from memory.

        Open transactions are preserved.
        """
        with self._lock:
            closed = [k for k, v in self._transactions.items()
                      if v.status != TransactionStatus.OPEN]
            for key in closed:
                del self._transactions[key]
            logger.debug("TransactionManager.clear: removed %d closed transactions", len(closed))

    def set_executor(self, executor: OperationExecutor) -> None:
        """Replace the operation executor (useful for testing or hot-swapping).

        Args:
            executor: New callable executor.
        """
        with self._lock:
            self._executor = executor


# ---------------------------------------------------------------------------
# Internal State
# ---------------------------------------------------------------------------

class _TransactionState:
    """Mutable internal state for an active transaction."""

    def __init__(
        self,
        transaction_id: str,
        parent_transaction_id: Optional[str],
        metadata: Dict,
    ) -> None:
        self.transaction_id = transaction_id
        self.parent_transaction_id = parent_transaction_id
        self.status: TransactionStatus = TransactionStatus.OPEN
        self.operations: List[FilesystemOperation] = []
        self.operation_results: List[OperationResult] = []
        self.metadata: Dict = metadata
        self.created_at: datetime = datetime.now(timezone.utc)

    def to_snapshot(self) -> Transaction:
        return Transaction(
            transaction_id=self.transaction_id,
            status=self.status,
            operations=list(self.operations),
            parent_transaction_id=self.parent_transaction_id,
            created_at=self.created_at,
            metadata=dict(self.metadata),
        )


# ---------------------------------------------------------------------------
# Private Utilities
# ---------------------------------------------------------------------------

def _new_id() -> str:
    return f"tx-{uuid.uuid4().hex[:8]}"


def _noop_executor(op: FilesystemOperation) -> OperationResult:
    """Default no-op executor used when no real executor is injected."""
    return OperationResult(
        operation_id=op.operation_id,
        operation_type=op.operation_type,
        status=OperationStatus.COMPLETED,
        source_path=op.source_path,
        destination_path=op.destination_path,
    )


def _make_result(
    transaction_id: str,
    status: TransactionStatus,
    op_results: List[OperationResult],
    error: Optional[str],
    metadata: Optional[Dict] = None,
) -> TransactionResult:
    now = datetime.now(timezone.utc)
    return TransactionResult(
        transaction_id=transaction_id,
        status=status,
        operation_results=op_results,
        completed_operations=sum(1 for r in op_results if r.status == OperationStatus.COMPLETED),
        failed_operations=sum(1 for r in op_results if r.status == OperationStatus.FAILED),
        error=error,
        started_at=now,
        finished_at=now,
        metadata=metadata or {},
    )
