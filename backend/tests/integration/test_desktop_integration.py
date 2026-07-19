"""Comprehensive integration tests for the Desktop Automation subsystem (Version 0.4.0)."""

from __future__ import annotations

import os
import sys
from unittest.mock import MagicMock
if "edge_tts" not in sys.modules:
    sys.modules["edge_tts"] = MagicMock()

# Preload pywin32 DLLs and register their search directories defensively
dll_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "venv", "Lib", "site-packages", "pywin32_system32"))
if os.path.exists(dll_dir):
    try:
        os.add_dll_directory(dll_dir)
    except AttributeError:
        pass

try:
    import pywintypes
    import pythoncom
    import win32com.client
except ImportError:
    pass

import time
# pyrefly: ignore [missing-import]
import pytest
from datetime import datetime, UTC
from unittest.mock import patch, MagicMock
from contextlib import ExitStack

from core.assistant import AuralisAssistant
from core.dispatcher import ActionDispatcher
from core.planner import Planner
from core.models import AssistantRequest, ExecutionPlan, ExecutionResult
from core.intents import Intent
from capabilities.desktop.desktop_capability import DesktopCapability
from automation.workflow.workflow_engine import WorkflowEngine
from voice.integration.voice_pipeline import VoicePipeline


@pytest.fixture(autouse=True)
def mock_desktop_subsystem():
    """Mocks all low-level system and OS interactions for desktop capabilities."""

    with ExitStack() as stack:
        stack.enter_context(patch("capabilities.desktop.application.process_manager.os.path.exists", return_value=True))
        stack.enter_context(patch("capabilities.desktop.application.process_manager.os.path.isfile", return_value=True))
        mock_popen = stack.enter_context(patch("capabilities.desktop.application.process_manager.subprocess.Popen"))
        mock_iter = stack.enter_context(patch("capabilities.desktop.application.process_manager.psutil.process_iter"))
        stack.enter_context(patch("capabilities.desktop.application.application_resolver.os.path.exists", return_value=True))
        stack.enter_context(patch("capabilities.desktop.application.application_resolver.os.path.isfile", return_value=True))
        mock_which = stack.enter_context(patch("capabilities.desktop.application.application_resolver.shutil.which"))

        mock_proc = MagicMock()
        mock_proc.pid = 1234
        mock_popen.return_value = mock_proc
        mock_which.return_value = "C:\\Windows\\System32\\notepad.exe"

        mock_pgw = stack.enter_context(patch("capabilities.desktop.windows.window_manager.pgw"))
        mock_window = MagicMock()
        mock_window.title = "VS Code"
        mock_pgw.getAllWindows.return_value = [mock_window]
        mock_pgw.getActiveWindow.return_value = mock_window

        mock_audio_utils = stack.enter_context(patch("capabilities.desktop.system.audio_controller.AudioUtilities"))
        mock_cast = stack.enter_context(patch("capabilities.desktop.system.audio_controller.cast"))
        mock_wmi = stack.enter_context(patch("win32com.client.GetObject"))
        stack.enter_context(patch("capabilities.desktop.system.display_controller.os"))
        stack.enter_context(patch("capabilities.desktop.system.power_controller.os"))
        mock_power_sub = stack.enter_context(patch("capabilities.desktop.system.power_controller.subprocess"))
        stack.enter_context(patch("capabilities.desktop.system.network_controller.os"))
        mock_net_sub = stack.enter_context(patch("capabilities.desktop.system.network_controller.subprocess"))

        mock_volume_scalar = MagicMock()
        mock_volume_scalar.GetMasterVolumeLevelScalar.return_value = 0.5
        mock_volume_scalar.GetMute.return_value = 0
        mock_cast.return_value = mock_volume_scalar

        mock_win32_cb = stack.enter_context(patch("capabilities.desktop.clipboard.clipboard_manager.win32clipboard"))
        mock_cb_os = stack.enter_context(patch("capabilities.desktop.clipboard.clipboard_manager.os"))
        
        mock_cb_os.name = "nt"
        mock_win32_cb.CF_UNICODETEXT = 13
        mock_win32_cb.IsClipboardFormatAvailable.return_value = True
        mock_win32_cb.GetClipboardData.return_value = "Hello World"

        mock_mss = stack.enter_context(patch("capabilities.desktop.screenshot.capture_manager.mss.mss"))

        mock_sct = MagicMock()
        mock_grab_img = MagicMock()
        mock_grab_img.size = (100, 100)
        mock_grab_img.bgra = b"\x00" * 40000
        mock_sct.grab.return_value = mock_grab_img
        mock_sct.monitors = [{"left": 0, "top": 0, "width": 100, "height": 100}]
        mock_mss.return_value.__enter__.return_value = mock_sct

        mock_pyautogui_kb = stack.enter_context(patch("capabilities.desktop.input.keyboard_controller.pyautogui"))
        mock_pyautogui_m = stack.enter_context(patch("capabilities.desktop.input.mouse_controller.pyautogui"))

        yield {
            "popen": mock_popen,
            "pgw": mock_pgw,
            "pyautogui_kb": mock_pyautogui_kb,
            "pyautogui_m": mock_pyautogui_m,
            "win32_cb": mock_win32_cb,
            "volume_scalar": mock_volume_scalar,
        }


@pytest.fixture
def setup_desktop_integration_env():
    """Sets up planner, capabilities, dispatcher, and assistant for integration testing."""

    planner = Planner()
    desktop_cap = DesktopCapability()
    workflow_engine = WorkflowEngine()

    dispatcher = ActionDispatcher(capabilities={
        desktop_cap.name: desktop_cap,
        workflow_engine.name: workflow_engine,
    })
    workflow_engine.set_dispatcher(dispatcher)
    assistant = AuralisAssistant(planner=planner, dispatcher=dispatcher)

    return assistant, dispatcher, desktop_cap, workflow_engine


# --- 1. Application Management Integration ---

def test_integration_application_management(setup_desktop_integration_env):
    assistant, _, _, _ = setup_desktop_integration_env

    req = AssistantRequest(
        message="open VS Code",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)
    assert res.result.success is True
    assert res.plan.intent == Intent.OPEN_APPLICATION
    assert res.plan.target == "VS Code"


# --- 2. Window Management Integration ---

def test_integration_window_management(setup_desktop_integration_env):
    assistant, _, _, _ = setup_desktop_integration_env

    req = AssistantRequest(
        message="minimize vs code",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)
    assert res.result.success is True
    assert res.plan.intent == Intent.MINIMIZE_WINDOW
    assert res.plan.target == "VS Code"


# --- 3. System Controls Integration ---

def test_integration_system_controls(setup_desktop_integration_env):
    assistant, _, _, _ = setup_desktop_integration_env

    req = AssistantRequest(
        message="set volume to 50%",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)
    assert res.result.success is True
    assert res.plan.intent == Intent.SET_VOLUME
    assert res.plan.target == "50%"


# --- 4. Clipboard Automation Integration ---

def test_integration_clipboard_automation(setup_desktop_integration_env):
    assistant, _, _, _ = setup_desktop_integration_env

    req = AssistantRequest(
        message="copy selected text",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)
    assert res.result.success is True
    assert res.plan.intent == Intent.COPY_SELECTION


# --- 5. Screenshot & Screen Utilities Integration ---

def test_integration_screenshot_utilities(setup_desktop_integration_env):
    assistant, _, _, _ = setup_desktop_integration_env

    req = AssistantRequest(
        message="take screenshot",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)
    assert res.result.success is True
    assert res.plan.intent == Intent.TAKE_SCREENSHOT


# --- 6. Input Automation Engine Integration ---

def test_integration_input_automation(setup_desktop_integration_env):
    assistant, _, _, _ = setup_desktop_integration_env

    req = AssistantRequest(
        message="type hello world",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)
    assert res.result.success is True
    assert res.plan.intent == Intent.TYPE_TEXT
    assert res.plan.target == "hello world"


# --- 7. Desktop Workflows Integration ---

def test_integration_desktop_workflows(setup_desktop_integration_env):
    assistant, _, _, _ = setup_desktop_integration_env

    req = AssistantRequest(
        message="Start Coding",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)
    assert res.result.success is True
    assert res.plan.intent == Intent.RUN_WORKFLOW
    assert res.plan.target == "Start Coding"


# --- 8. Voice Integration Command Flow ---

def test_integration_voice_command_flow(setup_desktop_integration_env):
    assistant, _, _, _ = setup_desktop_integration_env

    mock_detector = MagicMock()
    mock_sm = MagicMock()
    mock_stt = MagicMock()
    mock_cm = MagicMock()
    mock_tts = MagicMock()
    mock_ux = MagicMock()
    mock_router = MagicMock()
    mock_mic = MagicMock()

    pipeline = VoicePipeline(
        assistant=assistant,
        wake_word_detector=mock_detector,
        conversation_manager=mock_sm,
        speech_to_text=mock_stt,
        context_manager=mock_cm,
        text_to_speech=mock_tts,
        feedback_manager=mock_ux,
        event_router=mock_router,
        microphone=mock_mic,
    )

    from voice.context import ContextState, ResolutionResult
    mock_detector.detect_in_text.return_value = MagicMock(phrase="Hey Auralis")
    mock_cm.resolve_references.return_value = ResolutionResult(
        resolved_command="set volume to 30%", requires_clarification=False
    )
    mock_cm.state = ContextState()
    mock_session = MagicMock(session_id="session_123")
    mock_sm.get_active_session.side_effect = [None, mock_session, mock_session]

    success = pipeline.process_step(text_input="Hey Auralis, set volume to 30%")
    assert success is True
