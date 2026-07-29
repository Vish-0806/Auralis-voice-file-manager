"""Unit tests for SearchEngine (Phase 9.5)."""

import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

# pyrefly: ignore [missing-import]
import pytest

from brain.filesystem import SearchEngine, SearchResult, SortField, SortOrder


@pytest.fixture
def search_dir(tmp_path: Path) -> str:
    """Create a structured directory tree for search tests."""
    # Root level
    (tmp_path / "alpha.txt").write_text("a" * 100)
    (tmp_path / "beta.py").write_text("b" * 200)
    (tmp_path / "gamma.txt").write_text("c" * 50)
    (tmp_path / ".hidden_file").write_text("h" * 10)

    # Subdir
    sub = tmp_path / "subdir"
    sub.mkdir()
    (sub / "delta.txt").write_text("d" * 300)
    (sub / "epsilon.py").write_text("e" * 400)

    # Nested
    deep = sub / "deep"
    deep.mkdir()
    (deep / "zeta.txt").write_text("z" * 150)
    (deep / "eta.log").write_text("l" * 75)

    return str(tmp_path)


@pytest.fixture
def engine() -> SearchEngine:
    return SearchEngine()


# ---------------------------------------------------------------------------
# Basic Search
# ---------------------------------------------------------------------------

def test_search_all_files(engine: SearchEngine, search_dir: str) -> None:
    result = engine.search(search_dir, pattern="*", recursive=True)
    assert isinstance(result, SearchResult)
    assert result.total_matches >= 7


def test_search_nonexistent_root(engine: SearchEngine, tmp_path: Path) -> None:
    result = engine.search(str(tmp_path / "ghost"), pattern="*")
    assert result.total_matches == 0
    assert "error" in result.metadata


def test_search_non_recursive(engine: SearchEngine, search_dir: str) -> None:
    result = engine.search(search_dir, pattern="*", recursive=False)
    # Should only return root-level items
    assert result.total_matches == 4  # alpha.txt, beta.py, gamma.txt, .hidden_file


# ---------------------------------------------------------------------------
# Pattern Matching
# ---------------------------------------------------------------------------

def test_search_wildcard_txt(engine: SearchEngine, search_dir: str) -> None:
    result = engine.search(search_dir, pattern="*.txt", recursive=True)
    assert result.total_matches >= 4
    assert all(m.extension == ".txt" for m in result.matches)


def test_search_wildcard_py(engine: SearchEngine, search_dir: str) -> None:
    result = engine.search(search_dir, pattern="*.py", recursive=True)
    assert result.total_matches == 2
    assert all(m.extension == ".py" for m in result.matches)


def test_search_regex_pattern(engine: SearchEngine, search_dir: str) -> None:
    result = engine.search(search_dir, pattern=r"^(alpha|beta)\.", recursive=True, use_regex=True)
    assert result.total_matches == 2


def test_search_invalid_regex(engine: SearchEngine, search_dir: str) -> None:
    result = engine.search(search_dir, pattern="[invalid", recursive=True, use_regex=True)
    assert "error" in result.metadata


def test_search_case_insensitive_wildcard(engine: SearchEngine, search_dir: str) -> None:
    result = engine.search(search_dir, pattern="*.TXT", recursive=True)
    assert result.total_matches >= 4


# ---------------------------------------------------------------------------
# Extension Filter
# ---------------------------------------------------------------------------

def test_search_extension_filter_txt(engine: SearchEngine, search_dir: str) -> None:
    result = engine.search(search_dir, pattern="*", extensions=[".txt"], recursive=True)
    assert result.total_matches >= 4
    assert all(m.extension == ".txt" for m in result.matches)


def test_search_extension_filter_without_dot(engine: SearchEngine, search_dir: str) -> None:
    result = engine.search(search_dir, pattern="*", extensions=["log"], recursive=True)
    assert result.total_matches == 1


def test_search_extension_filter_multiple(engine: SearchEngine, search_dir: str) -> None:
    result = engine.search(search_dir, pattern="*", extensions=[".txt", ".py"], recursive=True)
    assert result.total_matches >= 6


# ---------------------------------------------------------------------------
# Size Filter
# ---------------------------------------------------------------------------

def test_search_min_size_filter(engine: SearchEngine, search_dir: str) -> None:
    result = engine.search(search_dir, pattern="*", min_size_bytes=200, recursive=True)
    # Files >= 200 bytes: beta.py(200), delta.txt(300), epsilon.py(400)
    assert all(m.size_bytes >= 200 for m in result.matches)


def test_search_max_size_filter(engine: SearchEngine, search_dir: str) -> None:
    result = engine.search(search_dir, pattern="*", max_size_bytes=100, recursive=True)
    assert all(m.size_bytes <= 100 for m in result.matches)


def test_search_size_range(engine: SearchEngine, search_dir: str) -> None:
    result = engine.search(search_dir, pattern="*", min_size_bytes=50, max_size_bytes=200, recursive=True)
    assert all(50 <= m.size_bytes <= 200 for m in result.matches)


# ---------------------------------------------------------------------------
# Date Filter
# ---------------------------------------------------------------------------

def test_search_modified_after_old_date(engine: SearchEngine, search_dir: str) -> None:
    old = datetime(2000, 1, 1, tzinfo=timezone.utc)
    result = engine.search(search_dir, pattern="*", modified_after=old, recursive=True)
    assert result.total_matches >= 7


def test_search_modified_before_future_date(engine: SearchEngine, search_dir: str) -> None:
    future = datetime(2099, 12, 31, tzinfo=timezone.utc)
    result = engine.search(search_dir, pattern="*", modified_before=future, recursive=True)
    assert result.total_matches >= 7


def test_search_modified_after_future_date_empty(engine: SearchEngine, search_dir: str) -> None:
    future = datetime(2099, 12, 31, tzinfo=timezone.utc)
    result = engine.search(search_dir, pattern="*", modified_after=future, recursive=True)
    assert result.total_matches == 0


# ---------------------------------------------------------------------------
# Sorting
# ---------------------------------------------------------------------------

def test_search_sort_by_name_ascending(engine: SearchEngine, search_dir: str) -> None:
    result = engine.search(search_dir, pattern="*.txt", recursive=True,
                           sort_by=SortField.NAME, sort_order=SortOrder.ASCENDING)
    names = [m.name for m in result.matches]
    assert names == sorted(names, key=str.lower)


def test_search_sort_by_name_descending(engine: SearchEngine, search_dir: str) -> None:
    result = engine.search(search_dir, pattern="*.txt", recursive=True,
                           sort_by=SortField.NAME, sort_order=SortOrder.DESCENDING)
    names = [m.name for m in result.matches]
    assert names == sorted(names, key=str.lower, reverse=True)


def test_search_sort_by_size(engine: SearchEngine, search_dir: str) -> None:
    result = engine.search(search_dir, pattern="*.txt", recursive=True,
                           sort_by=SortField.SIZE, sort_order=SortOrder.ASCENDING)
    sizes = [m.size_bytes for m in result.matches]
    assert sizes == sorted(sizes)


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------

def test_search_pagination_first_page(engine: SearchEngine, search_dir: str) -> None:
    result = engine.search(search_dir, pattern="*", recursive=True, page=1, page_size=3)
    assert len(result.matches) <= 3
    assert result.page == 1


def test_search_pagination_total_pages(engine: SearchEngine, search_dir: str) -> None:
    result = engine.search(search_dir, pattern="*", recursive=True, page_size=2)
    assert result.total_pages >= 4


def test_search_pagination_beyond_last_page(engine: SearchEngine, search_dir: str) -> None:
    result = engine.search(search_dir, pattern="*", recursive=True, page=999, page_size=10)
    assert len(result.matches) == 0
    assert result.total_matches > 0


def test_search_duration_populated(engine: SearchEngine, search_dir: str) -> None:
    result = engine.search(search_dir, pattern="*")
    assert result.duration_ms >= 0.0
