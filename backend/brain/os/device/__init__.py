"""Device Subsystem for Auralis Operating System Abstraction (Phase 11.7).

Exports domain models, enums, exceptions, abstract interfaces, services,
provider, runtime coordinator, and singleton accessors.
"""

from brain.os.device.device_controller import DeviceController
from brain.os.device.device_detector import DeviceDetector
from brain.os.device.device_models import (
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
from brain.os.device.device_monitor import DeviceMonitor
from brain.os.device.device_provider import DeviceProvider
from brain.os.device.device_runtime import DeviceRuntime
from brain.os.device.device_service import DeviceService
from brain.os.device.exceptions import (
    DeviceException,
    DeviceNotFoundError,
    DeviceOperationError,
    DevicePermissionError,
)
from brain.os.device.interfaces import (
    IDeviceController,
    IDeviceDetector,
    IDeviceMonitor,
    IDeviceProvider,
    IDeviceRuntime,
    IDeviceService,
)
from brain.os.device.runtime import get_device_runtime, reset_device_runtime

__all__ = [
    # Enums
    "DeviceType",
    "DeviceState",
    "AudioDeviceType",
    "NetworkType",
    "PowerState",
    # Models
    "DeviceInfo",
    "AudioDevice",
    "DisplayDevice",
    "InputDevice",
    "NetworkDevice",
    "StorageDevice",
    "BatteryStatus",
    "DeviceCapabilities",
    "DeviceStatistics",
    "DeviceHealth",
    "DeviceRuntimeStatus",
    "DeviceOperationRequest",
    "DeviceOperationResult",
    # Exceptions
    "DeviceException",
    "DeviceNotFoundError",
    "DeviceOperationError",
    "DevicePermissionError",
    # Interfaces
    "IDeviceDetector",
    "IDeviceService",
    "IDeviceController",
    "IDeviceMonitor",
    "IDeviceProvider",
    "IDeviceRuntime",
    # Services & Implementations
    "DeviceDetector",
    "DeviceService",
    "DeviceController",
    "DeviceMonitor",
    "DeviceProvider",
    "DeviceRuntime",
    # Singleton Accessors
    "get_device_runtime",
    "reset_device_runtime",
]
