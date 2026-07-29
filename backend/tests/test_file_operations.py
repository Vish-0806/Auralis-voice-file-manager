"""Unit tests for FileOperations (Phase 9.5)."""

import os
from pathlib import Path

# pyrefly: ignore [missing-import]
import pytest

from brain.filesystem import FileOperations, OperationStatus, OverwritePolicy
from brain.filesystem.filesystem_models import FileMetadata, FilesystemOperationType


@pytest.fixture
def file_ops() -> FileOperations:
    return FileOperations()


@pytest.fixture
def src_file(tmp_path: Path) -> str:
    f = tmp_path / "source.txt"
    f.write_text("hello world")
    return str(f)


@pytest.fixture
def dst_path(tmp_path: Path) -> str:
    return str(tmp_path / "dest" / "target.txt")


# ---------------------------------------------------------------------------
# copy()
# ---------------------------------------------------------------------------

def test_copy_success(file_ops: FileOperations, src_file: str, tmp_path: Path) -> None:
    dst = str(tmp_path / "copy.txt")
    result = file_ops.copy(src_file, dst)
    assert result.status == OperationStatus.COMPLETED
    assert Path(dst).exists()
    assert Path(dst).read_text() == "hello world"


def test_copy_nonexistent_source(file_ops: FileOperations, tmp_path: Path) -> None:
    result = file_ops.copy(str(tmp_path / "ghost.txt"), str(tmp_path / "dst.txt"))
    assert result.status == OperationStatus.FAILED
    assert result.error is not None


def test_copy_destination_conflict_deny(file_ops: FileOperations, src_file: str, tmp_path: Path) -> None:
    dst = str(tmp_path / "existing.txt")
    Path(dst).write_text("existing")
    result = file_ops.copy(src_file, dst, OverwritePolicy.DENY)
    assert result.status == OperationStatus.FAILED


def test_copy_destination_conflict_overwrite(file_ops: FileOperations, src_file: str, tmp_path: Path) -> None:
    dst = str(tmp_path / "existing.txt")
    Path(dst).write_text("old content")
    result = file_ops.copy(src_file, dst, OverwritePolicy.OVERWRITE)
    assert result.status == OperationStatus.COMPLETED
    assert Path(dst).read_text() == "hello world"


def test_copy_destination_conflict_skip(file_ops: FileOperations, src_file: str, tmp_path: Path) -> None:
    dst = str(tmp_path / "existing.txt")
    Path(dst).write_text("old content")
    result = file_ops.copy(src_file, dst, OverwritePolicy.SKIP)
    assert result.status == OperationStatus.SKIPPED
    assert Path(dst).read_text() == "old content"


def test_copy_creates_parent_directories(file_ops: FileOperations, src_file: str, dst_path: str) -> None:
    result = file_ops.copy(src_file, dst_path)
    assert result.status == OperationStatus.COMPLETED
    assert Path(dst_path).exists()


def test_copy_source_is_directory_fails(file_ops: FileOperations, tmp_path: Path) -> None:
    result = file_ops.copy(str(tmp_path), str(tmp_path / "copy"))
    assert result.status == OperationStatus.FAILED


def test_copy_result_duration_positive(file_ops: FileOperations, src_file: str, tmp_path: Path) -> None:
    dst = str(tmp_path / "copy.txt")
    result = file_ops.copy(src_file, dst)
    assert result.duration_ms >= 0.0


# ---------------------------------------------------------------------------
# move()
# ---------------------------------------------------------------------------

def test_move_success(file_ops: FileOperations, src_file: str, tmp_path: Path) -> None:
    dst = str(tmp_path / "moved.txt")
    result = file_ops.move(src_file, dst)
    assert result.status == OperationStatus.COMPLETED
    assert Path(dst).exists()
    assert not Path(src_file).exists()


def test_move_nonexistent_source(file_ops: FileOperations, tmp_path: Path) -> None:
    result = file_ops.move(str(tmp_path / "ghost.txt"), str(tmp_path / "dst.txt"))
    assert result.status == OperationStatus.FAILED


def test_move_conflict_deny(file_ops: FileOperations, src_file: str, tmp_path: Path) -> None:
    dst = str(tmp_path / "existing.txt")
    Path(dst).write_text("existing")
    result = file_ops.move(src_file, dst, OverwritePolicy.DENY)
    assert result.status == OperationStatus.FAILED
    # Source should still exist
    assert Path(src_file).exists()


def test_move_conflict_overwrite(file_ops: FileOperations, src_file: str, tmp_path: Path) -> None:
    dst = str(tmp_path / "existing.txt")
    Path(dst).write_text("old")
    result = file_ops.move(src_file, dst, OverwritePolicy.OVERWRITE)
    assert result.status == OperationStatus.COMPLETED
    assert Path(dst).read_text() == "hello world"


# ---------------------------------------------------------------------------
# rename()
# ---------------------------------------------------------------------------

def test_rename_success(file_ops: FileOperations, src_file: str, tmp_path: Path) -> None:
    result = file_ops.rename(src_file, "renamed.txt")
    assert result.status == OperationStatus.COMPLETED
    assert Path(tmp_path / "renamed.txt").exists()
    assert not Path(src_file).exists()


def test_rename_nonexistent_source(file_ops: FileOperations, tmp_path: Path) -> None:
    result = file_ops.rename(str(tmp_path / "ghost.txt"), "new.txt")
    assert result.status == OperationStatus.FAILED


def test_rename_conflict_deny(file_ops: FileOperations, src_file: str, tmp_path: Path) -> None:
    existing = str(tmp_path / "renamed.txt")
    Path(existing).write_text("other")
    result = file_ops.rename(src_file, "renamed.txt", OverwritePolicy.DENY)
    assert result.status == OperationStatus.FAILED


# ---------------------------------------------------------------------------
# delete()
# ---------------------------------------------------------------------------

def test_delete_success(file_ops: FileOperations, src_file: str) -> None:
    result = file_ops.delete(src_file)
    assert result.status == OperationStatus.COMPLETED
    assert not Path(src_file).exists()


def test_delete_nonexistent(file_ops: FileOperations, tmp_path: Path) -> None:
    result = file_ops.delete(str(tmp_path / "ghost.txt"))
    assert result.status == OperationStatus.FAILED


def test_delete_directory_safe_mode(file_ops: FileOperations, tmp_path: Path) -> None:
    """Should refuse to delete a directory in safe mode."""
    result = file_ops.delete(str(tmp_path), safe=True)
    assert result.status == OperationStatus.FAILED


# ---------------------------------------------------------------------------
# create()
# ---------------------------------------------------------------------------

def test_create_success(file_ops: FileOperations, tmp_path: Path) -> None:
    path = str(tmp_path / "new.txt")
    result = file_ops.create(path, "content")
    assert result.status == OperationStatus.COMPLETED
    assert Path(path).read_text() == "content"


def test_create_conflict_deny(file_ops: FileOperations, tmp_path: Path) -> None:
    path = str(tmp_path / "existing.txt")
    Path(path).write_text("old")
    result = file_ops.create(path, "new", OverwritePolicy.DENY)
    assert result.status == OperationStatus.FAILED


def test_create_conflict_overwrite(file_ops: FileOperations, tmp_path: Path) -> None:
    path = str(tmp_path / "existing.txt")
    Path(path).write_text("old")
    result = file_ops.create(path, "new", OverwritePolicy.OVERWRITE)
    assert result.status == OperationStatus.COMPLETED
    assert Path(path).read_text() == "new"


def test_create_empty_file(file_ops: FileOperations, tmp_path: Path) -> None:
    path = str(tmp_path / "empty.txt")
    result = file_ops.create(path)
    assert result.status == OperationStatus.COMPLETED
    assert Path(path).read_text() == ""


# ---------------------------------------------------------------------------
# read_metadata()
# ---------------------------------------------------------------------------

def test_read_metadata_existing_file(file_ops: FileOperations, src_file: str) -> None:
    meta = file_ops.read_metadata(src_file)
    assert isinstance(meta, FileMetadata)
    assert meta.size_bytes == len("hello world")
    assert meta.name == "source.txt"
    assert meta.extension == ".txt"


def test_read_metadata_nonexistent(file_ops: FileOperations, tmp_path: Path) -> None:
    meta = file_ops.read_metadata(str(tmp_path / "ghost.txt"))
    assert isinstance(meta, FileMetadata)
    assert meta.size_bytes == 0


# ---------------------------------------------------------------------------
# Thread Safety
# ---------------------------------------------------------------------------

def test_file_ops_concurrent_creates(tmp_path: Path) -> None:
    from concurrent.futures import ThreadPoolExecutor
    ops = FileOperations()
    results = []

    def create_file(i: int) -> None:
        path = str(tmp_path / f"file_{i}.txt")
        r = ops.create(path, f"content_{i}")
        results.append(r.status)

    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = [ex.submit(create_file, i) for i in range(20)]
        for f in futures:
            f.result()

    assert all(s == OperationStatus.COMPLETED for s in results)
