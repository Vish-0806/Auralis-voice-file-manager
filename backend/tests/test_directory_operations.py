"""Unit tests for DirectoryOperations (Phase 9.5)."""

from pathlib import Path
# pyrefly: ignore [missing-import]
import pytest

from brain.filesystem import DirectoryOperations, OperationStatus, OverwritePolicy
from brain.filesystem.filesystem_models import DirectoryMetadata


@pytest.fixture
def dir_ops() -> DirectoryOperations:
    return DirectoryOperations()


@pytest.fixture
def tmp_dir(tmp_path: Path) -> str:
    return str(tmp_path)


@pytest.fixture
def populated_dir(tmp_path: Path) -> str:
    d = tmp_path / "populated"
    d.mkdir()
    (d / "a.txt").write_text("aaa")
    (d / "b.txt").write_text("bbb")
    sub = d / "sub"
    sub.mkdir()
    (sub / "c.txt").write_text("ccc")
    return str(d)


# ---------------------------------------------------------------------------
# create_directory()
# ---------------------------------------------------------------------------

def test_create_directory_basic(dir_ops: DirectoryOperations, tmp_dir: str) -> None:
    new_dir = tmp_dir + "/new_dir"
    result = dir_ops.create_directory(new_dir)
    assert result.status == OperationStatus.COMPLETED
    assert Path(new_dir).is_dir()


def test_create_directory_nested(dir_ops: DirectoryOperations, tmp_dir: str) -> None:
    deep = tmp_dir + "/a/b/c"
    result = dir_ops.create_directory(deep, parents=True)
    assert result.status == OperationStatus.COMPLETED
    assert Path(deep).is_dir()


def test_create_directory_already_exists(dir_ops: DirectoryOperations, tmp_dir: str) -> None:
    result = dir_ops.create_directory(tmp_dir)
    assert result.status == OperationStatus.COMPLETED
    assert result.output.get("already_existed") is True


# ---------------------------------------------------------------------------
# delete_directory()
# ---------------------------------------------------------------------------

def test_delete_empty_directory(dir_ops: DirectoryOperations, tmp_dir: str) -> None:
    d = tmp_dir + "/empty"
    Path(d).mkdir()
    result = dir_ops.delete_directory(d)
    assert result.status == OperationStatus.COMPLETED
    assert not Path(d).exists()


def test_delete_nonempty_directory_without_recursive_fails(dir_ops: DirectoryOperations, populated_dir: str) -> None:
    result = dir_ops.delete_directory(populated_dir, recursive=False)
    assert result.status == OperationStatus.FAILED
    assert Path(populated_dir).exists()


def test_delete_nonempty_directory_recursive(dir_ops: DirectoryOperations, populated_dir: str) -> None:
    result = dir_ops.delete_directory(populated_dir, recursive=True)
    assert result.status == OperationStatus.COMPLETED
    assert not Path(populated_dir).exists()


def test_delete_nonexistent_directory(dir_ops: DirectoryOperations, tmp_dir: str) -> None:
    result = dir_ops.delete_directory(tmp_dir + "/ghost")
    assert result.status == OperationStatus.FAILED


def test_delete_file_as_directory_fails(dir_ops: DirectoryOperations, tmp_path: Path) -> None:
    f = tmp_path / "file.txt"
    f.write_text("data")
    result = dir_ops.delete_directory(str(f))
    assert result.status == OperationStatus.FAILED


# ---------------------------------------------------------------------------
# rename_directory()
# ---------------------------------------------------------------------------

def test_rename_directory_success(dir_ops: DirectoryOperations, tmp_dir: str) -> None:
    d = tmp_dir + "/original"
    Path(d).mkdir()
    result = dir_ops.rename_directory(d, "renamed")
    assert result.status == OperationStatus.COMPLETED
    assert Path(tmp_dir + "/renamed").is_dir()
    assert not Path(d).exists()


def test_rename_directory_nonexistent(dir_ops: DirectoryOperations, tmp_dir: str) -> None:
    result = dir_ops.rename_directory(tmp_dir + "/ghost", "new_name")
    assert result.status == OperationStatus.FAILED


def test_rename_directory_conflict_deny(dir_ops: DirectoryOperations, tmp_dir: str) -> None:
    src = tmp_dir + "/src"
    dst = tmp_dir + "/dst"
    Path(src).mkdir()
    Path(dst).mkdir()
    result = dir_ops.rename_directory(src, "dst", OverwritePolicy.DENY)
    assert result.status == OperationStatus.FAILED


# ---------------------------------------------------------------------------
# move_directory()
# ---------------------------------------------------------------------------

def test_move_directory_success(dir_ops: DirectoryOperations, populated_dir: str, tmp_path: Path) -> None:
    dst = str(tmp_path / "moved")
    result = dir_ops.move_directory(populated_dir, dst)
    assert result.status == OperationStatus.COMPLETED
    assert Path(dst).is_dir()
    assert not Path(populated_dir).exists()


def test_move_directory_conflict(dir_ops: DirectoryOperations, tmp_dir: str) -> None:
    src = tmp_dir + "/src"
    dst = tmp_dir + "/dst"
    Path(src).mkdir()
    Path(dst).mkdir()
    result = dir_ops.move_directory(src, dst)
    assert result.status == OperationStatus.FAILED


# ---------------------------------------------------------------------------
# copy_directory()
# ---------------------------------------------------------------------------

def test_copy_directory_success(dir_ops: DirectoryOperations, populated_dir: str, tmp_path: Path) -> None:
    dst = str(tmp_path / "copy")
    result = dir_ops.copy_directory(populated_dir, dst)
    assert result.status == OperationStatus.COMPLETED
    assert Path(dst).is_dir()
    assert Path(dst + "/a.txt").exists()
    assert Path(populated_dir).exists()  # original preserved


def test_copy_directory_conflict_skip(dir_ops: DirectoryOperations, populated_dir: str, tmp_path: Path) -> None:
    dst = str(tmp_path / "existing")
    Path(dst).mkdir()
    result = dir_ops.copy_directory(populated_dir, dst, OverwritePolicy.SKIP)
    assert result.status == OperationStatus.SKIPPED


# ---------------------------------------------------------------------------
# empty_directory()
# ---------------------------------------------------------------------------

def test_empty_directory_removes_contents(dir_ops: DirectoryOperations, populated_dir: str) -> None:
    result = dir_ops.empty_directory(populated_dir)
    assert result.status == OperationStatus.COMPLETED
    assert Path(populated_dir).is_dir()
    assert list(Path(populated_dir).iterdir()) == []
    assert result.output.get("items_removed", 0) >= 2


def test_empty_nonexistent_directory(dir_ops: DirectoryOperations, tmp_dir: str) -> None:
    result = dir_ops.empty_directory(tmp_dir + "/ghost")
    assert result.status == OperationStatus.FAILED


# ---------------------------------------------------------------------------
# list_directory()
# ---------------------------------------------------------------------------

def test_list_directory_non_recursive(dir_ops: DirectoryOperations, populated_dir: str) -> None:
    items = dir_ops.list_directory(populated_dir, recursive=False)
    assert len(items) == 3  # a.txt, b.txt, sub/


def test_list_directory_recursive(dir_ops: DirectoryOperations, populated_dir: str) -> None:
    items = dir_ops.list_directory(populated_dir, recursive=True)
    assert len(items) == 4  # a.txt, b.txt, sub/, sub/c.txt


def test_list_directory_nonexistent(dir_ops: DirectoryOperations, tmp_dir: str) -> None:
    items = dir_ops.list_directory(tmp_dir + "/ghost")
    assert items == []


# ---------------------------------------------------------------------------
# read_metadata()
# ---------------------------------------------------------------------------

def test_directory_metadata_populated(dir_ops: DirectoryOperations, populated_dir: str) -> None:
    meta = dir_ops.read_metadata(populated_dir)
    assert isinstance(meta, DirectoryMetadata)
    assert meta.child_count == 3
    assert meta.total_size_bytes > 0
    assert meta.name == "populated"


def test_directory_metadata_nonexistent(dir_ops: DirectoryOperations, tmp_dir: str) -> None:
    meta = dir_ops.read_metadata(tmp_dir + "/ghost")
    assert isinstance(meta, DirectoryMetadata)
    assert meta.child_count == 0
