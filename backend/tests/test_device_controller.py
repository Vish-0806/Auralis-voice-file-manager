"""Unit tests for DeviceController (Phase 11.7)."""

# pyrefly: ignore [missing-import]
import pytest
from brain.os.device import (
    DeviceController,
    DeviceNotFoundError,
    DeviceOperationError,
    DeviceOperationResult,
)


def test_device_controller_operations() -> None:
    ctrl = DeviceController()
    target_id = "audio_out_primary"

    res_vol = ctrl.set_volume(target_id, 50.0)
    assert isinstance(res_vol, DeviceOperationResult)
    assert res_vol.success is True

    res_mute = ctrl.set_mute(target_id, True)
    assert res_mute.success is True

    res_enable = ctrl.set_enabled(target_id, True)
    assert res_enable.success is True


def test_device_controller_invalid_device() -> None:
    ctrl = DeviceController()
    with pytest.raises(DeviceNotFoundError):
        ctrl.set_volume("non_existent_device_id_999", 50.0)
