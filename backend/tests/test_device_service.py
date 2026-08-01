"""Unit tests for DeviceService (Phase 11.7)."""

# pyrefly: ignore [missing-import]
import pytest
from brain.os.device import (
    AudioDevice,
    BatteryStatus,
    DeviceService,
    DisplayDevice,
    NetworkDevice,
    StorageDevice,
)


def test_device_service_hardware_inspection() -> None:
    svc = DeviceService()

    audio = svc.get_audio_devices()
    assert isinstance(audio, list)
    assert len(audio) > 0
    assert isinstance(audio[0], AudioDevice)

    displays = svc.get_display_devices()
    assert isinstance(displays, list)
    assert len(displays) > 0
    assert isinstance(displays[0], DisplayDevice)

    net = svc.get_network_devices()
    assert isinstance(net, list)
    assert len(net) > 0
    assert isinstance(net[0], NetworkDevice)

    storage = svc.get_storage_devices()
    assert isinstance(storage, list)
    assert len(storage) > 0
    assert isinstance(storage[0], StorageDevice)

    batt = svc.get_battery_status()
    assert isinstance(batt, BatteryStatus)
