"""Unit tests for TransactionManager (Phase 9.5)."""

# pyrefly: ignore [missing-import]
import pytest
from typing import List

from brain.filesystem import TransactionManager, TransactionStatus
from brain.filesystem.filesystem_models import (
    FilesystemOperation,
    FilesystemOperationType,
    OperationResult,
    OperationStatus,
    Transaction,
    TransactionResult,
)


# ---------------------------------------------------------------------------
# Fixtures & Helpers
# ---------------------------------------------------------------------------

def make_op(op_type: FilesystemOperationType = FilesystemOperationType.CREATE,
            source: str = "/tmp/file.txt",
            destination: str = None) -> FilesystemOperation:
    return FilesystemOperation(
        operation_id="op-test",
        operation_type=op_type,
        source_path=source,
        destination_path=destination,
    )


def success_executor(op: FilesystemOperation) -> OperationResult:
    return OperationResult(
        operation_id=op.operation_id,
        operation_type=op.operation_type,
        status=OperationStatus.COMPLETED,
        source_path=op.source_path,
    )


def fail_executor(op: FilesystemOperation) -> OperationResult:
    return OperationResult(
        operation_id=op.operation_id,
        operation_type=op.operation_type,
        status=OperationStatus.FAILED,
        source_path=op.source_path,
        error="Deliberate failure",
    )


@pytest.fixture
def tm() -> TransactionManager:
    return TransactionManager(executor=success_executor)


@pytest.fixture
def tm_fail() -> TransactionManager:
    return TransactionManager(executor=fail_executor)


# ---------------------------------------------------------------------------
# begin()
# ---------------------------------------------------------------------------

def test_begin_returns_transaction(tm: TransactionManager) -> None:
    tx = tm.begin()
    assert isinstance(tx, Transaction)
    assert tx.status == TransactionStatus.OPEN
    assert tx.transaction_id != ""


def test_begin_with_explicit_id(tm: TransactionManager) -> None:
    tx = tm.begin("my-tx-id")
    assert tx.transaction_id == "my-tx-id"


def test_begin_with_parent_id(tm: TransactionManager) -> None:
    parent = tm.begin("parent-tx")
    child = tm.begin("child-tx", parent_transaction_id="parent-tx")
    assert child.parent_transaction_id == "parent-tx"


def test_begin_duplicate_open_raises(tm: TransactionManager) -> None:
    tm.begin("dup-tx")
    with pytest.raises(ValueError):
        tm.begin("dup-tx")


def test_begin_after_committed_succeeds(tm: TransactionManager) -> None:
    tm.begin("reuse-tx")
    tm.commit("reuse-tx")
    # After commit, a new begin with the same ID should work
    tx = tm.begin("reuse-tx")
    assert tx.status == TransactionStatus.OPEN


# ---------------------------------------------------------------------------
# record_operation()
# ---------------------------------------------------------------------------

def test_record_operation_success(tm: TransactionManager) -> None:
    tm.begin("tx-1")
    ok = tm.record_operation("tx-1", make_op())
    assert ok is True


def test_record_operation_multiple_ops(tm: TransactionManager) -> None:
    tm.begin("tx-multi")
    for _ in range(5):
        tm.record_operation("tx-multi", make_op())
    tx_snap = tm.get_transaction("tx-multi")
    assert len(tx_snap.operations) == 5


def test_record_operation_unknown_transaction(tm: TransactionManager) -> None:
    ok = tm.record_operation("nonexistent-tx", make_op())
    assert ok is False


def test_record_operation_after_abort(tm: TransactionManager) -> None:
    tm.begin("abort-tx")
    tm.abort("abort-tx")
    ok = tm.record_operation("abort-tx", make_op())
    assert ok is False


# ---------------------------------------------------------------------------
# commit()
# ---------------------------------------------------------------------------

def test_commit_success(tm: TransactionManager) -> None:
    tm.begin("tx-commit")
    tm.record_operation("tx-commit", make_op())
    result = tm.commit("tx-commit")
    assert isinstance(result, TransactionResult)
    assert result.status == TransactionStatus.COMMITTED
    assert result.completed_operations == 1
    assert result.failed_operations == 0


def test_commit_multiple_ops(tm: TransactionManager) -> None:
    tm.begin("tx-multi-commit")
    for _ in range(3):
        tm.record_operation("tx-multi-commit", make_op())
    result = tm.commit("tx-multi-commit")
    assert result.completed_operations == 3
    assert result.status == TransactionStatus.COMMITTED


def test_commit_nonexistent_transaction(tm: TransactionManager) -> None:
    result = tm.commit("ghost-tx")
    assert result.status == TransactionStatus.FAILED


def test_commit_with_failure(tm_fail: TransactionManager) -> None:
    tm_fail.begin("tx-fail")
    tm_fail.record_operation("tx-fail", make_op())
    result = tm_fail.commit("tx-fail")
    assert result.status == TransactionStatus.FAILED
    assert result.failed_operations >= 1


def test_commit_empty_transaction_succeeds(tm: TransactionManager) -> None:
    tm.begin("tx-empty")
    result = tm.commit("tx-empty")
    assert result.status == TransactionStatus.COMMITTED


# ---------------------------------------------------------------------------
# abort()
# ---------------------------------------------------------------------------

def test_abort_open_transaction(tm: TransactionManager) -> None:
    tm.begin("tx-abort")
    result = tm.abort("tx-abort")
    assert result.status == TransactionStatus.ABORTED


def test_abort_nonexistent_transaction(tm: TransactionManager) -> None:
    result = tm.abort("ghost-tx-abort")
    assert result.status == TransactionStatus.ABORTED


def test_abort_preserves_transaction_state(tm: TransactionManager) -> None:
    tm.begin("tx-check-abort")
    tm.record_operation("tx-check-abort", make_op())
    tm.abort("tx-check-abort")
    tx = tm.get_transaction("tx-check-abort")
    assert tx.status == TransactionStatus.ABORTED


# ---------------------------------------------------------------------------
# get_transaction() / list_transactions()
# ---------------------------------------------------------------------------

def test_get_transaction_existing(tm: TransactionManager) -> None:
    tm.begin("tx-get")
    tx = tm.get_transaction("tx-get")
    assert tx is not None
    assert tx.transaction_id == "tx-get"


def test_get_transaction_nonexistent(tm: TransactionManager) -> None:
    result = tm.get_transaction("ghost")
    assert result is None


def test_list_transactions(tm: TransactionManager) -> None:
    tm.begin("list-tx-1")
    tm.begin("list-tx-2")
    txs = tm.list_transactions()
    assert "list-tx-1" in txs
    assert "list-tx-2" in txs


# ---------------------------------------------------------------------------
# clear()
# ---------------------------------------------------------------------------

def test_clear_removes_closed_transactions(tm: TransactionManager) -> None:
    tm.begin("tx-open")
    tm.begin("tx-close")
    tm.commit("tx-close")
    tm.clear()
    txs = tm.list_transactions()
    assert "tx-open" in txs
    assert "tx-close" not in txs


# ---------------------------------------------------------------------------
# Thread Safety
# ---------------------------------------------------------------------------

def test_transaction_manager_thread_safety(tm: TransactionManager) -> None:
    from concurrent.futures import ThreadPoolExecutor

    def run_transaction(i: int) -> TransactionResult:
        tx_id = f"concurrent-tx-{i}"
        tm.begin(tx_id)
        tm.record_operation(tx_id, make_op(source=f"/tmp/file{i}.txt"))
        return tm.commit(tx_id)

    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = [ex.submit(run_transaction, i) for i in range(20)]
        results = [f.result() for f in futures]

    assert all(r.status == TransactionStatus.COMMITTED for r in results)
