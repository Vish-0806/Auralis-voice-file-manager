import os
# pyrefly: ignore [missing-import]
import pytest
from unittest.mock import patch, MagicMock
from capabilities.files.file_operations import resolve_source, execute_action
from utils.helpers import format_speak_message


def test_resolve_source_empty():
    res = resolve_source("")
    assert res["status"] == "error"
    assert res["error_class"] == "ValueError"


def test_resolve_source_exists_on_disk(tmp_path):
    temp_file = tmp_path / "exist.txt"
    temp_file.write_text("content")

    res = resolve_source(str(temp_file))
    assert res["status"] == "success"
    assert res["path"] == os.path.abspath(str(temp_file))
    assert "exists on disk" in res["message"]


@patch("capabilities.files.file_operations.search_files")
def test_resolve_source_single_match(mock_search):
    mock_search.return_value = [
        {"name": "unique.txt", "path": "/mock/unique.txt", "type": ".txt"}
    ]

    res = resolve_source("unique.txt")
    assert res["status"] == "success"
    assert res["path"] == "/mock/unique.txt"
    assert "exactly one" in res["message"]


@patch("capabilities.files.file_operations.search_files")
def test_resolve_source_multiple_matches(mock_search):
    mock_search.return_value = [
        {"name": "match.txt", "path": "/mock/1/match.txt", "type": ".txt"},
        {"name": "match.txt", "path": "/mock/2/match.txt", "type": ".txt"},
    ]

    res = resolve_source("match.txt")
    assert res["status"] == "disambiguation"
    assert len(res["results"]) == 2
    assert res["results"][0]["path"] == "/mock/1/match.txt"


@patch("capabilities.files.file_operations.search_files")
def test_resolve_source_no_match(mock_search):
    mock_search.return_value = []

    res = resolve_source("missing.txt")
    assert res["status"] == "error"
    assert res["error_class"] == "FileNotFoundError"
    assert "not found" in res["message"]


@patch("capabilities.files.file_operations.search_files")
@patch("capabilities.files.file_operations.get_location_path")
@patch("capabilities.files.file_operations.move_item")
def test_execute_action_move_single_match(mock_move_item, mock_get_location, mock_search):
    mock_search.return_value = [
        {"name": "report.pdf", "path": "/mock/report.pdf", "type": ".pdf"}
    ]
    mock_get_location.return_value = "/mock/documents"
    mock_move_item.return_value = {
        "status": "success",
        "message": "Successfully moved report.pdf to report.pdf",
        "source": "/mock/report.pdf",
        "destination": "/mock/documents/report.pdf"
    }

    action_data = {
        "action": "move",
        "target": "report.pdf",
        "destination": "documents",
        "confirmed": True
    }

    res = execute_action(action_data)
    assert isinstance(res, dict)
    assert res["status"] == "success"
    assert res["destination"] == "/mock/documents/report.pdf"
    assert res["message"] == "Moved report.pdf to Documents."
    mock_move_item.assert_called_once_with("/mock/report.pdf", "/mock/documents")


@patch("capabilities.files.file_operations.search_files")
@patch("capabilities.files.file_operations.get_location_path")
@patch("capabilities.files.file_operations.copy_item")
def test_execute_action_copy_single_match(mock_copy_item, mock_get_location, mock_search):
    mock_search.return_value = [
        {"name": "resume.pdf", "path": "/mock/resume.pdf", "type": ".pdf"}
    ]
    mock_get_location.return_value = "/mock/desktop"
    mock_copy_item.return_value = {
        "status": "success",
        "message": "Successfully copied resume.pdf to resume.pdf",
        "source": "/mock/resume.pdf",
        "destination": "/mock/desktop/resume.pdf"
    }

    action_data = {
        "action": "copy",
        "target": "resume.pdf",
        "destination": "desktop"
    }

    res = execute_action(action_data)
    assert isinstance(res, dict)
    assert res["status"] == "success"
    assert res["destination"] == "/mock/desktop/resume.pdf"
    assert res["message"] == "Copied resume.pdf to Desktop."
    mock_copy_item.assert_called_once_with("/mock/resume.pdf", "/mock/desktop")


@patch("capabilities.files.file_operations.search_files")
def test_execute_action_move_multiple_matches(mock_search):
    mock_search.return_value = [
        {"name": "report.pdf", "path": "/mock/1/report.pdf", "type": ".pdf"},
        {"name": "report.pdf", "path": "/mock/2/report.pdf", "type": ".pdf"},
    ]

    action_data = {
        "action": "move",
        "target": "report.pdf",
        "destination": "documents"
    }

    res = execute_action(action_data)
    assert isinstance(res, dict)
    assert res["status"] == "disambiguation"
    assert len(res["results"]) == 2


@patch("capabilities.files.file_operations.search_files")
def test_execute_action_copy_no_match(mock_search):
    mock_search.return_value = []

    action_data = {
        "action": "copy",
        "target": "missing.txt",
        "destination": "desktop"
    }

    res = execute_action(action_data)
    assert isinstance(res, dict)
    assert res["status"] == "error"
    assert res["error_class"] == "FileNotFoundError"


def test_helpers_speak_messages():
    # Disambiguation
    res_disambig = {
        "status": "disambiguation",
        "message": "Multiple files found",
        "results": []
    }
    msg1 = format_speak_message(res_disambig, {"action": "move", "target": "report.pdf"})
    assert "Multiple files found matching report.pdf" in msg1

    # Error
    res_error = {
        "status": "error",
        "message": "File 'report.pdf' not found.",
        "error_class": "FileNotFoundError"
    }
    msg2 = format_speak_message(res_error, {"action": "move", "target": "report.pdf"})
    assert "File 'report.pdf' not found." in msg2

    # Success
    res_success = {
        "status": "success",
        "message": "Successfully moved report.pdf",
        "source": "",
        "destination": ""
    }
    msg3 = format_speak_message(res_success, {"action": "move", "target": "report.pdf"})
    assert "Successfully moved report.pdf" in msg3
