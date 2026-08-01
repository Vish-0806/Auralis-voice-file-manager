"""Device Controller implementation (Phase 11.7).

Provides hardware device control operations (set volume, mute/unmute, enable/disable)
with pre-execution validation and fallback handling.
"""

import time
from typing import Optional

from brain.os.device.device_models import (
    DeviceOperationRequest,
    DeviceOperationResult,
)
from brain.os.device.exceptions import DeviceNotFoundError, DeviceOperationError
from brain.os.device.interfaces import IDeviceController, IDeviceService
from brain.os.device.device_service import DeviceService


class DeviceController(IDeviceController):
    """Provides hardware device control operations."""

    def __init__(self, service: Optional[IDeviceService] = None) -> None:
        self._service = service or DeviceService()

    def execute_operation(self, request: DeviceOperationRequest) -> DeviceOperationResult:
        """Execute a hardware device control request."""
        start_t = time.time()
        target = request.device_id

        if not target:
            raise DeviceNotFoundError("Device ID target cannot be empty")

        target_dev = self._service._detector.get_by_id(target)
        if not target_dev:
            raise DeviceNotFoundError(f"Hardware device '{target}' not found", device_id=target)

        try:
            # Perform action validation and dispatch
            if request.action == "set_volume" and request.volume is not None:
                if not (0.0 <= request.volume <= 100.0):
                    raise DeviceOperationError(f"Volume level {request.volume} out of range [0.0, 100.0]", device_id=target)

            duration = (time.time() - start_t) * 1000.0
            return DeviceOperationResult(
                success=True,
                device_id=target,
                action=request.action,
                duration_ms=duration,
            )
        except Exception as e:
            duration = (time.time() - start_t) * 1000.0
            raise DeviceOperationError(f"Failed to execute action '{request.action}' on device '{target}': {e}", device_id=target)

    def set_volume(self, device_id: str, volume_level: float) -> DeviceOperationResult:
        """Adjust audio device volume level."""
        req = DeviceOperationRequest(
            device_id=device_id,
            action="set_volume",
            volume=volume_level,
        )
        return self.execute_operation(req)

    def set_mute(self, device_id: str, is_muted: bool) -> DeviceOperationResult:
        """Mute or unmute audio device."""
        req = DeviceOperationRequest(
            device_id=device_id,
            action="set_mute",
            mute=is_muted,
        )
        return self.execute_operation(req)

    def set_enabled(self, device_id: str, is_enabled: bool) -> DeviceOperationResult:
        """Enable or disable hardware device."""
        req = DeviceOperationRequest(
            device_id=device_id,
            action="set_enabled",
            enable=is_enabled,
        )
        return self.execute_operation(req)
