"""Tests for the system controls capability and its subcomponents."""

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
from capabilities.desktop.system.audio_controller import AudioController
from capabilities.desktop.system.display_controller import DisplayController
from capabilities.desktop.system.power_controller import PowerController
from capabilities.desktop.system.network_controller import NetworkController
from capabilities.desktop.system.system_service import SystemService


# --- AudioController Tests ---

@patch("capabilities.desktop.system.audio_controller.AudioUtilities")
def test_audio_controller_get_set(mock_utilities):
    mock_volume = MagicMock()
    mock_volume.GetMasterVolumeLevelScalar.return_value = 0.5
    mock_volume.GetMute.return_value = 0
    mock_interface = MagicMock()
    
    mock_device = MagicMock()
    mock_device.Activate.return_value = mock_interface
    mock_utilities.GetSpeakers.return_value = mock_device

    with patch("capabilities.desktop.system.audio_controller.cast", return_value=mock_volume):
        ctrl = AudioController()
        assert ctrl.get_volume() == 50
        
        ctrl.set_volume(75)
        mock_volume.SetMasterVolumeLevelScalar.assert_called_with(0.75, None)

        ctrl.mute()
        mock_volume.SetMute.assert_called_with(1, None)
        
        ctrl.unmute()
        mock_volume.SetMute.assert_called_with(0, None)


# --- DisplayController Tests ---

@patch("capabilities.desktop.system.display_controller.os")
def test_display_controller_brightness(mock_os):
    mock_os.name = "nt"
    
    mock_wmi = MagicMock()
    mock_method = MagicMock()
    mock_monitor = MagicMock()
    mock_monitor.CurrentBrightness = 40
    
    mock_wmi.ExecQuery.side_effect = lambda query: {
        "SELECT * FROM WmiMonitorBrightness": [mock_monitor],
        "SELECT * FROM WmiMonitorBrightnessMethods": [mock_method]
    }.get(query, [])

    with patch("win32com.client.GetObject", return_value=mock_wmi):
        ctrl = DisplayController()
        assert ctrl.get_brightness() == 40
        
        ctrl.set_brightness(80)
        mock_method.WmiSetBrightness.assert_called_with(0, 80)


# --- PowerController Tests ---

@patch("capabilities.desktop.system.power_controller.os")
@patch("capabilities.desktop.system.power_controller.subprocess")
def test_power_controller_actions(mock_sub, mock_os):
    mock_os.name = "nt"
    
    ctrl = PowerController()
    
    with patch("ctypes.windll.user32.LockWorkStation") as mock_lock:
        ctrl.lock_pc()
        mock_lock.assert_called_once()

    with patch("ctypes.windll.powrprof.SetSuspendState") as mock_sleep:
        ctrl.sleep_pc()
        mock_sleep.assert_called_with(0, 1, 0)

    assert ctrl.shutdown_pc(confirm=False) is False
    mock_sub.run.assert_not_called()
    
    assert ctrl.shutdown_pc(confirm=True) is True
    mock_sub.run.assert_called_with(["shutdown", "/s", "/t", "0"], capture_output=True)


# --- NetworkController Tests ---

@patch("capabilities.desktop.system.network_controller.os")
@patch("capabilities.desktop.system.network_controller.subprocess")
def test_network_controller_actions(mock_sub, mock_os):
    mock_os.name = "nt"
    mock_sub.run.return_value.returncode = 0
    
    ctrl = NetworkController()
    
    assert ctrl.enable_wifi() is True
    mock_sub.run.assert_called_with(
        ["netsh", "interface", "set", "interface", "name=Wi-Fi", "admin=enabled"],
        capture_output=True,
        text=True
    )
    
    assert ctrl.disable_wifi() is True
    mock_sub.run.assert_called_with(
        ["netsh", "interface", "set", "interface", "name=Wi-Fi", "admin=disabled"],
        capture_output=True,
        text=True
    )

    assert ctrl.enable_bluetooth() is True
    assert ctrl.disable_bluetooth() is True


# --- End-to-End Integration Pipeline Tests ---

@patch("capabilities.desktop.system.audio_controller.AudioUtilities")
@patch("capabilities.desktop.system.audio_controller.cast")
@patch("win32com.client.GetObject")
@patch("ctypes.windll.user32.LockWorkStation")
@patch("ctypes.windll.powrprof.SetSuspendState")
@patch("capabilities.desktop.system.network_controller.subprocess.run")
def test_integration_system_commands(
    mock_net_sub, mock_sleep, mock_lock, mock_wmi_get, mock_cast, mock_audio_utils
):
    mock_net_sub.return_value.returncode = 0
    mock_net_sub.return_value.stdout = "Enabled"

    mock_volume = MagicMock()
    mock_cast.return_value = mock_volume

    planner = Planner()
    desktop_cap = DesktopCapability()
    dispatcher = ActionDispatcher(capabilities={desktop_cap.name: desktop_cap})
    assistant = AuralisAssistant(planner=planner, dispatcher=dispatcher)

    # 1. Increase volume to 60%
    req = AssistantRequest(
        message="Increase volume to 60%",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)
    assert res.result.success is True
    assert res.plan.intent == Intent.SET_VOLUME
    assert res.plan.target == "60%"
    mock_volume.SetMasterVolumeLevelScalar.assert_called_with(0.60, None)

    # 2. Mute system
    req = AssistantRequest(
        message="Mute system",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)
    assert res.result.success is True
    assert res.plan.intent == Intent.MUTE
    mock_volume.SetMute.assert_called_with(1, None)

    # 3. Lock my computer
    req = AssistantRequest(
        message="Lock my computer",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)
    assert res.result.success is True
    assert res.plan.intent == Intent.LOCK_PC
    mock_lock.assert_called_once()

    # 4. Put the computer to sleep
    req = AssistantRequest(
        message="Put the computer to sleep",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)
    assert res.result.success is True
    assert res.plan.intent == Intent.SLEEP_PC
    mock_sleep.assert_called_with(0, 1, 0)

    # 5. Disable Wi-Fi
    req = AssistantRequest(
        message="Disable Wi-Fi",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)
    assert res.result.success is True
    assert res.plan.intent == Intent.DISABLE_WIFI
    mock_net_sub.assert_any_call(
        ["netsh", "interface", "set", "interface", "name=Wi-Fi", "admin=disabled"],
        capture_output=True,
        text=True
    )

    # 6. Enable Bluetooth
    req = AssistantRequest(
        message="Enable Bluetooth",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)
    assert res.result.success is True
    assert res.plan.intent == Intent.ENABLE_BLUETOOTH
