import os
import pytest
from datetime import datetime, UTC
from pathlib import Path
from unittest.mock import patch, MagicMock

from core.intents import Intent
from core.models import AssistantRequest, ExecutionPlan
from core.planner import Planner
from capabilities.files.folder_service import FolderService
from capabilities.files.file_capability import FileCapability


def test_validate_folder_name():
    service = FolderService()
    assert service.validate_folder_name("AI Notes") is True
    assert service.validate_folder_name("Semester 5") is True
    assert service.validate_folder_name("Valid-Name_123") is True

    assert service.validate_folder_name("") is False
    assert service.validate_folder_name("   ") is False
    assert service.validate_folder_name("a/b") is False
    assert service.validate_folder_name("a\\b") is False
    assert service.validate_folder_name("a:b") is False
    assert service.validate_folder_name("a*b") is False
    assert service.validate_folder_name("a?b") is False
    assert service.validate_folder_name("a\"b") is False
    assert service.validate_folder_name("a<b") is False
    assert service.validate_folder_name("a>b") is False
    assert service.validate_folder_name("a|b") is False
    assert service.validate_folder_name(".") is False
    assert service.validate_folder_name("..") is False
    assert service.validate_folder_name(None) is False


def test_create_folder_success(tmp_path):
    service = FolderService()
    parent = tmp_path / "parent"
    parent.mkdir()

    res = service.create_folder("New Folder", str(parent))
    assert res["status"] == "success"
    assert "New Folder" in res["message"]
    assert Path(res["path"]).exists()
    assert Path(res["path"]).is_dir()


def test_create_folder_invalid_name(tmp_path):
    service = FolderService()
    res = service.create_folder("New/Folder", str(tmp_path))
    assert res["status"] == "error"
    assert res["error_class"] == "ValueError"


def test_create_folder_parent_not_found(tmp_path):
    service = FolderService()
    non_existent = tmp_path / "non_existent"
    res = service.create_folder("Folder", str(non_existent))
    assert res["status"] == "error"
    assert res["error_class"] == "FileNotFoundError"


def test_create_folder_already_exists(tmp_path):
    service = FolderService()
    existing = tmp_path / "Existing"
    existing.mkdir()

    res = service.create_folder("Existing", str(tmp_path))
    assert res["status"] == "error"
    assert res["error_class"] == "FileExistsError"


@patch("capabilities.files.folder_service.send2trash")
def test_delete_folder_success(mock_send2trash, tmp_path):
    service = FolderService()
    folder = tmp_path / "to_delete"
    folder.mkdir()

    res = service.delete_folder(str(folder))
    assert res["status"] == "success"
    assert "to_delete" in res["message"]
    mock_send2trash.assert_called_once_with(str(folder.resolve()))


def test_delete_folder_not_found(tmp_path):
    service = FolderService()
    non_existent = tmp_path / "non_existent"
    res = service.delete_folder(str(non_existent))
    assert res["status"] == "error"
    assert res["error_class"] == "FileNotFoundError"


def test_delete_folder_not_a_directory(tmp_path):
    service = FolderService()
    file_path = tmp_path / "file.txt"
    file_path.write_text("not a folder")

    res = service.delete_folder(str(file_path))
    assert res["status"] == "error"
    assert res["error_class"] == "ValueError"


def test_delete_protected_folder():
    service = FolderService()
    home = Path.home().resolve()

    # Try deleting user's profile home directory
    res = service.delete_folder(str(home))
    assert res["status"] == "error"
    assert res["error_class"] == "PermissionError"

    # Try deleting standard folder
    desktop = (home / "Desktop").resolve()
    # Mocking folder existence so safety checks trigger
    with patch.object(Path, "exists", return_value=True), \
         patch.object(Path, "is_dir", return_value=True):
        res = service.delete_folder(str(desktop))
        assert res["status"] == "error"
        assert res["error_class"] == "PermissionError"


def test_planner_folder_intents():
    planner = Planner()

    # Test CREATE_FOLDER detection and parameter extraction
    req1 = AssistantRequest(message="Create folder AI Notes", source="test", timestamp=datetime.now(UTC))
    plan1 = planner.create_plan(req1)
    assert plan1.intent == Intent.CREATE_FOLDER
    assert plan1.target == "AI Notes"
    assert plan1.parameters["folder_name"] == "AI Notes"
    assert plan1.parameters["destination_folder"] is None

    req2 = AssistantRequest(message="Create folder Semester 5 in Documents", source="test", timestamp=datetime.now(UTC))
    plan2 = planner.create_plan(req2)
    assert plan2.intent == Intent.CREATE_FOLDER
    assert plan2.target == "Semester 5"
    assert plan2.parameters["folder_name"] == "Semester 5"
    assert plan2.parameters["destination_folder"] == "Documents"

    # Test DELETE_FOLDER detection and parameter extraction
    req3 = AssistantRequest(message="Delete folder Old Project", source="test", timestamp=datetime.now(UTC))
    plan3 = planner.create_plan(req3)
    assert plan3.intent == Intent.DELETE_FOLDER
    assert plan3.target == "Old Project"
    assert plan3.parameters["folder_name"] == "Old Project"


@patch("capabilities.files.folder_service.send2trash")
def test_file_capability_create_and_delete(mock_send2trash, tmp_path):
    capability = FileCapability()

    # Mock PathResolver so it resolves "Documents" to tmp_path
    with patch.object(capability._path_resolver, "resolve", return_value=str(tmp_path)):
        # Test create plan execution
        plan_create = ExecutionPlan(
            intent=Intent.CREATE_FOLDER,
            target="Semester 5",
            parameters={"folder_name": "Semester 5", "destination_folder": "Documents"},
            confidence=0.9
        )
        res_create = capability.execute_plan(plan_create)
        assert res_create.success is True
        assert (tmp_path / "Semester 5").exists()

        # Test delete plan execution
        # First mock search engine to find the folder we just created
        with patch.object(capability._search_engine, "search", return_value=[str(tmp_path / "Semester 5")]):
            plan_delete = ExecutionPlan(
                intent=Intent.DELETE_FOLDER,
                target="Semester 5",
                parameters={"folder_name": "Semester 5"},
                confidence=0.9
            )
            res_delete = capability.execute_plan(plan_delete)
            assert res_delete.success is True
            mock_send2trash.assert_called_once_with(str((tmp_path / "Semester 5").resolve()))
