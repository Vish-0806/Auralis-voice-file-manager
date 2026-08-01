"""Unit tests for filesystem_models.py (Phase 9.5)."""

# pyrefly: ignore [missing-import]
import pytest
from datetime import datetime, timezone
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from brain.filesystem import (
    DirectoryMetadata,
    FileMetadata,
    FilesystemHealth,
    FilesystemOperation,
    FilesystemOperationType,
    FilesystemStatistics,
    OperationResult,
    OperationStatus,
    OverwritePolicy,
    PermissionResult,
    RollbackOperation,
    RollbackResult,
    SearchMatch,
    SearchResult,
    SortField,
    SortOrder,
    Transaction,
    TransactionResult,
    TransactionStatus,
)


# ---------------------------------------------------------------------------
# FilesystemOperation
# ---------------------------------------------------------------------------

def test_filesystem_operation_defaults() -> None:
    op = FilesystemOperation()
    assert op.operation_type == FilesystemOperationType.READ
    assert op.source_path == ""
    assert op.overwrite_policy == OverwritePolicy.DENY
    assert op.recursive is False
    assert isinstance(op.created_at, datetime)


def test_filesystem_operation_frozen() -> None:
    op = FilesystemOperation(source_path="/tmp/foo")
    with pytest.raises((TypeError, ValidationError)):
        op.source_path = "/tmp/bar"


def test_filesystem_operation_all_types() -> None:
    for t in FilesystemOperationType:
        op = FilesystemOperation(operation_type=t, source_path="/f")
        assert op.operation_type == t


def test_filesystem_operation_overwrite_policies() -> None:
    for p in OverwritePolicy:
        op = FilesystemOperation(overwrite_policy=p)
        assert op.overwrite_policy == p


# ---------------------------------------------------------------------------
# OperationResult
# ---------------------------------------------------------------------------

def test_operation_result_defaults() -> None:
    r = OperationResult()
    assert r.status == OperationStatus.COMPLETED
    assert r.error is None
    assert r.duration_ms == 0.0


def test_operation_result_frozen() -> None:
    r = OperationResult(status=OperationStatus.FAILED)
    with pytest.raises((TypeError, ValidationError)):
        r.status = OperationStatus.COMPLETED


def test_operation_result_all_statuses() -> None:
    for s in OperationStatus:
        r = OperationResult(status=s)
        assert r.status == s


def test_operation_result_with_error() -> None:
    r = OperationResult(status=OperationStatus.FAILED, error="Something went wrong")
    assert r.error == "Something went wrong"


# ---------------------------------------------------------------------------
# Transaction / TransactionResult
# ---------------------------------------------------------------------------

def test_transaction_defaults() -> None:
    t = Transaction()
    assert t.status == TransactionStatus.OPEN
    assert t.operations == []
    assert t.parent_transaction_id is None


def test_transaction_frozen() -> None:
    t = Transaction(transaction_id="tx-1")
    with pytest.raises((TypeError, ValidationError)):
        t.transaction_id = "tx-2"


def test_transaction_result_defaults() -> None:
    r = TransactionResult()
    assert r.completed_operations == 0
    assert r.failed_operations == 0
    assert r.error is None


def test_transaction_result_frozen() -> None:
    r = TransactionResult(completed_operations=5)
    with pytest.raises((TypeError, ValidationError)):
        r.completed_operations = 0


# ---------------------------------------------------------------------------
# RollbackOperation / RollbackResult
# ---------------------------------------------------------------------------

def test_rollback_operation_defaults() -> None:
    rb = RollbackOperation()
    assert rb.operation_type == FilesystemOperationType.ROLLBACK
    assert rb.source_path == ""


def test_rollback_operation_frozen() -> None:
    rb = RollbackOperation(source_path="/a")
    with pytest.raises((TypeError, ValidationError)):
        rb.source_path = "/b"


def test_rollback_result_defaults() -> None:
    r = RollbackResult()
    assert r.completed_rollbacks == 0
    assert r.failed_rollbacks == 0
    assert r.partial is False


def test_rollback_result_frozen() -> None:
    r = RollbackResult(completed_rollbacks=3)
    with pytest.raises((TypeError, ValidationError)):
        r.completed_rollbacks = 0


# ---------------------------------------------------------------------------
# FileMetadata / DirectoryMetadata
# ---------------------------------------------------------------------------

def test_file_metadata_defaults() -> None:
    m = FileMetadata()
    assert m.size_bytes == 0
    assert m.is_hidden is False
    assert m.is_symlink is False


def test_file_metadata_frozen() -> None:
    m = FileMetadata(name="test.txt")
    with pytest.raises((TypeError, ValidationError)):
        m.name = "other.txt"


def test_directory_metadata_defaults() -> None:
    m = DirectoryMetadata()
    assert m.child_count == 0
    assert m.total_size_bytes == 0


def test_directory_metadata_frozen() -> None:
    m = DirectoryMetadata(path="/tmp")
    with pytest.raises((TypeError, ValidationError)):
        m.path = "/other"


# ---------------------------------------------------------------------------
# SearchResult / SearchMatch
# ---------------------------------------------------------------------------

def test_search_result_defaults() -> None:
    r = SearchResult()
    assert r.total_matches == 0
    assert r.page == 1
    assert r.page_size == 100
    assert r.matches == []


def test_search_result_frozen() -> None:
    r = SearchResult(total_matches=5)
    with pytest.raises((TypeError, ValidationError)):
        r.total_matches = 0


def test_search_match_defaults() -> None:
    m = SearchMatch()
    assert m.path == ""
    assert m.is_directory is False
    assert m.size_bytes == 0


def test_sort_fields_and_orders() -> None:
    for f in SortField:
        assert isinstance(f.value, str)
    for o in SortOrder:
        assert isinstance(o.value, str)


# ---------------------------------------------------------------------------
# PermissionResult
# ---------------------------------------------------------------------------

def test_permission_result_defaults() -> None:
    r = PermissionResult()
    assert r.can_read is False
    assert r.can_write is False
    assert r.can_delete is False
    assert r.can_execute is False
    assert r.exists is False


def test_permission_result_frozen() -> None:
    r = PermissionResult(can_read=True)
    with pytest.raises((TypeError, ValidationError)):
        r.can_read = False


# ---------------------------------------------------------------------------
# FilesystemHealth / FilesystemStatistics
# ---------------------------------------------------------------------------

def test_filesystem_health_defaults() -> None:
    h = FilesystemHealth()
    assert h.healthy is True
    assert h.status == "READY"
    assert h.registered_components == []
    assert h.uptime_seconds == 0.0


def test_filesystem_health_frozen() -> None:
    h = FilesystemHealth(healthy=True)
    with pytest.raises((TypeError, ValidationError)):
        h.healthy = False


def test_filesystem_statistics_defaults() -> None:
    s = FilesystemStatistics()
    assert s.operations_started == 0
    assert s.transactions_committed == 0
    assert s.rollbacks_performed == 0
    assert s.average_operation_ms == 0.0


def test_filesystem_statistics_frozen() -> None:
    s = FilesystemStatistics(operations_started=10)
    with pytest.raises((TypeError, ValidationError)):
        s.operations_started = 0


# ---------------------------------------------------------------------------
# Phase 11.2 brain.os.filesystem Models Tests
# ---------------------------------------------------------------------------

def test_os_filesystem_entry_defaults_and_immutability() -> None:
    from brain.os.filesystem import FilesystemEntry, FilesystemEntryType

    entry = FilesystemEntry(path="/tmp/test.txt", name="test.txt", entry_type=FilesystemEntryType.FILE)
    assert entry.path == "/tmp/test.txt"
    assert entry.entry_type == FilesystemEntryType.FILE

    with pytest.raises((TypeError, ValidationError)):
        entry.name = "other.txt"  # type: ignore


def test_os_filesystem_permission_info_defaults_and_immutability() -> None:
    from brain.os.filesystem import PermissionInfo

    info = PermissionInfo(path="/tmp/test.txt", can_read=True, can_write=True)
    assert info.can_read is True
    assert info.can_write is True

    with pytest.raises((TypeError, ValidationError)):
        info.can_read = False  # type: ignore


def test_os_filesystem_capabilities_defaults_and_immutability() -> None:
    from brain.os.filesystem import FilesystemCapabilities

    caps = FilesystemCapabilities(supports_atomic_writes=True)
    assert caps.supports_atomic_writes is True
    assert caps.supports_transactions is True

    with pytest.raises((TypeError, ValidationError)):
        caps.supports_atomic_writes = False  # type: ignore

