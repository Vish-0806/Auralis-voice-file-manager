"""Unit tests for FilesystemSearchService (Phase 11.2)."""

import pytest
from brain.os.filesystem import FilesystemSearchService, SearchResult


def test_search_service_query_and_extension(tmp_path) -> None:
    d = tmp_path / "search_dir"
    d.mkdir()

    (d / "report_2026.pdf").write_bytes(b"%PDF sample")
    (d / "report_2026.txt").write_text("text sample")
    (d / "notes.txt").write_text("notes sample")

    sub = d / "deep"
    sub.mkdir()
    (sub / "report_sub.pdf").write_bytes(b"%PDF deep")

    svc = FilesystemSearchService()

    # Search by query
    res1 = svc.search(str(d), query="report")
    assert isinstance(res1, SearchResult)
    assert res1.total_matches == 3

    # Search by extension
    res2 = svc.search(str(d), extension=".pdf")
    assert res2.total_matches == 2

    # Search non-recursive
    res3 = svc.search(str(d), query="report", recursive=False)
    assert res3.total_matches == 2


def test_search_service_pattern_and_regex(tmp_path) -> None:
    d = tmp_path / "search_patterns"
    d.mkdir()

    (d / "image001.png").write_bytes(b"png")
    (d / "image002.jpg").write_bytes(b"jpg")
    (d / "data.csv").write_text("a,b,c")

    svc = FilesystemSearchService()

    # Glob pattern match
    res1 = svc.search(str(d), pattern="image*.png")
    assert res1.total_matches == 1
    assert res1.matches[0].name == "image001.png"

    # Regex match
    res2 = svc.search(str(d), regex=r"image\d{3}\.(png|jpg)")
    assert res2.total_matches == 2
