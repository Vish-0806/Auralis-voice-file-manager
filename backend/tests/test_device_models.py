"""Unit tests for Phase 11.7 Device Runtime domain models."""

from datetime import datetime
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from brain.os.device import (
    AudioDevice,
    AudioDeviceType,
    BatteryStatus,
    DeviceCapabilities,
    DeviceHealth,
    DeviceInfo,
    DeviceOperationRequest,
    DeviceOperationResult,
    DeviceRuntimeStatus,
    DeviceState,
    DeviceStatistics,
    DeviceType,
    DisplayDevice,
    InputDevice,
    NetworkDevice,
    NetworkType,
    PowerState,
    StorageDevice,
)


def test_device_enums() -> None:
    assert DeviceType.AUDIO.value == "audio"
    assert DeviceState.ACTIVE.value == "active"
    assert AudioDeviceType.OUTPUT_SPEAKER.value == "output_speaker"
    assert NetworkType.ETHERNET.value == "ethernet"
    assert PowerState.CHARGING.value == "charging"


def test_device_info_defaults_and_immutability() -> None:
    info = DeviceInfo(device_id="dev_1", name="Speakers", device_type=DeviceType.AUDIO)
    assert info.device_id == "dev_1"
    assert info.name == "Speakers"

    with pytest.raises((TypeError, ValidationError)):
        info.name = "Mic"  # type: ignore


def test_audio_device_defaults_and_immutability() -> None:
    info = DeviceInfo(device_id="audio_1", name="Headset")
    audio = AudioDevice(info=info, volume_level=75.0, is_muted=False)
    assert audio.volume_level == 75.0

    with pytest.raises((TypeError, ValidationError)):
        audio.volume_level = 50.0  # type: ignore


def test_battery_status_defaults_and_immutability() -> None:
    batt = BatteryStatus(is_present=True, power_state=PowerState.DISCHARGING, percentage=85.0)
    assert batt.is_present is True
    assert batt.percentage == 85.0

    with pytest.raises((TypeError, ValidationError)):
        batt.percentage = 90.0  # type: ignore
