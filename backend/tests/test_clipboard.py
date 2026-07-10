"""Tests for the clipboard capability and its subcomponents."""

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
from capabilities.desktop.clipboard.models import ClipboardEntry
from capabilities.desktop.clipboard.clipboard_history import ClipboardHistory
from capabilities.desktop.clipboard.clipboard_manager import ClipboardManager
from capabilities.desktop.clipboard.clipboard_service import ClipboardService


# --- ClipboardHistory Tests ---

def test_history_fifo_bounds():
    hist = ClipboardHistory(max_size=3)
    entry1 = ClipboardEntry(content="c1", content_type="text", timestamp=datetime.now(UTC), size_bytes=2)
    entry2 = ClipboardEntry(content="c2", content_type="text", timestamp=datetime.now(UTC), size_bytes=2)
    entry3 = ClipboardEntry(content="c3", content_type="text", timestamp=datetime.now(UTC), size_bytes=2)
    entry4 = ClipboardEntry(content="c4", content_type="text", timestamp=datetime.now(UTC), size_bytes=2)

    hist.add_entry(entry1)
    hist.add_entry(entry2)
    hist.add_entry(entry3)
    items = hist.get_history()
    assert len(items) == 3
    assert items[0].content == "c3"

    hist.add_entry(entry4)
    items = hist.get_history()
    assert len(items) == 3
    assert items[0].content == "c4"
    assert items[2].content == "c2"


# --- ClipboardManager Mocked Tests ---

@patch("capabilities.desktop.clipboard.clipboard_manager.win32clipboard")
@patch("capabilities.desktop.clipboard.clipboard_manager.os")
def test_manager_mocked_reads(mock_os, mock_win32):
    mock_os.name = "nt"
    mock_win32.CF_UNICODETEXT = 13
    mock_win32.IsClipboardFormatAvailable.return_value = True
    mock_win32.GetClipboardData.return_value = "Hello World"

    mgr = ClipboardManager()
    assert mgr.read_clipboard() == "Hello World"
    mock_win32.OpenClipboard.assert_called_once()
    mock_win32.CloseClipboard.assert_called_once()


# --- ClipboardService Tests ---

@patch("capabilities.desktop.clipboard.clipboard_service.ClipboardManager")
def test_service_save_to_file(mock_mgr_class, tmp_path):
    mock_mgr = mock_mgr_class.return_value
    mock_mgr.read_clipboard.return_value = "Clipboard file export contents."
    
    svc = ClipboardService(manager=mock_mgr)
    dest = tmp_path / "out.txt"
    
    assert svc.save_to_file(str(dest)) is True
    assert os.path.exists(dest)
    with open(dest, "r", encoding="utf-8") as f:
        assert f.read() == "Clipboard file export contents."


# --- End-to-End Pipeline Integration Tests ---

@patch("capabilities.desktop.clipboard.clipboard_manager.win32clipboard")
@patch("capabilities.desktop.clipboard.clipboard_manager.os")
@patch("capabilities.desktop.clipboard.clipboard_service.os.makedirs")
@patch("capabilities.desktop.clipboard.clipboard_service.open")
def test_integration_clipboard_commands(
    mock_open, mock_makedirs, mock_os, mock_win32
):
    mock_os.name = "nt"
    mock_win32.CF_UNICODETEXT = 13
    mock_win32.CF_BITMAP = 2
    mock_win32.IsClipboardFormatAvailable.side_effect = lambda fmt: fmt == mock_win32.CF_UNICODETEXT
    mock_win32.GetClipboardData.return_value = "Selected text content"

    planner = Planner()
    desktop_cap = DesktopCapability()
    dispatcher = ActionDispatcher(capabilities={desktop_cap.name: desktop_cap})
    assistant = AuralisAssistant(planner=planner, dispatcher=dispatcher)

    # 1. Copy selected text
    req = AssistantRequest(
        message="Copy selected text",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)
    assert res.result.success is True
    assert res.plan.intent == Intent.COPY_SELECTION
    mock_win32.SetClipboardText.assert_called_with("Selected text placeholder", mock_win32.CF_UNICODETEXT)

    # 2. Paste
    req = AssistantRequest(
        message="Paste",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)
    assert res.result.success is True
    assert res.plan.intent == Intent.PASTE
    assert "Selected text content" in res.response

    # 3. Clear clipboard
    req = AssistantRequest(
        message="Clear clipboard",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)
    assert res.result.success is True
    assert res.plan.intent == Intent.CLEAR_CLIPBOARD
    mock_win32.EmptyClipboard.assert_called()

    # 4. Show clipboard contents
    req = AssistantRequest(
        message="Show clipboard contents",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)
    assert res.result.success is True
    assert res.plan.intent == Intent.SHOW_CLIPBOARD
    assert "Selected text content" in res.response

    # 5. Save clipboard as a text file
    req = AssistantRequest(
        message="Save clipboard as a text file",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)
    assert res.result.success is True
    assert res.plan.intent == Intent.SAVE_CLIPBOARD
    mock_open.assert_called()

    # 6. Copy the current file path
    req = AssistantRequest(
        message="Copy the current file path",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)
    assert res.result.success is True
    assert res.plan.intent == Intent.COPY_FILE_PATH
    mock_win32.SetClipboardText.assert_called_with("C:\\workspace\\active_file.txt", mock_win32.CF_UNICODETEXT)
