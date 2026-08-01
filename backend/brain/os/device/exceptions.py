"""Custom exception hierarchy for Device Subsystem (Phase 11.7)."""


class DeviceException(Exception):
    """Base exception for Device Subsystem errors."""

    def __init__(self, message: str, device_id: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.device_id = device_id


class DeviceNotFoundError(DeviceException):
    """Raised when a specified device ID or type is not found."""

    pass


class DeviceOperationError(DeviceException):
    """Raised when a hardware device operation or control request fails."""

    pass


class DevicePermissionError(DeviceException):
    """Raised when permissions are insufficient to access or control a device."""

    pass
