"""Tests for the window management capability and its subcomponents."""

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
from capabilities.desktop.windows.window_resolver import WindowResolver
from capabilities.desktop.windows.window_manager import WindowManager
from capabilities.desktop.windows.window_service import WindowService


# Helper function to create mock windows
def create_mock_window(hwnd, title, visible=True, is_minimized=False, is_maximized=False):
    win = MagicMock()
    win._hWnd = hwnd
    win.title = title
    win.visible = visible
    win.isMinimized = is_minimized
    win.isMaximized = is_maximized
    return win


# --- WindowResolver Tests ---

@patch("capabilities.desktop.windows.window_manager.win32process.GetWindowThreadProcessId")
@patch("capabilities.desktop.windows.window_manager.psutil.Process")
def test_resolver_by_title_and_app(mock_process, mock_thread_pid):
    mock_proc1 = MagicMock()
    mock_proc1.name.return_value = "Code.exe"
    mock_proc2 = MagicMock()
    mock_proc2.name.return_value = "chrome.exe"
    mock_process.side_effect = [mock_proc1, mock_proc2]
    mock_thread_pid.return_value = (0, 100)

    wm = WindowManager()
    win1 = create_mock_window(1, "VS Code - main.py")
    win2 = create_mock_window(2, "Google Chrome")
    
    with patch.object(wm, "get_all_windows", return_value=[win1, win2]):
        resolver = WindowResolver(wm)
        matches = resolver.resolve("main.py")
        assert len(matches) == 1
        assert matches[0] == win1

        matches = resolver.resolve("Chrome")
        assert len(matches) == 1
        assert matches[0] == win2


@patch("capabilities.desktop.windows.window_manager.WindowManager.get_active_window")
def test_resolver_active(mock_get_active):
    win = create_mock_window(1, "Active Win")
    mock_get_active.return_value = win

    wm = WindowManager()
    resolver = WindowResolver(wm)
    matches = resolver.resolve("active")
    assert len(matches) == 1
    assert matches[0] == win


# --- WindowManager Safety Tests ---

@patch("capabilities.desktop.windows.window_manager.win32process.GetWindowThreadProcessId")
def test_manager_safety_protected(mock_thread_pid):
    wm = WindowManager()

    protected_win = create_mock_window(1, "Taskbar")
    assert wm.is_protected(protected_win) is True

    mock_thread_pid.return_value = (0, os.getpid())
    own_win = create_mock_window(2, "Auralis CLI")
    assert wm.is_protected(own_win) is True

    mock_thread_pid.return_value = (0, 99999)
    normal_win = create_mock_window(3, "Calculator")
    assert wm.is_protected(normal_win) is False


# --- WindowService Tests ---

@patch("capabilities.desktop.windows.window_manager.win32process.GetWindowThreadProcessId")
@patch("capabilities.desktop.windows.window_manager.psutil.Process")
def test_service_list_windows(mock_process, mock_thread_pid):
    mock_proc = MagicMock()
    mock_proc.name.return_value = "notepad.exe"
    mock_process.return_value = mock_proc
    mock_thread_pid.return_value = (0, 200)

    win = create_mock_window(1, "Untitled - Notepad", visible=True)
    wm = WindowManager()
    
    with patch.object(wm, "get_all_windows", return_value=[win]):
        svc = WindowService(window_manager=wm)
        details = svc.list_windows()
        assert len(details) == 1
        assert details[0].title == "Untitled - Notepad"
        assert details[0].app_name == "notepad.exe"


# --- DesktopCapability Intent Routing Tests ---

@patch("capabilities.desktop.windows.window_service.WindowService.maximize_window")
def test_capability_maximize(mock_maximize):
    mock_maximize.return_value = True
    cap = DesktopCapability()
    res = cap.execute("MAXIMIZE_WINDOW", {"target": "VS Code"})
    assert res["success"] is True
    assert "Successfully maximized" in res["response"]


# --- End-to-End Pipeline Integration Tests ---

@patch("capabilities.desktop.windows.window_manager.pgw.getAllWindows")
@patch("capabilities.desktop.windows.window_manager.pgw.getActiveWindow")
@patch("capabilities.desktop.windows.window_manager.win32process.GetWindowThreadProcessId")
@patch("capabilities.desktop.windows.window_manager.psutil.Process")
def test_integration_window_commands(
    mock_process, mock_thread_pid, mock_get_active, mock_get_all
):
    mock_proc_code = MagicMock()
    mock_proc_code.name.return_value = "Code.exe"
    mock_proc_chrome = MagicMock()
    mock_proc_chrome.name.return_value = "chrome.exe"
    mock_proc_notepad = MagicMock()
    mock_proc_notepad.name.return_value = "notepad.exe"
    mock_proc_spotify = MagicMock()
    mock_proc_spotify.name.return_value = "Spotify.exe"
    mock_proc_calc = MagicMock()
    mock_proc_calc.name.return_value = "calc.exe"

    mock_process.side_effect = lambda pid: {
        101: mock_proc_code,
        102: mock_proc_chrome,
        103: mock_proc_notepad,
        104: mock_proc_spotify,
        105: mock_proc_calc,
    }.get(pid, MagicMock())

    mock_thread_pid.side_effect = lambda hwnd: {
        1: (0, 101),
        2: (0, 102),
        3: (0, 103),
        4: (0, 104),
        5: (0, 105),
    }.get(hwnd, (0, 0))

    win_code = create_mock_window(1, "VS Code")
    win_chrome = create_mock_window(2, "Google Chrome")
    win_notepad = create_mock_window(3, "Untitled - Notepad")
    win_spotify = create_mock_window(4, "Spotify Premium")
    win_calc = create_mock_window(5, "Calculator")

    all_mock_windows = [win_code, win_chrome, win_notepad, win_spotify, win_calc]
    mock_get_all.return_value = all_mock_windows
    mock_get_active.return_value = win_chrome

    planner = Planner()
    desktop_cap = DesktopCapability()
    dispatcher = ActionDispatcher(capabilities={desktop_cap.name: desktop_cap})
    assistant = AuralisAssistant(planner=planner, dispatcher=dispatcher)

    # 1. Maximize VS Code
    req = AssistantRequest(
        message="Maximize VS Code",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)
    assert res.result.success is True
    assert res.plan.intent == Intent.MAXIMIZE_WINDOW
    assert res.plan.target == "VS Code"
    win_code.maximize.assert_called_once()

    # 2. Minimize Chrome
    req = AssistantRequest(
        message="Minimize Chrome",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)
    assert res.result.success is True
    assert res.plan.intent == Intent.MINIMIZE_WINDOW
    assert res.plan.target == "Chrome"
    win_chrome.minimize.assert_called_once()

    # 3. Restore Notepad
    req = AssistantRequest(
        message="Restore Notepad",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)
    assert res.result.success is True
    assert res.plan.intent == Intent.RESTORE_WINDOW
    assert res.plan.target == "Notepad"
    win_notepad.restore.assert_called_once()

    # 4. Focus Spotify
    req = AssistantRequest(
        message="Focus Spotify",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)
    assert res.result.success is True
    assert res.plan.intent == Intent.FOCUS_WINDOW
    assert res.plan.target == "Spotify"
    win_spotify.activate.assert_called_once()

    # 5. Close Calculator
    req = AssistantRequest(
        message="Close Calculator",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)
    assert res.result.success is True
    assert res.plan.intent == Intent.CLOSE_WINDOW
    assert res.plan.target == "Calculator"
    win_calc.close.assert_called_once()

    # 6. Show Desktop
    req = AssistantRequest(
        message="Show Desktop",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)
    assert res.result.success is True
    assert res.plan.intent == Intent.SHOW_DESKTOP

    # 7. List open windows
    req = AssistantRequest(
        message="List open windows",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)
    assert res.result.success is True
    assert res.plan.intent == Intent.LIST_WINDOWS
    assert "VS Code" in res.response
    assert "Google Chrome" in res.response
