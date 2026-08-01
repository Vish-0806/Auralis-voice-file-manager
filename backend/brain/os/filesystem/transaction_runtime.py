"""Filesystem Transaction Runtime implementation (Phase 11.2).

Provides thread-safe transaction logging, operation recording, commit, abort,
and integration with Phase 9.5 transaction & rollback engines.
"""

from datetime import datetime, timezone
import os
import shutil
import threading

from typing import Any, Dict, Optional
import uuid

from brain.filesystem.rollback_manager import RollbackManager
from brain.filesystem.transaction_manager import TransactionManager
from brain.os.filesystem.exceptions import TransactionError
from brain.os.filesystem.filesystem_models import OperationStatus, TransactionRecord
from brain.os.filesystem.interfaces import IFilesystemTransactionRuntime


class FilesystemTransactionRuntime(IFilesystemTransactionRuntime):
    """Thread-safe transaction tracking and rollback coordinator."""

    def __init__(
        self,
        transaction_manager: Optional[TransactionManager] = None,
        rollback_manager: Optional[RollbackManager] = None,
    ) -> None:
        self._lock = threading.RLock()
        self._tx_manager = transaction_manager or TransactionManager()
        self._rollback_manager = rollback_manager or RollbackManager()
        self._active_records: Dict[str, Dict[str, Any]] = {}

    def begin_transaction(self) -> str:
        """Begin a new transaction and return transaction ID."""
        with self._lock:
            tx_id = f"tx_{uuid.uuid4().hex[:12]}"
            tx_record = {
                "transaction_id": tx_id,
                "status": OperationStatus.PENDING,
                "operations": [],
                "created_at": datetime.now(timezone.utc),
                "committed_at": None,
                "rolled_back_at": None,
                "error": None,
            }
            self._active_records[tx_id] = tx_record
            try:
                self._tx_manager.begin_transaction(tx_id)
            except Exception:
                pass
            return tx_id

    def record_operation(
        self,
        transaction_id: str,
        operation_type: str,
        source_path: str,
        target_path: Optional[str] = None,
        backup_path: Optional[str] = None,
    ) -> None:
        """Record an operation step under an active transaction."""
        with self._lock:
            if transaction_id not in self._active_records:
                raise TransactionError(f"Transaction {transaction_id} not found")

            rec = self._active_records[transaction_id]
            if rec["status"] != OperationStatus.PENDING and rec["status"] != OperationStatus.RUNNING:
                raise TransactionError(f"Transaction {transaction_id} is not active")

            rec["status"] = OperationStatus.RUNNING
            op_data = {
                "operation_type": operation_type,
                "source_path": source_path,
                "target_path": target_path,
                "backup_path": backup_path,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            rec["operations"].append(op_data)

    def commit_transaction(self, transaction_id: str) -> TransactionRecord:
        """Commit an active transaction."""
        with self._lock:
            if transaction_id not in self._active_records:
                raise TransactionError(f"Transaction {transaction_id} not found")

            rec = self._active_records[transaction_id]
            rec["status"] = OperationStatus.SUCCESS
            rec["committed_at"] = datetime.now(timezone.utc)

            # Cleanup backup files if any
            for op in rec["operations"]:
                b_path = op.get("backup_path")
                if b_path and os.path.exists(b_path):
                    try:
                        if os.path.isdir(b_path):
                            shutil.rmtree(b_path)
                        else:
                            os.remove(b_path)
                    except Exception:
                        pass

            try:
                self._tx_manager.commit_transaction(transaction_id)
            except Exception:
                pass

            return TransactionRecord(
                transaction_id=rec["transaction_id"],
                status=rec["status"],
                operations=rec["operations"],
                created_at=rec["created_at"],
                committed_at=rec["committed_at"],
                rolled_back_at=rec["rolled_back_at"],
                error=rec["error"],
            )

    def abort_transaction(self, transaction_id: str) -> TransactionRecord:
        """Abort and rollback an active transaction."""
        with self._lock:
            if transaction_id not in self._active_records:
                raise TransactionError(f"Transaction {transaction_id} not found")

            rec = self._active_records[transaction_id]
            rec["status"] = OperationStatus.ROLLED_BACK
            rec["rolled_back_at"] = datetime.now(timezone.utc)

            # Perform reverse rollback of recorded operations
            for op in reversed(rec["operations"]):
                op_type = op.get("operation_type")
                src = op.get("source_path")
                dst = op.get("target_path")
                b_path = op.get("backup_path")

                try:
                    if op_type == "delete_file" and b_path and os.path.exists(b_path):
                        shutil.copy2(b_path, src)
                    elif op_type in ("write_text", "write_bytes") and b_path and os.path.exists(b_path):
                        shutil.copy2(b_path, src)
                    elif op_type == "move_file" and dst and os.path.exists(dst):
                        shutil.move(dst, src)
                except Exception as e:
                    rec["error"] = f"Rollback error: {e}"

            try:
                self._tx_manager.abort_transaction(transaction_id)
            except Exception:
                pass

            return TransactionRecord(
                transaction_id=rec["transaction_id"],
                status=rec["status"],
                operations=rec["operations"],
                created_at=rec["created_at"],
                committed_at=rec["committed_at"],
                rolled_back_at=rec["rolled_back_at"],
                error=rec["error"],
            )

    def get_transaction(self, transaction_id: str) -> Optional[TransactionRecord]:
        """Retrieve details of a transaction by ID."""
        with self._lock:
            rec = self._active_records.get(transaction_id)
            if rec is None:
                return None
            return TransactionRecord(
                transaction_id=rec["transaction_id"],
                status=rec["status"],
                operations=rec["operations"],
                created_at=rec["created_at"],
                committed_at=rec["committed_at"],
                rolled_back_at=rec["rolled_back_at"],
                error=rec["error"],
            )
