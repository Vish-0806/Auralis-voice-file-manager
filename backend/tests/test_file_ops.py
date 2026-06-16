import os
import pytest
from unittest.mock import patch, MagicMock
from file_engine.search_engine import search_files


def test_search_files_empty_query():
    # Empty query or whitespace query should return empty list
    assert search_files("") == []
    assert search_files("   ") == []
    assert search_files(None) == []


@patch("os.path.exists")
@patch("os.walk")
def test_search_files_matching(mock_walk, mock_exists):
    # Mock exists to always return True for Desktop/Documents/Downloads
    mock_exists.return_value = True

    # Setup mock data for walk
    # os.walk yields (root, dirs, files)
    mock_walk.side_effect = [
        # Desktop
        [
            ("C:\\Users\\User\\Desktop", [], ["report.pdf", "notes.txt", "vacation_pic.jpg"])
        ],
        # Documents
        [
            ("C:\\Users\\User\\Documents", ["Subfolder"], ["Resume.docx", "Project_Report.xlsx"]),
            ("C:\\Users\\User\\Documents\\Subfolder", [], ["draft.txt"])
        ],
        # Downloads
        [
            ("C:\\Users\\User\\Downloads", [], ["setup.exe", "report_draft.pdf"])
        ]
    ]

    # Test exact match
    results_exact = search_files("setup.exe")
    assert len(results_exact) == 1
    assert results_exact[0]["name"] == "setup.exe"
    assert results_exact[0]["path"] == "C:\\Users\\User\\Downloads\\setup.exe"
    assert results_exact[0]["type"] == ".exe"

    # Reset mock for subsequent tests
    mock_walk.side_effect = [
        [("C:\\Users\\User\\Desktop", [], ["report.pdf", "notes.txt"])],
        [("C:\\Users\\User\\Documents", [], ["Resume.docx", "Project_Report.xlsx"])],
        [("C:\\Users\\User\\Downloads", [], ["setup.exe", "report_draft.pdf"])]
    ]

    # Test partial match
    results_partial = search_files("report")
    # Should find report.pdf, Project_Report.xlsx, report_draft.pdf
    assert len(results_partial) == 3
    names = [r["name"] for r in results_partial]
    assert "report.pdf" in names
    assert "Project_Report.xlsx" in names
    assert "report_draft.pdf" in names

    # Reset mock for case-insensitive test
    mock_walk.side_effect = [
        [("C:\\Users\\User\\Desktop", [], ["REPORT.pdf"])],
        [("C:\\Users\\User\\Documents", [], ["resume.docx"])],
        [("C:\\Users\\User\\Downloads", [], [])]
    ]

    # Test case-insensitivity
    results_case = search_files("report")
    assert len(results_case) == 1
    assert results_case[0]["name"] == "REPORT.pdf"


@patch("os.path.exists")
@patch("os.walk")
def test_search_files_limit(mock_walk, mock_exists):
    mock_exists.return_value = True

    # Generate 30 matching files
    desktop_files = [f"file_{i}.txt" for i in range(30)]
    mock_walk.side_effect = [
        [("C:\\Users\\User\\Desktop", [], desktop_files)],
        [],
        []
    ]

    results = search_files("file_")
    # Result must be limited to exactly 20 matches
    assert len(results) == 20
    # Ensure they are the first 20
    assert results[0]["name"] == "file_0.txt"
    assert results[19]["name"] == "file_19.txt"


@patch("os.path.exists")
@patch("os.walk")
def test_search_files_permission_error(mock_walk, mock_exists):
    mock_exists.return_value = True

    # We want to simulate a situation where accessing Desktop triggers the onerror callback,
    # but walking Documents and Downloads succeeds.
    def walk_side_effect(search_dir, topdown=True, onerror=None):
        if "Desktop" in search_dir:
            # Call the onerror handler with a mock PermissionError
            if onerror:
                exc = PermissionError("Permission denied to Desktop")
                exc.filename = search_dir
                onerror(exc)
            # Yield nothing since it failed
            return iter([])
        elif "Documents" in search_dir:
            # Returns a valid file
            return iter([("C:\\Users\\User\\Documents", [], ["secret.txt"])])
        else:
            return iter([])

    mock_walk.side_effect = walk_side_effect

    # Execute search
    results = search_files("secret.txt")

    # Should have bypassed the Desktop error and successfully matched in Documents
    assert len(results) == 1
    assert results[0]["name"] == "secret.txt"
    assert results[0]["path"] == "C:\\Users\\User\\Documents\\secret.txt"
