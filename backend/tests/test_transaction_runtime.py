"""Unit tests for FilesystemTransactionRuntime (Phase 11.2)."""

import pytest
from brain.os.filesystem import (
    FilesystemTransactionRuntime,
    OperationStatus,
    TransactionRecord,
)


def test_transaction_runtime_lifecycle(tmp_path) -> None:
    f_path = tmp_path / "tx_file.txt"
    f_path.write_text("original content")

    b_path = tmp_path / "tx_file.txt.bak"
    b_path.write_text("original content")

    tx_rt = FilesystemTransactionRuntime()
    tx_id = tx_rt.begin_transaction()
    assert isinstance(tx_id, str) and len(tx_id) > 0

    tx_rt.record_operation(
        transaction_id=tx_id,
        operation_type="write_text",
        source_path=str(f_path),
        backup_path=str(b_path),
    )

    f_path.write_text("new mutated content")

    rec = tx_rt.get_transaction(tx_id)
    assert isinstance(rec, TransactionRecord)
    assert rec.status == OperationStatus.RUNNING
    assert len(rec.operations) == 1

    # Abort & Rollback
    aborted_rec = tx_rt.abort_transaction(tx_id)
    assert aborted_rec.status == OperationStatus.ROLLED_BACK
    assert f_path.read_text() == "original content"


def test_transaction_runtime_commit(tmp_path) -> None:
    tx_rt = FilesystemTransactionRuntime()
    tx_id = tx_rt.begin_transaction()

    b_path = tmp_path / "temp.bak"
    b_path.write_text("backup")

    tx_rt.record_operation(
        transaction_id=tx_id,
        operation_type="write_text",
        source_path=str(tmp_path / "file.txt"),
        backup_path=str(b_path),
    )

    committed = tx_rt.commit_transaction(tx_id)
    assert committed.status == OperationStatus.SUCCESS
    assert not b_path.exists()
