"""Abstract interfaces for Device Subsystem (Phase 11.7).

Defines canonical interfaces for Device Detector, Service, Controller,
Monitor, Provider, and Runtime.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from brain.os.device.device_models import (
    AudioDevice,
    BatteryStatus,
    DeviceCapabilities,
    DeviceHealth,
    DeviceInfo,
    DeviceOperationRequest,
    DeviceOperationResult,
    DeviceRuntimeStatus,
    DeviceStatistics,
    DeviceType,
    DisplayDevice,
    NetworkDevice,
    StorageDevice,
)


class IDeviceDetector(ABC):
    """Interface for hardware device discovery and enumeration."""

    @abstractmethod
    def enumerate_devices(self) -> List[DeviceInfo]:
        """Enumerate all connected hardware devices."""
        pass

    @abstractmethod
    def get_by_id(self, device_id: str) -> Optional[DeviceInfo]:
        """Lookup device metadata by Device ID."""
        pass

    @abstractmethod
    def get_by_type(self, device_type: DeviceType) -> List[DeviceInfo]:
        """Lookup devices matching a specific device type category."""
        pass

    @abstractmethod
    def get_default_device(self, device_type: DeviceType) -> Optional[DeviceInfo]:
        """Get default system device for a category."""
        pass


class IDeviceService(ABC):
    """Interface for detailed hardware inspection and status metrics."""

    @abstractmethod
    def get_audio_devices(self) -> List[AudioDevice]:
        """Inspect audio input/output devices."""
        pass

    @abstractmethod
    def get_display_devices(self) -> List[DisplayDevice]:
        """Inspect connected display monitors."""
        pass

    @abstractmethod
    def get_network_devices(self) -> List[NetworkDevice]:
        """Inspect network interface adapters."""
        pass

    @abstractmethod
    def get_storage_devices(self) -> List[StorageDevice]:
        """Inspect mounted storage volumes."""
        pass

    @abstractmethod
    def get_battery_status(self) -> BatteryStatus:
        """Inspect system power and battery status."""
        pass


class IDeviceController(ABC):
    """Interface for hardware device control (volume, mute, toggle)."""

    @abstractmethod
    def execute_operation(self, request: DeviceOperationRequest) -> DeviceOperationResult:
        """Execute a hardware device control request."""
        pass

    @abstractmethod
    def set_volume(self, device_id: str, volume_level: float) -> DeviceOperationResult:
        """Adjust audio device volume level."""
        pass

    @abstractmethod
    def set_mute(self, device_id: str, is_muted: bool) -> DeviceOperationResult:
        """Mute or unmute audio device."""
        pass

    @abstractmethod
    def set_enabled(self, device_id: str, is_enabled: bool) -> DeviceOperationResult:
        """Enable or disable hardware device."""
        pass


class IDeviceMonitor(ABC):
    """Interface for hardware device monitoring and state change tracking."""

    @abstractmethod
    def start_monitoring(self, device_id: str) -> DeviceInfo:
        """Begin monitoring a hardware device."""
        pass

    @abstractmethod
    def stop_monitoring(self, device_id: str) -> bool:
        """Stop monitoring a hardware device."""
        pass

    @abstractmethod
    def get_monitored_devices(self) -> List[DeviceInfo]:
        """List currently monitored hardware devices."""
        pass

    @abstractmethod
    def get_statistics(self) -> DeviceStatistics:
        """Get device subsystem performance statistics."""
        pass


class IDeviceProvider(ABC):
    """Interface for Device Subsystem Provider."""

    @abstractmethod
    def get_detector(self) -> IDeviceDetector:
        """Return device detector."""
        pass

    @abstractmethod
    def get_service(self) -> IDeviceService:
        """Return device service."""
        pass

    @abstractmethod
    def get_controller(self) -> IDeviceController:
        """Return device controller."""
        pass

    @abstractmethod
    def get_monitor(self) -> IDeviceMonitor:
        """Return device monitor."""
        pass

    @abstractmethod
    def get_health(self) -> DeviceHealth:
        """Return provider health status."""
        pass

    @abstractmethod
    def get_statistics(self) -> DeviceStatistics:
        """Return device statistics."""
        pass

    @abstractmethod
    def get_capabilities(self) -> DeviceCapabilities:
        """Return device capabilities."""
        pass

    @abstractmethod
    def get_diagnostics(self) -> Dict[str, Any]:
        """Return diagnostic information."""
        pass


class IDeviceRuntime(ABC):
    """Interface for Device Runtime coordinator."""

    @abstractmethod
    def initialize(self) -> None:
        """Initialize device runtime."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown device runtime."""
        pass

    @abstractmethod
    def register_provider(self, provider: IDeviceProvider) -> None:
        """Register device provider."""
        pass

    @abstractmethod
    def get_provider(self) -> Optional[IDeviceProvider]:
        """Get registered device provider."""
        pass

    @abstractmethod
    def get_statistics(self) -> DeviceStatistics:
        """Get device runtime performance statistics."""
        pass

    @abstractmethod
    def get_health(self) -> DeviceRuntimeStatus:
        """Get overall runtime health status."""
        pass

    @abstractmethod
    def get_diagnostics(self) -> Dict[str, Any]:
        """Get runtime diagnostics dictionary."""
        pass
