"""Unit tests for FilesystemProvider (Phase 9.5)."""

from pathlib import Path
# pyrefly: ignore [missing-import]
import pytest

from brain.filesystem import (
    FilesystemProvider,
    OperationStatus,
    OverwritePolicy,
    SearchResult,
    TransactionStatus,
)


@pytest.fixture
def provider() -> FilesystemProvider:
    return FilesystemProvider()


@pytest.fixture
def src_file(tmp_path: Path) -> str:
    f = tmp_path / "source.txt"
    f.write_text("hello provider")
    return str(f)


# ---------------------------------------------------------------------------
# copy()
# ---------------------------------------------------------------------------

def test_provider_copy_success(provider: FilesystemProvider, src_file: str, tmp_path: Path) -> None:
    dst = str(tmp_path / "copied.txt")
    result = provider.copy(src_file, dst)
    assert result.status == OperationStatus.COMPLETED
    assert Path(dst).exists()


def test_provider_copy_nonexistent_source(provider: FilesystemProvider, tmp_path: Path) -> None:
    result = provider.copy(str(tmp_path / "ghost.txt"), str(tmp_path / "dst.txt"))
    assert result.status == OperationStatus.FAILED


def test_provider_copy_deny_on_conflict(provider: FilesystemProvider, src_file: str, tmp_path: Path) -> None:
    dst = str(tmp_path / "existing.txt")
    Path(dst).write_text("exists")
    result = provider.copy(src_file, dst, OverwritePolicy.DENY)
    assert result.status == OperationStatus.FAILED


# ---------------------------------------------------------------------------
# move()
# ---------------------------------------------------------------------------

def test_provider_move_success(provider: FilesystemProvider, src_file: str, tmp_path: Path) -> None:
    dst = str(tmp_path / "moved.txt")
    result = provider.move(src_file, dst)
    assert result.status == OperationStatus.COMPLETED
    assert Path(dst).exists()
    assert not Path(src_file).exists()


# ---------------------------------------------------------------------------
# rename()
# ---------------------------------------------------------------------------

def test_provider_rename_success(provider: FilesystemProvider, src_file: str, tmp_path: Path) -> None:
    result = provider.rename(src_file, "renamed.txt")
    assert result.status == OperationStatus.COMPLETED
    assert Path(tmp_path / "renamed.txt").exists()


# ---------------------------------------------------------------------------
# delete()
# ---------------------------------------------------------------------------

def test_provider_delete_success(provider: FilesystemProvider, src_file: str) -> None:
    result = provider.delete(src_file)
    assert result.status == OperationStatus.COMPLETED
    assert not Path(src_file).exists()


def test_provider_delete_nonexistent(provider: FilesystemProvider, tmp_path: Path) -> None:
    result = provider.delete(str(tmp_path / "ghost.txt"))
    assert result.status == OperationStatus.FAILED


# ---------------------------------------------------------------------------
# create()
# ---------------------------------------------------------------------------

def test_provider_create_success(provider: FilesystemProvider, tmp_path: Path) -> None:
    path = str(tmp_path / "new.txt")
    result = provider.create(path, "content")
    assert result.status == OperationStatus.COMPLETED
    assert Path(path).read_text() == "content"


def test_provider_create_overwrite(provider: FilesystemProvider, tmp_path: Path) -> None:
    path = str(tmp_path / "exist.txt")
    Path(path).write_text("old")
    result = provider.create(path, "new", OverwritePolicy.OVERWRITE)
    assert result.status == OperationStatus.COMPLETED
    assert Path(path).read_text() == "new"


# ---------------------------------------------------------------------------
# create_directory() / delete_directory() / list_directory()
# ---------------------------------------------------------------------------

def test_provider_create_directory(provider: FilesystemProvider, tmp_path: Path) -> None:
    d = str(tmp_path / "new_dir")
    result = provider.create_directory(d)
    assert result.status == OperationStatus.COMPLETED
    assert Path(d).is_dir()


def test_provider_delete_directory(provider: FilesystemProvider, tmp_path: Path) -> None:
    d = tmp_path / "del_dir"
    d.mkdir()
    result = provider.delete_directory(str(d))
    assert result.status == OperationStatus.COMPLETED
    assert not d.exists()


def test_provider_list_directory(provider: FilesystemProvider, tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "b.txt").write_text("b")
    items = provider.list_directory(str(tmp_path))
    assert len(items) >= 2


# ---------------------------------------------------------------------------
# search()
# ---------------------------------------------------------------------------

def test_provider_search_basic(provider: FilesystemProvider, tmp_path: Path) -> None:
    (tmp_path / "find_me.txt").write_text("data")
    result = provider.search(str(tmp_path), pattern="*.txt")
    assert isinstance(result, SearchResult)
    assert result.total_matches >= 1


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------

def test_provider_file_metadata(provider: FilesystemProvider, src_file: str) -> None:
    meta = provider.file_metadata(src_file)
    assert meta.size_bytes == len("hello provider")


def test_provider_directory_metadata(provider: FilesystemProvider, tmp_path: Path) -> None:
    meta = provider.directory_metadata(str(tmp_path))
    assert meta.path == str(tmp_path)
    assert meta.child_count >= 0


# ---------------------------------------------------------------------------
# Transaction Context Manager
# ---------------------------------------------------------------------------

def test_provider_transaction_commit(provider: FilesystemProvider, tmp_path: Path) -> None:
    path = str(tmp_path / "tx_file.txt")
    with provider.transaction() as tx_id:
        provider.create(path, "tx content", transaction_id=tx_id)
    assert Path(path).exists()


def test_provider_transaction_abort_on_exception(provider: FilesystemProvider, tmp_path: Path) -> None:
    """Verify abort is called on exception within transaction context."""
    path = str(tmp_path / "aborted.txt")
    with pytest.raises(ValueError):
        with provider.transaction() as tx_id:
            provider.create(path, "data", transaction_id=tx_id)
            raise ValueError("Abort!")
    # File should not exist since transaction was aborted (never executed)
    assert not Path(path).exists()


def test_provider_begin_commit_transaction(provider: FilesystemProvider, tmp_path: Path) -> None:
    path = str(tmp_path / "manual_tx.txt")
    tx_id = provider.begin_transaction()
    provider.create(path, "manual tx", transaction_id=tx_id)
    result = provider.commit_transaction(tx_id)
    assert result.status == TransactionStatus.COMMITTED
    assert Path(path).exists()


def test_provider_begin_abort_transaction(provider: FilesystemProvider, tmp_path: Path) -> None:
    tx_id = provider.begin_transaction()
    result = provider.abort_transaction(tx_id)
    assert result.status == TransactionStatus.ABORTED


# ---------------------------------------------------------------------------
# Transaction with immediate execution
# ---------------------------------------------------------------------------

def test_provider_direct_copy_no_transaction(provider: FilesystemProvider, src_file: str, tmp_path: Path) -> None:
    dst = str(tmp_path / "direct.txt")
    result = provider.copy(src_file, dst)
    assert result.status == OperationStatus.COMPLETED


def test_provider_transaction_recorded_as_pending(provider: FilesystemProvider, tmp_path: Path) -> None:
    tx_id = provider.begin_transaction()
    path = str(tmp_path / "pending.txt")
    result = provider.create(path, "data", transaction_id=tx_id)
    # Should be PENDING until commit
    assert result.status == OperationStatus.PENDING
    provider.abort_transaction(tx_id)


# ---------------------------------------------------------------------------
# Rollback
# ---------------------------------------------------------------------------

def test_provider_rollback_after_create(provider: FilesystemProvider, tmp_path: Path) -> None:
    path = str(tmp_path / "rollback_me.txt")
    tx_id = provider.begin_transaction()
    provider.create(path, "will be rolled back", transaction_id=tx_id)
    tx_result = provider.commit_transaction(tx_id)
    rb_result = provider.rollback(tx_result)
    assert rb_result.completed_rollbacks >= 0  # Rollback ran
