"""Device Provider implementation (Phase 11.7).

Aggregates DeviceDetector, DeviceService, DeviceController, and DeviceMonitor
into a unified provider. Provides health tracking, statistics, capabilities, and diagnostics.
"""

from datetime import datetime, timezone
import time
from typing import Any, Dict, Optional

from brain.os.device.device_controller import DeviceController
from brain.os.device.device_detector import DeviceDetector
from brain.os.device.device_models import (
    DeviceCapabilities,
    DeviceHealth,
    DeviceStatistics,
)
from brain.os.device.device_monitor import DeviceMonitor
from brain.os.device.device_service import DeviceService
from brain.os.device.interfaces import (
    IDeviceController,
    IDeviceDetector,
    IDeviceMonitor,
    IDeviceProvider,
    IDeviceService,
)
from brain.os.environment_service import EnvironmentService
from brain.os.interfaces import IEnvironmentService, IPlatformDetector
from brain.os.platform_detector import PlatformDetector


class DeviceProvider(IDeviceProvider):
    """Canonical device subsystem provider."""

    def __init__(
        self,
        detector: Optional[IDeviceDetector] = None,
        service: Optional[IDeviceService] = None,
        controller: Optional[IDeviceController] = None,
        monitor: Optional[IDeviceMonitor] = None,
        environment_service: Optional[IEnvironmentService] = None,
        platform_detector: Optional[IPlatformDetector] = None,
    ) -> None:
        self._detector_comp = platform_detector or PlatformDetector()
        self._env_service = environment_service or EnvironmentService(
            platform_detector=self._detector_comp
        )

        self._detector = detector or DeviceDetector(
            environment_service=self._env_service,
            platform_detector=self._detector_comp,
        )
        self._service = service or DeviceService(detector=self._detector)
        self._controller = controller or DeviceController(service=self._service)
        self._monitor = monitor or DeviceMonitor(
            detector=self._detector, service=self._service
        )

        self._created_at = datetime.now(timezone.utc)
        self._start_time = time.time()
        self._healthy = True

    def get_detector(self) -> IDeviceDetector:
        """Return device detector."""
        return self._detector

    def get_service(self) -> IDeviceService:
        """Return device service."""
        return self._service

    def get_controller(self) -> IDeviceController:
        """Return device controller."""
        return self._controller

    def get_monitor(self) -> IDeviceMonitor:
        """Return device monitor."""
        return self._monitor

    def get_health(self) -> DeviceHealth:
        """Return provider health status."""
        uptime = max(0.0, time.time() - self._start_time)
        stats = self.get_statistics()
        batt = self._service.get_battery_status()

        return DeviceHealth(
            healthy=self._healthy,
            status="READY" if self._healthy else "DEGRADED",
            active_devices_count=stats.active_devices_count,
            battery_percent=batt.percentage,
            uptime_seconds=uptime,
            details={"provider_type": "DeviceProvider"},
        )

    def get_statistics(self) -> DeviceStatistics:
        """Return device statistics."""
        return self._monitor.get_statistics()

    def get_capabilities(self) -> DeviceCapabilities:
        """Return device capabilities."""
        return DeviceCapabilities(
            supports_device_enumeration=True,
            supports_volume_control=True,
            supports_device_toggle=True,
            supports_battery_monitoring=True,
        )

    def get_diagnostics(self) -> Dict[str, Any]:
        """Return diagnostic information."""
        health = self.get_health()
        stats = self.get_statistics()

        return {
            "provider_type": "DeviceProvider",
            "healthy": health.healthy,
            "active_devices_count": health.active_devices_count,
            "battery_percent": health.battery_percent,
            "total_operations": stats.total_operations,
            "uptime_seconds": health.uptime_seconds,
            "created_at": self._created_at.isoformat(),
        }
