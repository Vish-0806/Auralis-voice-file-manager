"""Device Monitor implementation (Phase 11.7).

Provides thread-safe monitoring of active hardware devices, state tracking,
operation metrics, and statistics generation.
"""

import threading
from typing import Dict, List, Optional

from brain.os.device.device_detector import DeviceDetector
from brain.os.device.device_models import DeviceInfo, DeviceStatistics
from brain.os.device.device_service import DeviceService
from brain.os.device.interfaces import IDeviceDetector, IDeviceMonitor, IDeviceService


class DeviceMonitor(IDeviceMonitor):
    """Thread-safe device monitor for tracking active hardware devices."""

    def __init__(
        self,
        detector: Optional[IDeviceDetector] = None,
        service: Optional[IDeviceService] = None,
    ) -> None:
        self._lock = threading.RLock()
        self._detector = detector or DeviceDetector()
        self._service = service or DeviceService(detector=self._detector)
        self._monitored_devices: Dict[str, DeviceInfo] = {}
        self._total_discovered = 0
        self._total_operations = 0
        self._successful_operations = 0
        self._failed_operations = 0

    def start_monitoring(self, device_id: str) -> DeviceInfo:
        """Begin monitoring a hardware device."""
        with self._lock:
            info = self._detector.get_by_id(device_id)
            if not info:
                info = DeviceInfo(device_id=device_id, name=f"Device {device_id}")
            self._monitored_devices[device_id] = info
            self._total_discovered += 1
            return info

    def stop_monitoring(self, device_id: str) -> bool:
        """Stop monitoring a hardware device."""
        with self._lock:
            if device_id in self._monitored_devices:
                del self._monitored_devices[device_id]
                return True
            return False

    def record_operation(self, success: bool) -> None:
        """Record device control operation metrics."""
        with self._lock:
            self._total_operations += 1
            if success:
                self._successful_operations += 1
            else:
                self._failed_operations += 1

    def get_monitored_devices(self) -> List[DeviceInfo]:
        """List currently monitored hardware devices."""
        with self._lock:
            return list(self._monitored_devices.values())

    def get_statistics(self) -> DeviceStatistics:
        """Get device subsystem performance statistics."""
        with self._lock:
            return DeviceStatistics(
                total_devices_discovered=self._total_discovered,
                active_devices_count=len(self._monitored_devices),
                total_operations=self._total_operations,
                successful_operations=self._successful_operations,
                failed_operations=self._failed_operations,
            )
