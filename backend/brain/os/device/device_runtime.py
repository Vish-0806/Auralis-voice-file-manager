"""Device Runtime Coordinator (Phase 11.7).

Manages the lifecycle, health checks, statistics tracking, provider registration,
and thread safety for the Device Subsystem using threading.RLock().
Integrates with OperatingSystemRuntime (Phase 11.1), ApplicationRuntime (Phase 11.3),
ProcessRuntime (Phase 11.4), DesktopRuntime (Phase 11.5), and WindowRuntime (Phase 11.6).
"""

import threading
import time
from typing import Any, Dict, Optional

from brain.os.application.application_runtime import ApplicationRuntime
from brain.os.application.runtime import get_application_runtime
from brain.os.desktop.desktop_runtime import DesktopRuntime
from brain.os.desktop.runtime import get_desktop_runtime
from brain.os.device.device_models import DeviceRuntimeStatus, DeviceStatistics
from brain.os.device.device_provider import DeviceProvider
from brain.os.device.interfaces import IDeviceProvider, IDeviceRuntime
from brain.os.os_runtime import OperatingSystemRuntime
from brain.os.process.process_runtime import ProcessRuntime
from brain.os.process.runtime import get_process_runtime
from brain.os.runtime import get_os_runtime
from brain.os.window.runtime import get_window_runtime
from brain.os.window.window_runtime import WindowRuntime


class DeviceRuntime(IDeviceRuntime):
    """Thread-safe runtime coordinator for the Device Subsystem."""

    def __init__(
        self,
        provider: Optional[IDeviceProvider] = None,
        os_runtime: Optional[OperatingSystemRuntime] = None,
        application_runtime: Optional[ApplicationRuntime] = None,
        process_runtime: Optional[ProcessRuntime] = None,
        desktop_runtime: Optional[DesktopRuntime] = None,
        window_runtime: Optional[WindowRuntime] = None,
    ) -> None:
        self._lock = threading.RLock()
        self._provider = provider
        self._os_runtime = os_runtime
        self._app_runtime = application_runtime
        self._proc_runtime = process_runtime
        self._desktop_runtime = desktop_runtime
        self._window_runtime = window_runtime
        self._state = "Initializing"
        self._start_time: Optional[float] = None

    def initialize(self) -> None:
        """Initialize device runtime and bind underlying runtimes."""
        with self._lock:
            if self._state == "Running":
                return

            if self._os_runtime is None:
                self._os_runtime = get_os_runtime()

            if self._app_runtime is None:
                self._app_runtime = get_application_runtime()

            if self._proc_runtime is None:
                self._proc_runtime = get_process_runtime()

            if self._desktop_runtime is None:
                self._desktop_runtime = get_desktop_runtime()

            if self._window_runtime is None:
                self._window_runtime = get_window_runtime()

            if self._provider is None:
                self._provider = DeviceProvider()

            self._state = "Running"
            self._start_time = time.time()

    def shutdown(self) -> None:
        """Shutdown device runtime."""
        with self._lock:
            self._state = "Stopped"

    def register_provider(self, provider: IDeviceProvider) -> None:
        """Register device provider."""
        with self._lock:
            if not isinstance(provider, IDeviceProvider):
                raise TypeError("Provider must implement IDeviceProvider")
            self._provider = provider

    def get_provider(self) -> Optional[IDeviceProvider]:
        """Get registered device provider."""
        with self._lock:
            return self._provider

    def get_statistics(self) -> DeviceStatistics:
        """Get device runtime performance statistics."""
        with self._lock:
            if self._provider is not None:
                return self._provider.get_statistics()
            return DeviceStatistics()

    def get_health(self) -> DeviceRuntimeStatus:
        """Get overall runtime health status."""
        with self._lock:
            uptime = 0.0
            if self._start_time is not None and self._state == "Running":
                uptime = max(0.0, time.time() - self._start_time)

            healthy = (
                self._state == "Running"
                and self._provider is not None
                and self._provider.get_health().healthy
            )

            stats = self.get_statistics()

            return DeviceRuntimeStatus(
                state=self._state,
                healthy=healthy,
                provider_registered=self._provider is not None,
                active_devices_count=stats.active_devices_count,
                total_operations=stats.total_operations,
                uptime_seconds=uptime,
            )

    def get_diagnostics(self) -> Dict[str, Any]:
        """Get runtime diagnostics dictionary."""
        with self._lock:
            health = self.get_health()
            stats = self.get_statistics()
            provider_diag = (
                self._provider.get_diagnostics() if self._provider else {}
            )

            return {
                "runtime_state": self._state,
                "healthy": health.healthy,
                "uptime_seconds": health.uptime_seconds,
                "active_devices_count": stats.active_devices_count,
                "total_operations": stats.total_operations,
                "provider_diagnostics": provider_diag,
            }
