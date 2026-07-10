"""Tests for the screenshot capability and its subcomponents."""

from __future__ import annotations

import os
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, UTC
from PIL import Image

from core.assistant import AuralisAssistant
from core.dispatcher import ActionDispatcher
from core.planner import Planner
from core.models import AssistantRequest
from core.intents import Intent
from capabilities.desktop.desktop_capability import DesktopCapability
from capabilities.desktop.screenshot.capture_manager import CaptureManager
from capabilities.desktop.screenshot.annotation import Annotation
from capabilities.desktop.screenshot.screen_recorder import ScreenRecorder
from capabilities.desktop.screenshot.screenshot_service import ScreenshotService


# --- Annotation Tests ---

def test_annotation_operations():
    img = Image.new("RGB", (100, 100), "white")
    
    img_rect = Annotation.draw_rectangle(img, (10, 10, 50, 50), color="red")
    assert img_rect.getpixel((10, 10)) == (255, 0, 0)

    img_hl = Annotation.highlight_region(img, (20, 20, 60, 60), color="yellow")
    assert img_hl.getpixel((30, 30)) != (255, 255, 255)

    img_txt = Annotation.add_text(img, "hello", (0, 0), color="blue")
    assert img_txt is not None

    img_blur = Annotation.blur_region(img, (5, 5, 25, 25))
    assert img_blur.size == (100, 100)


# --- ScreenRecorder Tests ---

def test_screen_recorder_state():
    rec = ScreenRecorder()
    assert rec.is_recording is False
    assert rec.is_paused is False

    assert rec.start_recording("test.mp4") is True
    assert rec.is_recording is True
    
    assert rec.pause_recording() is True
    assert rec.is_paused is True

    assert rec.stop_recording() is True
    assert rec.is_recording is False
    assert rec.is_paused is False


# --- CaptureManager Mocked Tests ---

@patch("capabilities.desktop.screenshot.capture_manager.mss.mss")
def test_capture_manager_fullscreen(mock_mss):
    mock_sct = MagicMock()
    mock_grab_img = MagicMock()
    mock_grab_img.size = (100, 100)
    mock_grab_img.bgra = b"\x00" * 40000
    mock_sct.grab.return_value = mock_grab_img
    mock_sct.monitors = [{"left": 0, "top": 0, "width": 100, "height": 100}]
    mock_mss.return_value.__enter__.return_value = mock_sct

    mgr = CaptureManager()
    img = mgr.capture_fullscreen()
    assert img.size == (100, 100)


# --- ScreenshotService Shortcut Resolution & Safety Tests ---

def test_service_shortcuts_and_unique_paths(tmp_path):
    svc = ScreenshotService()
    
    with patch.dict(os.environ, {"USERPROFILE": "C:\\Users\\Mock"}):
        desktop = svc._resolve_special_folder("Desktop")
        assert "Desktop" in desktop
        
        pictures = svc._resolve_special_folder("Pictures")
        assert "Pictures" in pictures

    test_dir = tmp_path / "screenshots"
    os.makedirs(test_dir, exist_ok=True)
    
    path1 = svc._get_unique_path(str(test_dir))
    with open(path1, "w") as f:
        f.write("")
        
    path2 = svc._get_unique_path(str(test_dir))
    assert path1 != path2


# --- End-to-End Pipeline Integration Tests ---

@patch("capabilities.desktop.screenshot.capture_manager.mss.mss")
@patch("capabilities.desktop.screenshot.capture_manager.pgw.getActiveWindow")
@patch("capabilities.desktop.screenshot.screenshot_service.os.name", "nt")
@patch("win32clipboard.OpenClipboard")
@patch("win32clipboard.EmptyClipboard")
@patch("win32clipboard.SetClipboardData")
@patch("win32clipboard.CloseClipboard")
def test_integration_screenshot_commands(
    mock_close, mock_set, mock_empty, mock_open, mock_active_win, mock_mss
):
    mock_win = MagicMock()
    mock_win.left = 10
    mock_win.top = 10
    mock_win.width = 80
    mock_win.height = 80
    mock_active_win.return_value = mock_win

    mock_sct = MagicMock()
    mock_grab_img = MagicMock()
    mock_grab_img.size = (100, 100)
    mock_grab_img.bgra = b"\x00" * 40000
    mock_sct.grab.return_value = mock_grab_img
    mock_sct.monitors = [
        {"left": 0, "top": 0, "width": 100, "height": 100},
        {"left": 0, "top": 0, "width": 50, "height": 50},
        {"left": 50, "top": 0, "width": 50, "height": 50},
    ]
    mock_mss.return_value.__enter__.return_value = mock_sct

    planner = Planner()
    desktop_cap = DesktopCapability()
    dispatcher = ActionDispatcher(capabilities={desktop_cap.name: desktop_cap})
    assistant = AuralisAssistant(planner=planner, dispatcher=dispatcher)

    # 1. Take a screenshot
    req = AssistantRequest(
        message="Take a screenshot",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)
    assert res.result.success is True
    assert res.plan.intent == Intent.TAKE_SCREENSHOT

    # 2. Capture active window
    req = AssistantRequest(
        message="Capture the active window",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)
    assert res.result.success is True
    assert res.plan.intent == Intent.CAPTURE_WINDOW

    # 3. Capture monitor 2
    req = AssistantRequest(
        message="Capture monitor 2",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)
    assert res.result.success is True
    assert res.plan.intent == Intent.CAPTURE_MONITOR
    assert res.plan.target == "2"

    # 4. Take a screenshot in 5 seconds
    req = AssistantRequest(
        message="Take a screenshot in 5 seconds",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)
    assert res.result.success is True
    assert res.plan.intent == Intent.DELAYED_SCREENSHOT
    assert res.plan.target == "5"

    # 5. Save screenshot to Desktop
    with patch.object(desktop_cap._screenshot_service, "save_image") as mock_save:
        from capabilities.desktop.screenshot.models import ScreenshotDetails
        mock_save.return_value = ScreenshotDetails(
            path="C:\\Users\\Mock\\Desktop\\screenshot.png",
            timestamp=datetime.now(UTC),
            width=100,
            height=100,
            format="PNG",
        )
        req = AssistantRequest(
            message="Save screenshot to Desktop",
            source="test",
            timestamp=datetime.now(UTC),
        )
        res = assistant.process_request(req)
        assert res.result.success is True
        assert res.plan.intent == Intent.SAVE_SCREENSHOT
        assert res.plan.target == "Desktop"
        mock_save.assert_called_with(None, "Desktop")

    # 6. Copy screenshot to clipboard
    req = AssistantRequest(
        message="Copy screenshot to clipboard",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)
    assert res.result.success is True
    assert res.plan.intent == Intent.COPY_SCREENSHOT
    mock_set.assert_called()
