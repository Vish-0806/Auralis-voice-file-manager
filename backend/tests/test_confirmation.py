import os
import pytest
from unittest.mock import patch
from ai_engine.intent_classifier import classify_intent
from file_engine.file_operations import execute_action, set_pending_action, get_pending_action
from utils.helpers import format_speak_message


def test_confirmation_intent_classification():
    # Confirm
    assert classify_intent("yes") == "confirm"
    assert classify_intent("yep") == "confirm"
    assert classify_intent("sure") == "confirm"
    assert classify_intent("ok") == "confirm"
    assert classify_intent("okay") == "confirm"

    # Cancel
    assert classify_intent("no") == "cancel"
    assert classify_intent("nope") == "cancel"
    assert classify_intent("cancel") == "cancel"
    assert classify_intent("stop") == "cancel"


def test_no_action_pending():
    set_pending_action(None)
    
    res1 = execute_action({"action": "confirm", "target": ""})
    assert res1 == "No action pending confirmation"
    
    res2 = execute_action({"action": "cancel", "target": ""})
    assert res2 == "No action pending confirmation"

    assert format_speak_message(res1, {"action": "confirm"}) == "There is no action pending confirmation."
    assert format_speak_message(res2, {"action": "cancel"}) == "There is no action pending confirmation."


def test_delete_confirmation_flow(tmp_path):
    # Ensure no pending action
    set_pending_action(None)

    temp_file = tmp_path / "report.pdf"
    temp_file.write_text("dummy")

    action_data = {
        "action": "delete",
        "target": str(temp_file)
    }

    # Step 1: Initial delete request
    res = execute_action(action_data)
    assert isinstance(res, dict)
    assert res["status"] == "pending_confirmation"
    assert "delete" in res["message"]
    assert os.path.exists(str(temp_file))

    # Verify pending action is stored
    assert get_pending_action() == action_data

    # Step 2: Confirm action
    confirm_res = execute_action({"action": "confirm", "target": ""})
    assert confirm_res == f"{str(temp_file)} deleted"
    
    # File should be deleted
    assert not os.path.exists(str(temp_file))
    assert get_pending_action() is None


def test_delete_cancel_flow(tmp_path):
    # Ensure no pending action
    set_pending_action(None)

    temp_file = tmp_path / "report.pdf"
    temp_file.write_text("dummy")

    action_data = {
        "action": "delete",
        "target": str(temp_file)
    }

    # Step 1: Initial delete request
    res = execute_action(action_data)
    assert isinstance(res, dict)
    assert res["status"] == "pending_confirmation"

    # Step 2: Cancel action
    cancel_res = execute_action({"action": "cancel", "target": ""})
    assert cancel_res == "Action cancelled"
    
    # File should still exist
    assert os.path.exists(str(temp_file))
    assert get_pending_action() is None
    assert format_speak_message(cancel_res, {"action": "cancel"}) == "Action cancelled."


@patch("file_engine.source_resolver.search_files")
@patch("file_engine.file_operations.get_location_path")
@patch("file_engine.transfer.move_item")
def test_move_confirmation_flow(mock_move_item, mock_get_location, mock_search):
    # Ensure no pending action
    set_pending_action(None)

    mock_search.return_value = [
        {"name": "report.pdf", "path": "/mock/report.pdf", "type": ".pdf"}
    ]
    mock_get_location.return_value = "/mock/documents"
    mock_move_item.return_value = {
        "status": "success",
        "message": "Successfully moved",
        "source": "/mock/report.pdf",
        "destination": "/mock/documents/report.pdf"
    }

    action_data = {
        "action": "move",
        "target": "report.pdf",
        "destination": "documents"
    }

    # Step 1: Initial move request
    res = execute_action(action_data)
    assert isinstance(res, dict)
    assert res["status"] == "pending_confirmation"
    assert "Are you sure you want to move report.pdf to Documents?" in res["message"]

    # Step 2: Confirm
    confirm_res = execute_action({"action": "confirm", "target": ""})
    assert isinstance(confirm_res, dict)
    assert confirm_res["status"] == "success"
    assert confirm_res["message"] == "Moved report.pdf to Documents."
    mock_move_item.assert_called_once_with("/mock/report.pdf", "/mock/documents")
    assert get_pending_action() is None
