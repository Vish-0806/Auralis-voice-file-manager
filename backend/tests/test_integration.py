import os
import pytest
from datetime import datetime, UTC
from pathlib import Path
from unittest.mock import patch, MagicMock

from core.assistant import AuralisAssistant
from core.dispatcher import ActionDispatcher
from core.planner import Planner
from core.models import AssistantRequest, SessionContext
from core.intents import Intent
from capabilities.files.file_capability import FileCapability


@pytest.fixture
def setup_integration_env(tmp_path):
    """Sets up a mock home directory structure for path resolution."""

    home = tmp_path / "home"
    home.mkdir()
    (home / "Desktop").mkdir()
    (home / "Downloads").mkdir()
    (home / "Documents").mkdir()
    (home / "Pictures").mkdir()

    # Mock Path.home() and expanduser to point to our test home directory
    with patch("pathlib.Path.home", return_value=home), \
         patch("capabilities.files.folder_service.Path.home", return_value=home), \
         patch("capabilities.files.path_resolver.Path.home", return_value=home):
        yield home


@patch("capabilities.files.file_capability.os.startfile")
def test_integration_open_folder(mock_startfile, setup_integration_env):
    home = setup_integration_env
    planner = Planner()
    file_capability = FileCapability()
    dispatcher = ActionDispatcher(capabilities={file_capability.name: file_capability})
    assistant = AuralisAssistant(planner=planner, dispatcher=dispatcher)

    req = AssistantRequest(
        message="open documents",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)

    assert res.result.success is True
    assert res.plan.intent == Intent.OPEN_FOLDER
    mock_startfile.assert_called_once_with(str((home / "Documents").resolve()))


def test_integration_search_file(setup_integration_env):
    home = setup_integration_env
    planner = Planner()
    file_capability = FileCapability()
    dispatcher = ActionDispatcher(capabilities={file_capability.name: file_capability})
    assistant = AuralisAssistant(planner=planner, dispatcher=dispatcher)

    # Place a file to search
    search_target = home / "Desktop" / "report.pdf"
    search_target.write_text("dummy")

    req = AssistantRequest(
        message="find report.pdf",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)

    assert res.result.success is True
    assert res.plan.intent == Intent.SEARCH_FILE
    assert "report.pdf" in res.response


def test_integration_create_folder(setup_integration_env):
    home = setup_integration_env
    planner = Planner()
    file_capability = FileCapability()
    dispatcher = ActionDispatcher(capabilities={file_capability.name: file_capability})
    assistant = AuralisAssistant(planner=planner, dispatcher=dispatcher)

    req = AssistantRequest(
        message="create folder AI Notes in Documents",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)

    assert res.result.success is True
    assert res.plan.intent == Intent.CREATE_FOLDER
    assert (home / "Documents" / "AI Notes").exists()
    assert (home / "Documents" / "AI Notes").is_dir()


@patch("capabilities.files.folder_service.send2trash")
def test_integration_delete_folder(mock_send2trash, setup_integration_env):
    home = setup_integration_env
    planner = Planner()
    file_capability = FileCapability()
    dispatcher = ActionDispatcher(capabilities={file_capability.name: file_capability})
    assistant = AuralisAssistant(planner=planner, dispatcher=dispatcher)

    # Place a folder to delete
    target_dir = home / "Documents" / "Old Project"
    target_dir.mkdir()

    req = AssistantRequest(
        message="delete folder Old Project",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)

    assert res.result.success is True
    assert res.plan.intent == Intent.DELETE_FOLDER
    mock_send2trash.assert_called_once_with(str(target_dir.resolve()))


def test_integration_organize_downloads(setup_integration_env):
    home = setup_integration_env
    planner = Planner()
    file_capability = FileCapability()
    dispatcher = ActionDispatcher(capabilities={file_capability.name: file_capability})
    assistant = AuralisAssistant(planner=planner, dispatcher=dispatcher)

    # Place files in downloads
    pdf_file = home / "Downloads" / "slide.pdf"
    pdf_file.write_text("pdf")
    txt_file = home / "Downloads" / "notes.txt"
    txt_file.write_text("text")

    req = AssistantRequest(
        message="Organize my Downloads",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)

    assert res.result.success is True
    assert res.plan.intent == Intent.ORGANIZE_FOLDER
    assert (home / "Downloads" / "PDF" / "slide.pdf").exists()
    assert (home / "Downloads" / "Text" / "notes.txt").exists()


def test_integration_file_information(setup_integration_env):
    home = setup_integration_env
    planner = Planner()
    file_capability = FileCapability()
    dispatcher = ActionDispatcher(capabilities={file_capability.name: file_capability})
    assistant = AuralisAssistant(planner=planner, dispatcher=dispatcher)

    # Place a file to inspect
    target_file = home / "Documents" / "info.txt"
    target_file.write_text("hello world")

    req = AssistantRequest(
        message="show information about info.txt",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)

    assert res.result.success is True
    assert res.plan.intent == Intent.GET_FILE_INFO
    assert "File Information for info.txt" in res.response
    assert "Type: Text Document" in res.response
    assert "Size: 11 bytes" in res.response
