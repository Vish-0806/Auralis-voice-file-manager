"""Tests for the input automation capability and its subcomponents."""

from __future__ import annotations

# pyrefly: ignore [missing-import]
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, UTC

from core.assistant import AuralisAssistant
from core.dispatcher import ActionDispatcher
from core.planner import Planner
from core.models import AssistantRequest
from core.intents import Intent
from capabilities.desktop.desktop_capability import DesktopCapability
from capabilities.desktop.input.keyboard_controller import KeyboardController
from capabilities.desktop.input.mouse_controller import MouseController
from capabilities.desktop.input.shortcut_manager import ShortcutManager
from capabilities.desktop.input.macro_executor import MacroExecutor
from capabilities.desktop.input.input_service import InputService


# --- KeyboardController Tests ---

@patch("capabilities.desktop.input.keyboard_controller.pyautogui")
def test_keyboard_controller_types_and_presses(mock_pyautogui):
    kb = KeyboardController()
    
    kb.type_text("Hello World")
    mock_pyautogui.write.assert_called_with("Hello World", interval=0.01)

    kb.press_key("Enter")
    mock_pyautogui.press.assert_called_with("enter")

    kb.press_hotkey("Ctrl", "S")
    mock_pyautogui.hotkey.assert_called_with("ctrl", "s")


# --- MouseController Tests ---

@patch("capabilities.desktop.input.mouse_controller.pyautogui")
def test_mouse_controller_actions_and_validation(mock_pyautogui):
    mock_pyautogui.size.return_value = (1920, 1080)
    mc = MouseController()

    mc.move_mouse(500, 300)
    mock_pyautogui.moveTo.assert_called_with(500, 300, duration=0.25)

    with pytest.raises(ValueError):
        mc.move_mouse(2000, 3000)

    mc.click()
    mock_pyautogui.click.assert_called_with(button="left")

    mc.double_click()
    mock_pyautogui.doubleClick.assert_called_with(button="left")

    mc.right_click()
    mock_pyautogui.rightClick.assert_called()

    mc.scroll(-100)
    mock_pyautogui.scroll.assert_called_with(-100)

    mc.drag_and_drop(10, 10, 100, 100)
    mock_pyautogui.dragTo.assert_called_with(100, 100, duration=0.5)


# --- ShortcutManager and MacroExecutor Tests ---

def test_shortcut_manager_lookup():
    mock_kb = MagicMock()
    sm = ShortcutManager(keyboard_controller=mock_kb)

    sm.execute_shortcut("save")
    mock_kb.press_hotkey.assert_called_with("ctrl", "s")

    sm.execute_shortcut("ctrl+s")
    mock_kb.press_hotkey.assert_called_with("ctrl", "s")

    with pytest.raises(ValueError):
        sm.execute_shortcut("invalid_shortcut")


@patch("capabilities.desktop.input.macro_executor.time.sleep")
def test_macro_executor_save_file(mock_sleep):
    mock_service = MagicMock()
    me = MacroExecutor(input_service=mock_service)

    me.run_macro("Save File")
    mock_service.press_hotkey.assert_called_with("ctrl", "s")
    mock_service.type_text.assert_called_with("saved_file.txt")
    mock_service.press_key.assert_called_with("enter")


# --- End-to-End Pipeline Integration Tests ---

@patch("capabilities.desktop.input.mouse_controller.pyautogui")
@patch("capabilities.desktop.input.keyboard_controller.pyautogui")
@patch("capabilities.desktop.input.macro_executor.time.sleep")
def test_integration_input_commands(
    mock_sleep, mock_kb_pyautogui, mock_mouse_pyautogui
):
    mock_mouse_pyautogui.size.return_value = (1920, 1080)

    planner = Planner()
    desktop_cap = DesktopCapability()
    dispatcher = ActionDispatcher(capabilities={desktop_cap.name: desktop_cap})
    assistant = AuralisAssistant(planner=planner, dispatcher=dispatcher)

    # 1. Type Hello World
    req = AssistantRequest(
        message="Type Hello World",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)
    assert res.result.success is True
    assert res.plan.intent == Intent.TYPE_TEXT
    assert res.plan.target == "Hello World"
    mock_kb_pyautogui.write.assert_called_with("Hello World", interval=0.01)

    # 2. Press Enter
    req = AssistantRequest(
        message="Press Enter",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)
    assert res.result.success is True
    assert res.plan.intent == Intent.PRESS_KEY
    assert res.plan.target == "Enter"
    mock_kb_pyautogui.press.assert_called_with("enter")

    # 3. Press Ctrl+S
    req = AssistantRequest(
        message="Press Ctrl+S",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)
    assert res.result.success is True
    assert res.plan.intent == Intent.PRESS_SHORTCUT
    assert res.plan.target == "Ctrl+S"
    mock_kb_pyautogui.hotkey.assert_called_with("ctrl", "s")

    # 4. Move mouse to (500, 300)
    req = AssistantRequest(
        message="Move mouse to (500, 300)",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)
    assert res.result.success is True
    assert res.plan.intent == Intent.MOVE_MOUSE
    assert res.plan.target == "500,300"
    mock_mouse_pyautogui.moveTo.assert_called_with(500, 300, duration=0.25)

    # 5. Click
    req = AssistantRequest(
        message="Click",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)
    assert res.result.success is True
    assert res.plan.intent == Intent.CLICK_MOUSE
    mock_mouse_pyautogui.click.assert_called_with(button="left")

    # 6. Double click
    req = AssistantRequest(
        message="Double click",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)
    assert res.result.success is True
    assert res.plan.intent == Intent.DOUBLE_CLICK
    mock_mouse_pyautogui.doubleClick.assert_called_with(button="left")

    # 7. Scroll down
    req = AssistantRequest(
        message="Scroll down",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)
    assert res.result.success is True
    assert res.plan.intent == Intent.SCROLL
    assert res.plan.target == "down"
    mock_mouse_pyautogui.scroll.assert_called_with(-100)

    # 8. Run Save File macro
    req = AssistantRequest(
        message="Run Save File macro",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)
    assert res.result.success is True
    assert res.plan.intent == Intent.RUN_MACRO
    assert res.plan.target == "Save File"
    mock_kb_pyautogui.hotkey.assert_called_with("ctrl", "s")
    mock_kb_pyautogui.write.assert_called_with("saved_file.txt", interval=0.01)
    mock_kb_pyautogui.press.assert_called_with("enter")
