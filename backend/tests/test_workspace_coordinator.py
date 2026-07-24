"""Unit tests for WorkspaceIntelligenceCoordinator and WorkspaceCache."""

import time
# pyrefly: ignore [missing-import]
import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime, timezone
from memory.workspace import (
    WorkspaceIntelligenceCoordinator,
    WorkspaceCache,
    WorkspaceAnalysis,
    WorkspaceIndex,
)


@pytest.fixture
def mock_analysis() -> WorkspaceAnalysis:
    """Fixture providing a mock WorkspaceAnalysis."""
    return WorkspaceAnalysis(
        workspace_path="/test/path",
        project_name="path",
        project_type="python",
        repository_type="git",
        dominant_language="Python",
        language_statistics={"Python": 1.0},
        language_counts={"Python": 1},
        build_system="pip",
        recommended_build_command="pip install -r requirements.txt",
        git_branch="main",
        git_remote_available=True,
        git_dirty=False,
        git_has_unpushed_commits=False,
        total_files=1,
        total_directories=0,
        maximum_depth=1,
        total_size=100,
        last_indexed=datetime.now(timezone.utc),
        analysis_timestamp=datetime.now(timezone.utc),
    )


def test_workspace_cache_ttl_and_operations(mock_analysis) -> None:
    """Verify that WorkspaceCache sets, gets, expires, invalidates and clears successfully."""
    # Custom TTL of 0.05 seconds
    cache = WorkspaceCache(ttl_seconds=0.05)
    path = "/test/path"

    # 1. Miss
    assert cache.get(path) is None

    # 2. Set and Hit
    cache.set(path, mock_analysis)
    assert cache.get(path) == mock_analysis

    # 3. Expiration
    time.sleep(0.06)
    assert cache.get(path) is None  # Should be expired

    # 4. Invalidation
    cache.set(path, mock_analysis)
    cache.invalidate(path)
    assert cache.get(path) is None

    # 5. Clear
    cache.set(path, mock_analysis)
    cache.clear()
    assert cache.get(path) is None


@pytest.mark.anyio
async def test_coordinator_cache_hits_and_misses(mock_analysis) -> None:
    """Verify that coordinator retrieves from cache or triggers fresh indexings."""
    mock_indexer = MagicMock()
    mock_indexer.index = AsyncMock()
    # Mock index return
    mock_index = WorkspaceIndex(
        workspace_path="/test/path",
        directories=[],
        files={},
        directory_count=0,
        file_count=0,
        total_size=0,
        maximum_depth=0,
        indexed_at=datetime.now(timezone.utc),
    )
    mock_indexer.index.return_value = mock_index

    mock_engine = MagicMock()
    mock_engine.analyze = AsyncMock()
    mock_engine.analyze.return_value = mock_analysis

    # Initalize coordinator with 1 second TTL
    coordinator = WorkspaceIntelligenceCoordinator(
        indexer=mock_indexer,
        engine=mock_engine,
        cache_ttl=1.0
    )

    path = "/test/path"

    # 1. Miss - Should trigger scan and analyze
    res1 = await coordinator.analyze(path)
    assert res1 == mock_analysis
    assert mock_indexer.index.call_count == 1
    assert mock_engine.analyze.call_count == 1

    # 2. Hit - Should pull from cache directly
    res2 = await coordinator.analyze(path)
    assert res2 == mock_analysis
    assert mock_indexer.index.call_count == 1  # Should not increase
    assert mock_engine.analyze.call_count == 1

    # 3. Force Refresh - Should bypass cache
    res3 = await coordinator.refresh(path)
    assert res3 == mock_analysis
    assert mock_indexer.index.call_count == 2
    assert mock_engine.analyze.call_count == 2
