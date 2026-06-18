import os
import pytest
from unittest.mock import patch
from ai_engine.intent_classifier import classify_intent
from file_engine.file_operations import execute_action, set_pending_action, get_pending_action
from utils.helpers import format_speak_message


def test_confirmation_intent_classification():
    # Confirm
    assert classify_intent("yes") == "confirm"
    assert classify_intent("yeah") == "confirm"
    assert classify_intent("yep") == "confirm"
    assert classify_intent("sure") == "confirm"
    assert classify_intent("confirm") == "confirm"
    assert classify_intent("proceed") == "confirm"
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
    pending = get_pending_action()
    assert pending["action"] == "delete"
    assert pending["target"] == str(temp_file)
    assert pending["resolved_source_path"] == str(temp_file)

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


@patch("file_engine.source_resolver.search_files")
def test_move_cancel_flow(mock_search):
    # Ensure no pending action
    set_pending_action(None)

    mock_search.return_value = [
        {"name": "report.pdf", "path": "/mock/report.pdf", "type": ".pdf"}
    ]

    action_data = {
        "action": "move",
        "target": "report.pdf",
        "destination": "documents"
    }

    # Step 1: Initial move request
    res = execute_action(action_data)
    assert isinstance(res, dict)
    assert res["status"] == "pending_confirmation"

    # Step 2: Cancel
    cancel_res = execute_action({"action": "cancel", "target": ""})
    assert cancel_res == "Action cancelled"
    assert get_pending_action() is None


def test_organize_confirmation_flow(tmp_path):
    # Ensure no pending action
    set_pending_action(None)

    # Setup a folder to organize
    downloads_dir = tmp_path / "downloads"
    downloads_dir.mkdir()
    temp_file = downloads_dir / "report.pdf"
    temp_file.write_text("dummy")

    action_data = {
        "action": "organize",
        "target": "downloads"
    }

    # Mock get_target_path to return our temp downloads_dir
    with patch("file_engine.file_operations.get_target_path", return_value=str(downloads_dir)):
        # Step 1: Initial organize request
        res = execute_action(action_data)
        assert isinstance(res, dict)
        assert res["status"] == "pending_confirmation"
        assert res["message"] == "Are you sure you want to organize downloads?"
        assert get_pending_action() == action_data

        # Step 2: Confirm action
        confirm_res = execute_action({"action": "confirm", "target": ""})
        assert "Successfully organized" in confirm_res
        
        # File should be organized into PDFs folder
        assert (downloads_dir / "PDFs" / "report.pdf").exists()
        assert get_pending_action() is None


def test_organize_cancel_flow(tmp_path):
    # Ensure no pending action
    set_pending_action(None)

    # Setup a folder to organize
    downloads_dir = tmp_path / "downloads"
    downloads_dir.mkdir()
    temp_file = downloads_dir / "report.pdf"
    temp_file.write_text("dummy")

    action_data = {
        "action": "organize",
        "target": "downloads"
    }

    # Mock get_target_path to return our temp downloads_dir
    with patch("file_engine.file_operations.get_target_path", return_value=str(downloads_dir)):
        # Step 1: Initial organize request
        res = execute_action(action_data)
        assert isinstance(res, dict)
        assert res["status"] == "pending_confirmation"

        # Step 2: Cancel action
        cancel_res = execute_action({"action": "cancel", "target": ""})
        assert cancel_res == "Action cancelled"
        
        # File should not be organized
        assert temp_file.exists()
        assert not (downloads_dir / "PDFs" / "report.pdf").exists()
        assert get_pending_action() is None


from fastapi.testclient import TestClient
from main import app
client = TestClient(app)

@patch("api.voice_routes.listen")
@patch("api.voice_routes.detect_wake_word")
@patch("api.voice_routes.tts_speak")
def test_voice_route_confirmation_flow(mock_speak, mock_detect, mock_listen):
    set_pending_action(None)
    
    # 1. Simulate there is a pending action (e.g. a delete action)
    action_data = {
        "action": "delete",
        "target": "report.pdf",
        "resolved_source_path": "/mock/report.pdf",
        "confirmed": False
    }
    set_pending_action(action_data)
    
    # 2. Mock user saying "yes"
    mock_listen.return_value = "hey auralis yes"
    mock_detect.return_value = {"activated": True, "cleaned_command": "yes"}
    
    with patch("api.voice_routes.execute_action") as mock_execute:
        mock_execute.return_value = "/mock/report.pdf deleted"
        
        response = client.get("/voice/listen")
        assert response.status_code == 200
        res_json = response.json()
        assert res_json["status"] == "success"
        assert res_json["command"] == "yes"
        assert res_json["parsed_action"] == {"action": "confirm", "target": ""}
        assert res_json["result"] == "/mock/report.pdf deleted"
        
        mock_execute.assert_called_once_with({"action": "confirm", "target": ""})

@patch("api.voice_routes.listen")
@patch("api.voice_routes.detect_wake_word")
@patch("api.voice_routes.tts_speak")
def test_voice_route_cancellation_flow(mock_speak, mock_detect, mock_listen):
    set_pending_action(None)
    
    # 1. Simulate there is a pending action
    action_data = {
        "action": "delete",
        "target": "report.pdf",
        "resolved_source_path": "/mock/report.pdf",
        "confirmed": False
    }
    set_pending_action(action_data)
    
    # 2. Mock user saying "no"
    mock_listen.return_value = "hey auralis no"
    mock_detect.return_value = {"activated": True, "cleaned_command": "no"}
    
    with patch("api.voice_routes.execute_action") as mock_execute:
        mock_execute.return_value = "Action cancelled"
        
        response = client.get("/voice/listen")
        assert response.status_code == 200
        res_json = response.json()
        assert res_json["status"] == "success"
        assert res_json["command"] == "no"
        assert res_json["parsed_action"] == {"action": "cancel", "target": ""}
        assert res_json["result"] == "Action cancelled"
        
        mock_execute.assert_called_once_with({"action": "cancel", "target": ""})

@patch("api.voice_routes.listen")
@patch("api.voice_routes.detect_wake_word")
@patch("api.voice_routes.tts_speak")
def test_voice_route_invalid_flow_when_pending(mock_speak, mock_detect, mock_listen):
    set_pending_action(None)
    
    # 1. Simulate there is a pending action
    action_data = {
        "action": "delete",
        "target": "report.pdf",
        "resolved_source_path": "/mock/report.pdf",
        "confirmed": False
    }
    set_pending_action(action_data)
    
    # 2. Mock user saying something unrelated, e.g. "create folder notes"
    mock_listen.return_value = "hey auralis create folder notes"
    mock_detect.return_value = {"activated": True, "cleaned_command": "create folder notes"}
    
    response = client.get("/voice/listen")
    assert response.status_code == 400
    assert response.json()["detail"] == "Action pending. Please say yes or no."
    
    # Verify mock_speak warned the user
    mock_speak.assert_called_once_with("Action pending. Please say yes or no.")
    
    # Clear state
    set_pending_action(None)
