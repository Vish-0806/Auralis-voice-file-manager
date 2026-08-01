"""Unit tests for DeviceDetector (Phase 11.7)."""

# pyrefly: ignore [missing-import]
import pytest
from brain.os.device import DeviceDetector, DeviceInfo, DeviceType


def test_device_detector_enumerate_and_lookup() -> None:
    detector = DeviceDetector()
    devices = detector.enumerate_devices()
    assert isinstance(devices, list)
    assert len(devices) > 0

    first = devices[0]
    found = detector.get_by_id(first.device_id)
    assert found is not None
    assert found.device_id == first.device_id

    audio_devs = detector.get_by_type(DeviceType.AUDIO)
    assert len(audio_devs) > 0

    default_audio = detector.get_default_device(DeviceType.AUDIO)
    assert default_audio is not None
