"""Unit tests for RollbackManager (Phase 9.5)."""

from pathlib import Path
# pyrefly: ignore [missing-import]
import pytest

from brain.filesystem import RollbackManager, OperationStatus
from brain.filesystem.filesystem_models import (
    FilesystemOperationType,
    OperationResult,
    RollbackOperation,
    RollbackResult,
    TransactionResult,
    TransactionStatus,
)
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_completed_result(
    op_type: FilesystemOperationType,
    source: str,
    destination: str = None,
    op_id: str = "op-1",
) -> OperationResult:
    now = datetime.now(timezone.utc)
    return OperationResult(
        operation_id=op_id,
        operation_type=op_type,
        status=OperationStatus.COMPLETED,
        source_path=source,
        destination_path=destination,
        started_at=now,
        finished_at=now,
    )


def make_failed_result(op_type: FilesystemOperationType, source: str) -> OperationResult:
    now = datetime.now(timezone.utc)
    return OperationResult(
        operation_id="op-fail",
        operation_type=op_type,
        status=OperationStatus.FAILED,
        source_path=source,
        started_at=now,
        finished_at=now,
    )


def make_tx_result(op_results, tx_id: str = "tx-1") -> TransactionResult:
    now = datetime.now(timezone.utc)
    return TransactionResult(
        transaction_id=tx_id,
        status=TransactionStatus.COMMITTED,
        operation_results=op_results,
        completed_operations=sum(1 for r in op_results if r.status == OperationStatus.COMPLETED),
        failed_operations=sum(1 for r in op_results if r.status == OperationStatus.FAILED),
        started_at=now,
        finished_at=now,
    )


@pytest.fixture
def rm() -> RollbackManager:
    return RollbackManager()


@pytest.fixture
def rm_stop() -> RollbackManager:
    return RollbackManager(stop_on_failure=True)


# ---------------------------------------------------------------------------
# rollback() — Basic
# ---------------------------------------------------------------------------

def test_rollback_empty_transaction(rm: RollbackManager) -> None:
    tx = make_tx_result([])
    result = rm.rollback(tx)
    assert isinstance(result, RollbackResult)
    assert result.completed_rollbacks == 0
    assert result.failed_rollbacks == 0


def test_rollback_skips_failed_operations(rm: RollbackManager, tmp_path: Path) -> None:
    """Failed operations should not generate rollback entries."""
    failed = make_failed_result(FilesystemOperationType.COPY, str(tmp_path / "src.txt"))
    tx = make_tx_result([failed])
    result = rm.rollback(tx)
    assert result.completed_rollbacks == 0


def test_rollback_result_duration_populated(rm: RollbackManager) -> None:
    tx = make_tx_result([])
    result = rm.rollback(tx)
    assert result.duration_ms >= 0.0


def test_rollback_result_frozen(rm: RollbackManager) -> None:
    # pyrefly: ignore [missing-import]
    from pydantic import ValidationError
    tx = make_tx_result([])
    result = rm.rollback(tx)
    with pytest.raises((TypeError, ValidationError)):
        result.completed_rollbacks = 99


# ---------------------------------------------------------------------------
# rollback() — COPY inversion
# ---------------------------------------------------------------------------

def test_rollback_copy_deletes_destination(rm: RollbackManager, tmp_path: Path) -> None:
    src = tmp_path / "src.txt"
    dst = tmp_path / "dst.txt"
    src.write_text("data")
    dst.write_text("copied data")

    op = make_completed_result(FilesystemOperationType.COPY, str(src), str(dst))
    tx = make_tx_result([op])
    result = rm.rollback(tx)
    assert result.completed_rollbacks == 1
    assert not dst.exists()


def test_rollback_copy_no_destination_generates_no_plan(rm: RollbackManager, tmp_path: Path) -> None:
    op = make_completed_result(FilesystemOperationType.COPY, str(tmp_path / "src.txt"), destination=None)
    tx = make_tx_result([op])
    result = rm.rollback(tx)
    assert len(result.rollback_operations) == 0


# ---------------------------------------------------------------------------
# rollback() — CREATE inversion
# ---------------------------------------------------------------------------

def test_rollback_create_deletes_created_file(rm: RollbackManager, tmp_path: Path) -> None:
    created = tmp_path / "new_file.txt"
    created.write_text("content")

    op = make_completed_result(FilesystemOperationType.CREATE, str(created))
    tx = make_tx_result([op])
    result = rm.rollback(tx)
    assert result.completed_rollbacks == 1
    assert not created.exists()


def test_rollback_create_nonexistent_file_succeeds(rm: RollbackManager, tmp_path: Path) -> None:
    """Rollback of a CREATE for an already-deleted file should not fail."""
    op = make_completed_result(FilesystemOperationType.CREATE, str(tmp_path / "ghost.txt"))
    tx = make_tx_result([op])
    result = rm.rollback(tx)
    assert result.failed_rollbacks == 0


# ---------------------------------------------------------------------------
# rollback() — MOVE inversion
# ---------------------------------------------------------------------------

def test_rollback_move_restores_file(rm: RollbackManager, tmp_path: Path) -> None:
    src = tmp_path / "src.txt"
    dst = tmp_path / "dst.txt"
    src.write_text("data")
    # Simulate: move happened, so dst exists
    src.rename(dst)

    op = make_completed_result(FilesystemOperationType.MOVE, str(src), str(dst))
    tx = make_tx_result([op])
    result = rm.rollback(tx)
    assert result.completed_rollbacks == 1
    assert src.exists()
    assert not dst.exists()


# ---------------------------------------------------------------------------
# rollback() — RENAME inversion
# ---------------------------------------------------------------------------

def test_rollback_rename_restores_original_name(rm: RollbackManager, tmp_path: Path) -> None:
    original = tmp_path / "original.txt"
    renamed = tmp_path / "renamed.txt"
    original.write_text("data")
    original.rename(renamed)

    op = make_completed_result(FilesystemOperationType.RENAME, str(original), str(renamed))
    tx = make_tx_result([op])
    result = rm.rollback(tx)
    assert result.completed_rollbacks == 1
    assert original.exists()
    assert not renamed.exists()


# ---------------------------------------------------------------------------
# rollback() — DELETE (not invertible)
# ---------------------------------------------------------------------------

def test_rollback_delete_is_not_invertible(rm: RollbackManager, tmp_path: Path) -> None:
    op = make_completed_result(FilesystemOperationType.DELETE, str(tmp_path / "deleted.txt"))
    tx = make_tx_result([op])
    result = rm.rollback(tx)
    # DELETE has no inverse — 0 rollback operations generated
    assert len(result.rollback_operations) == 0
    assert result.completed_rollbacks == 0


# ---------------------------------------------------------------------------
# rollback() — LIFO Order
# ---------------------------------------------------------------------------

def test_rollback_lifo_order(rm: RollbackManager, tmp_path: Path) -> None:
    """Files created in order A, B, C should be deleted C, B, A on rollback."""
    paths = []
    op_results = []
    for name in ["a.txt", "b.txt", "c.txt"]:
        p = tmp_path / name
        p.write_text(name)
        paths.append(p)
        op_results.append(make_completed_result(
            FilesystemOperationType.CREATE, str(p), op_id=f"op-{name}"
        ))

    tx = make_tx_result(op_results)
    result = rm.rollback(tx)
    # All 3 create rollbacks should succeed (delete files)
    assert result.completed_rollbacks == 3
    assert all(not p.exists() for p in paths)


# ---------------------------------------------------------------------------
# rollback_operation() — Direct
# ---------------------------------------------------------------------------

def test_rollback_operation_delete_copy(rm: RollbackManager, tmp_path: Path) -> None:
    f = tmp_path / "copy.txt"
    f.write_text("data")
    rb_op = RollbackOperation(
        rollback_id="rb-1",
        original_operation_id="op-1",
        operation_type=FilesystemOperationType.ROLLBACK,
        source_path=str(f),
        parameters={"rollback_type": "delete_copy"},
    )
    result = rm.rollback_operation(rb_op)
    assert result.status == OperationStatus.COMPLETED
    assert not f.exists()


def test_rollback_operation_unknown_type_fails_gracefully(rm: RollbackManager, tmp_path: Path) -> None:
    rb_op = RollbackOperation(
        rollback_id="rb-x",
        original_operation_id="op-x",
        operation_type=FilesystemOperationType.ROLLBACK,
        source_path=str(tmp_path / "ghost.txt"),
        parameters={"rollback_type": "unknown_type_xyz"},
    )
    result = rm.rollback_operation(rb_op)
    assert result.status == OperationStatus.FAILED


# ---------------------------------------------------------------------------
# stop_on_failure
# ---------------------------------------------------------------------------

def test_stop_on_failure_stops_after_first_failure(rm_stop: RollbackManager, tmp_path: Path) -> None:
    """With stop_on_failure, a failed rollback aborts remaining steps."""
    # Create two files; first rollback will use unknown type (fail), second would succeed
    f1 = tmp_path / "file1.txt"
    f2 = tmp_path / "file2.txt"
    f1.write_text("d1")
    f2.write_text("d2")

    op1 = make_completed_result(FilesystemOperationType.COPY, str(f1), str(f2), op_id="op-1")
    op2 = make_completed_result(FilesystemOperationType.CREATE, str(f1), op_id="op-2")
    tx = make_tx_result([op1, op2])

    # Patch rollback plan so first rollback fails (delete nonexistent dst)
    import unittest.mock as mock
    with mock.patch.object(rm_stop, "_dispatch_rollback", return_value=False):
        result = rm_stop.rollback(tx)

    assert result.partial is True
    assert result.failed_rollbacks >= 1
