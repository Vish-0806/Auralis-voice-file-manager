"""Tests for the desktop capability and its subcomponents."""

from __future__ import annotations

import os
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, UTC

from core.assistant import AuralisAssistant
from core.dispatcher import ActionDispatcher
from core.planner import Planner
from core.models import AssistantRequest
from core.intents import Intent
from capabilities.desktop.desktop_capability import DesktopCapability
from capabilities.desktop.application.application_resolver import ApplicationResolver
from capabilities.desktop.application.process_manager import ProcessManager
from capabilities.desktop.application.application_service import ApplicationService


# --- ApplicationResolver Tests ---

def test_resolver_custom_mappings():
    resolver = ApplicationResolver(custom_mappings={"CustomApp": "C:\\path\\to\\app.exe"})
    assert resolver.resolve("CustomApp") == "C:\\path\\to\\app.exe"
    assert resolver.resolve("customapp") == "C:\\path\\to\\app.exe"
    assert resolver.resolve("NonExistent") is None


@patch("capabilities.desktop.application.application_resolver.os.path.exists", return_value=True)
@patch("capabilities.desktop.application.application_resolver.os.path.isfile", return_value=True)
def test_resolver_candidates(mock_isfile, mock_exists):
    resolver = ApplicationResolver()
    resolved = resolver.resolve("Microsoft Edge")
    assert resolved is not None
    assert "msedge.exe" in resolved


@patch("capabilities.desktop.application.application_resolver.os.path.exists", return_value=False)
@patch("capabilities.desktop.application.application_resolver.shutil.which")
def test_resolver_fallback_path(mock_which, mock_exists):
    mock_which.return_value = "C:\\Windows\\System32\\notepad.exe"
    resolver = ApplicationResolver()
    resolved = resolver.resolve("Notepad")
    assert resolved == "C:\\Windows\\System32\\notepad.exe"
    mock_which.assert_called_with("notepad")


# --- ProcessManager Tests ---

@patch("capabilities.desktop.application.process_manager.os.path.exists", return_value=True)
@patch("capabilities.desktop.application.process_manager.os.path.isfile", return_value=True)
@patch("capabilities.desktop.application.process_manager.subprocess.Popen")
def test_process_manager_start(mock_popen, mock_isfile, mock_exists):
    mock_proc = MagicMock()
    mock_proc.pid = 1234
    mock_popen.return_value = mock_proc

    pm = ProcessManager()
    pid = pm.start_process("C:\\path\\to\\app.exe", ["--arg"])
    assert pid == 1234
    mock_popen.assert_called_once()


@patch("capabilities.desktop.application.process_manager.psutil.process_iter")
def test_process_manager_terminate_protected(mock_iter):
    mock_proc = MagicMock()
    mock_proc.info = {"pid": 9999, "name": "explorer.exe"}
    mock_iter.return_value = [mock_proc]

    pm = ProcessManager()
    with pytest.raises(PermissionError):
        pm.terminate_process("explorer", "explorer.exe")


@patch("capabilities.desktop.application.process_manager.psutil.process_iter")
def test_process_manager_terminate_normal(mock_iter):
    mock_proc = MagicMock()
    mock_proc.info = {"pid": 5678, "name": "notepad.exe"}
    mock_iter.return_value = [mock_proc]

    pm = ProcessManager()
    success = pm.terminate_process("notepad", "notepad.exe")
    assert success is True
    mock_proc.terminate.assert_called_once()


@patch("capabilities.desktop.application.process_manager.psutil.process_iter")
def test_process_manager_is_running(mock_iter):
    mock_proc = MagicMock()
    mock_proc.info = {"name": "chrome.exe"}
    mock_iter.return_value = [mock_proc]

    pm = ProcessManager()
    assert pm.is_running("chrome", "chrome.exe") is True
    assert pm.is_running("spotify", "Spotify.exe") is False


# --- ApplicationService Tests ---

@patch("capabilities.desktop.application.application_service.ApplicationResolver.resolve")
@patch("capabilities.desktop.application.application_service.ProcessManager.start_process")
@patch("capabilities.desktop.application.application_service.os.path.exists", return_value=True)
@patch("capabilities.desktop.application.application_service.os.path.isfile", return_value=True)
def test_service_launch(mock_isfile, mock_exists, mock_start, mock_resolve):
    mock_resolve.return_value = "C:\\path\\to\\chrome.exe"
    mock_start.return_value = 999

    svc = ApplicationService()
    pid = svc.launch_application("Chrome")
    assert pid == 999
    mock_resolve.assert_called_with("Chrome")
    mock_start.assert_called_with("C:\\path\\to\\chrome.exe", None)


# --- DesktopCapability Tests ---

@patch("capabilities.desktop.application.application_service.ApplicationService.launch_application")
@patch("capabilities.desktop.application.application_service.ApplicationResolver.resolve")
@patch("capabilities.desktop.application.application_service.os.path.exists", return_value=True)
@patch("capabilities.desktop.application.application_service.os.path.isfile", return_value=True)
def test_desktop_capability_execute_open(mock_isfile, mock_exists, mock_resolve, mock_launch):
    mock_resolve.return_value = "C:\\path\\to\\chrome.exe"
    mock_launch.return_value = 456

    cap = DesktopCapability()
    result_dict = cap.execute("OPEN_APPLICATION", {"target": "Chrome"})
    assert result_dict["success"] is True
    assert "Successfully launched Chrome" in result_dict["response"]
    assert result_dict["data"]["pid"] == 456


# --- End-to-End Pipeline Integration Tests ---

@patch("capabilities.desktop.application.application_service.ApplicationResolver.resolve")
@patch("capabilities.desktop.application.application_service.ProcessManager.start_process")
@patch("capabilities.desktop.application.application_service.ProcessManager.terminate_process")
@patch("capabilities.desktop.application.application_service.ProcessManager.is_running")
@patch("capabilities.desktop.application.application_service.os.path.exists", return_value=True)
@patch("capabilities.desktop.application.application_service.os.path.isfile", return_value=True)
def test_integration_desktop_commands(
    mock_isfile, mock_exists, mock_is_running, mock_terminate, mock_start, mock_resolve
):
    mock_resolve.side_effect = lambda name: f"C:\\mock\\{name.lower()}.exe"
    mock_start.return_value = 777
    mock_terminate.return_value = True
    mock_is_running.side_effect = lambda app, exe: app.lower() == "chrome"

    planner = Planner()
    desktop_cap = DesktopCapability()
    dispatcher = ActionDispatcher(capabilities={desktop_cap.name: desktop_cap})
    assistant = AuralisAssistant(planner=planner, dispatcher=dispatcher)

    # 1. Open Chrome
    req = AssistantRequest(
        message="Open Chrome",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)
    assert res.result.success is True
    assert res.plan.intent == Intent.OPEN_APPLICATION
    assert res.plan.target == "Chrome"
    assert "Successfully launched Chrome" in res.response

    # 2. Open VS Code
    req = AssistantRequest(
        message="Open VS Code",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)
    assert res.result.success is True
    assert res.plan.intent == Intent.OPEN_APPLICATION
    assert res.plan.target == "VS Code"

    # 3. Close Notepad
    req = AssistantRequest(
        message="Close Notepad",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)
    assert res.result.success is True
    assert res.plan.intent == Intent.CLOSE_APPLICATION
    assert res.plan.target == "Notepad"
    assert "Successfully closed Notepad" in res.response

    # 4. Restart Calculator
    req = AssistantRequest(
        message="Restart Calculator",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)
    assert res.result.success is True
    assert res.plan.intent == Intent.RESTART_APPLICATION
    assert res.plan.target == "Calculator"
    assert "Successfully restarted Calculator" in res.response

    # 5. List running applications
    req = AssistantRequest(
        message="List running applications",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)
    assert res.result.success is True
    assert res.plan.intent == Intent.LIST_RUNNING_APPLICATIONS
    assert "Chrome" in res.response
