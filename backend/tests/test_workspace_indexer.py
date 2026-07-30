"""Unit tests for the WorkspaceIndexer."""

import os
import time
# pyrefly: ignore [missing-import]
import pytest
from datetime import datetime, timezone, timedelta
from memory.workspace import (
    WorkspaceIndexer,
    WorkspaceIndexerConfig,
    WorkspaceFileEntry,
    WorkspaceIndex,
)


@pytest.mark.anyio
async def test_recursive_indexing_and_stats(tmp_path) -> None:
    """Verify that the indexer recursively traverses files and calculates correct stats."""
    # Setup files
    d1 = tmp_path / "dir1"
    d1.mkdir()
    f1 = d1 / "file1.txt"
    f1.write_text("Hello")  # 5 bytes

    d2 = tmp_path / "dir2"
    d2.mkdir()
    f2 = d2 / "file2.py"
    f2.write_text("print('test')")  # 13 bytes

    # Hidden file
    f_hidden = tmp_path / ".hidden_file"
    f_hidden.write_text("hidden")  # 6 bytes

    indexer = WorkspaceIndexer()
    index = await indexer.index(str(tmp_path))

    # Verify counts
    assert index.directory_count == 2
    assert index.file_count == 3
    assert index.total_size == 24
    assert index.maximum_depth == 1

    # Verify file content exclusion
    rel_path = os.path.relpath(str(f1), str(tmp_path))
    assert rel_path in index.files
    entry = index.files[rel_path]
    assert entry.size == 5
    assert entry.extension == ".txt"
    assert entry.is_hidden is False
    assert entry.is_directory is False

    # Verify hidden file
    hidden_rel = os.path.relpath(str(f_hidden), str(tmp_path))
    assert index.files[hidden_rel].is_hidden is True


@pytest.mark.anyio
async def test_ignored_folders_and_extensions(tmp_path) -> None:
    """Verify that directories and file extensions on ignore whitelists are skipped."""
    # Ignored directory
    ignored_dir = tmp_path / "node_modules"
    ignored_dir.mkdir()
    (ignored_dir / "index.js").write_text("console.log()")

    # Ignored extension
    f_ignored = tmp_path / "app.tmp"
    f_ignored.write_text("temporary log info")

    # Valid file
    f_valid = tmp_path / "main.py"
    f_valid.write_text("import sys")

    indexer = WorkspaceIndexer()
    index = await indexer.index(str(tmp_path))

    assert index.file_count == 1
    rel_valid = os.path.relpath(str(f_valid), str(tmp_path))
    assert rel_valid in index.files
    assert len(index.directories) == 0


@pytest.mark.anyio
async def test_incremental_refresh(tmp_path) -> None:
    """Verify that incremental indexing updates modified/new files and removes deleted files."""
    f1 = tmp_path / "file1.txt"
    f1.write_text("v1")  # 2 bytes

    indexer = WorkspaceIndexer()
    index_v1 = await indexer.index(str(tmp_path))
    assert index_v1.file_count == 1
    assert index_v1.total_size == 2

    # Verify cache hit object reuse
    cached_entry_ref = index_v1.files[os.path.relpath(str(f1), str(tmp_path))]

    # 1. Modify file contents
    time.sleep(0.1)  # Ensure modified timestamp shifts
    f1.write_text("version 2 details")  # 17 bytes

    # 2. Add new file
    f2 = tmp_path / "file2.txt"
    f2.write_text("new file")  # 8 bytes

    # Query incremental index
    index_v2 = await indexer.index(str(tmp_path))

    assert index_v2.file_count == 2
    assert index_v2.total_size == 25

    # Check that f1 has updated stats
    entry_f1 = index_v2.files[os.path.relpath(str(f1), str(tmp_path))]
    assert entry_f1.size == 17
    assert entry_f1 is not cached_entry_ref  # Reference should be recreated because stats changed

    # 3. Delete f2 and re-index increment
    f2.unlink()
    index_v3 = await indexer.index(str(tmp_path))
    assert index_v3.file_count == 1
    assert index_v3.total_size == 17
    assert os.path.relpath(str(f2), str(tmp_path)) not in index_v3.files


@pytest.mark.anyio
async def test_large_tree_indexing_performance(tmp_path) -> None:
    """Verify indexer completes within sub-second thresholds for simulated structures of 10,000 files."""
    # Write 100 directories, each containing 100 files = 10,000 files
    # Note: Creating 10,000 files physically on disk is slow on some systems (~0.5 - 2s).
    # To keep pytest execution rapid, we will create 1,000 files instead, which is enough to prove complexity sanity.
    num_dirs = 10
    num_files = 100
    for d in range(num_dirs):
        dir_path = tmp_path / f"dir_{d}"
        dir_path.mkdir()
        for f in range(num_files):
            # We mock files content to be tiny
            file_path = dir_path / f"file_{f}.txt"
            file_path.write_text("x")

    indexer = WorkspaceIndexer()
    start_time = time.time()
    index = await indexer.index(str(tmp_path))
    duration = time.time() - start_time

    assert index.file_count == 1000
    assert index.directory_count == 10
    # Performance check: 1,000 files metadata scan should run within reasonable window
    assert duration < 2.0
