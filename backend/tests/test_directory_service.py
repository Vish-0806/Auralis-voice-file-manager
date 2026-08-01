"""Unit tests for DirectoryService (Phase 11.2)."""

# pyrefly: ignore [missing-import]
import pytest
from brain.os.filesystem import DirectoryService, FilesystemEntry, FilesystemEntryType


def test_directory_service_list_and_traverse(tmp_path) -> None:
    d1 = tmp_path / "dir1"
    d1.mkdir()
    (d1 / "a.txt").write_text("a")
    (d1 / "b.py").write_text("b")

    sub = d1 / "subdir"
    sub.mkdir()
    (sub / "c.json").write_text("{}")

    svc = DirectoryService()

    entries = svc.list_directory(str(d1))
    assert len(entries) == 3
    entry_names = [e.name for e in entries]
    assert "a.txt" in entry_names
    assert "b.py" in entry_names
    assert "subdir" in entry_names

    traversed = svc.traverse_directory(str(d1), recursive=True)
    traversed_names = [e.name for e in traversed]
    assert "c.json" in traversed_names


def test_directory_service_tree_and_empty(tmp_path) -> None:
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    svc = DirectoryService()
    assert svc.is_empty(str(empty_dir)) is True

    (empty_dir / "file.txt").write_text("data")
    assert svc.is_empty(str(empty_dir)) is False

    tree = svc.generate_tree(str(tmp_path), max_depth=2)
    assert isinstance(tree, dict)
    assert tree["type"] == "directory"
    assert len(tree["children"]) > 0
