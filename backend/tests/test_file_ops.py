import os
# pyrefly: ignore [missing-import]
import pytest
from unittest.mock import patch, MagicMock
from capabilities.files.file_operations import search_files


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


@patch("capabilities.files.file_operations.search_files")
def test_execute_action_search(mock_search_files):
    from capabilities.files.file_operations import execute_action

    # Case 1: Results found
    mock_search_files.return_value = [
        {"name": "file1.txt", "path": "path/to/file1.txt", "type": ".txt"}
    ]
    action_data = {"action": "search", "target": "file1"}
    res = execute_action(action_data)
    assert res == {
        "count": 1,
        "results": [{"name": "file1.txt", "path": "path/to/file1.txt", "type": ".txt"}]
    }

    # Case 2: No results found
    mock_search_files.return_value = []
    action_data = {"action": "search", "target": "missing"}
    res = execute_action(action_data)
    assert res == "No files found matching 'missing'"


def test_format_speak_message():
    from utils.helpers import format_speak_message

    # Test No results cases
    parsed_action = {"action": "search", "target": "report"}
    assert format_speak_message([], parsed_action) == "I couldn't find any files named report."
    assert format_speak_message("No files found matching 'report'", parsed_action) == "I couldn't find any files named report."
    assert format_speak_message({"count": 0, "results": []}, parsed_action) == "I couldn't find any files named report."

    # Test Single result cases
    parsed_action = {"action": "search", "target": "report.pdf"}
    single_res = {
        "count": 1,
        "results": [
            {"name": "report.pdf", "path": "C:\\Users\\User\\Documents\\report.pdf", "type": ".pdf"}
        ]
    }
    assert format_speak_message(single_res, parsed_action) == "I found report.pdf in Documents."

    # Test Single result in other folder cases
    single_res_downloads = {
        "count": 1,
        "results": [
            {"name": "report.pdf", "path": "C:\\Users\\User\\Downloads\\report.pdf", "type": ".pdf"}
        ]
    }
    assert format_speak_message(single_res_downloads, parsed_action) == "I found report.pdf in Downloads."

    # Test Multiple results cases
    parsed_action = {"action": "search", "target": "report"}
    multi_res = {
        "count": 5,
        "results": [{"name": f"file_{i}.txt", "path": f"path/file_{i}.txt", "type": ".txt"} for i in range(5)]
    }
    assert format_speak_message(multi_res, parsed_action) == "I found 5 matching files."

    # Test other commands formatting
    assert format_speak_message("Opened downloads", {"action": "open", "target": "downloads"}) == "Opened downloads"
    assert format_speak_message("Folder 'college' created", {"action": "create_folder", "target": "college"}) == "Folder created successfully"
    assert format_speak_message("report.pdf not found", {"action": "delete", "target": "report.pdf"}) == "report.pdf not found"


