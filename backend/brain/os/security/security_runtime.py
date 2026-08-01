"""Security Runtime Coordinator (Phase 11.8).

Manages the lifecycle, health checks, statistics tracking, provider registration,
and thread safety for the Security Subsystem using threading.RLock().
Integrates with OperatingSystemRuntime (Phase 11.1), FilesystemRuntime (Phase 11.2),
ApplicationRuntime (Phase 11.3), ProcessRuntime (Phase 11.4), DesktopRuntime (Phase 11.5),
WindowRuntime (Phase 11.6), and DeviceRuntime (Phase 11.7).
"""

import threading
import time
from typing import Any, Dict, Optional

from brain.os.application.application_runtime import ApplicationRuntime
from brain.os.application.runtime import get_application_runtime
from brain.os.desktop.desktop_runtime import DesktopRuntime
from brain.os.desktop.runtime import get_desktop_runtime
from brain.os.device.device_runtime import DeviceRuntime
from brain.os.device.runtime import get_device_runtime
from brain.os.filesystem.filesystem_runtime import FilesystemRuntime
from brain.os.filesystem.runtime import get_filesystem_runtime
from brain.os.os_runtime import OperatingSystemRuntime
from brain.os.process.process_runtime import ProcessRuntime
from brain.os.process.runtime import get_process_runtime
from brain.os.runtime import get_os_runtime
from brain.os.security.interfaces import ISecurityProvider, ISecurityRuntime
from brain.os.security.security_models import (
    SecurityDecision,
    SecurityRequest,
    SecurityRuntimeStatus,
    SecurityStatistics,
)
from brain.os.security.security_provider import SecurityProvider
from brain.os.window.runtime import get_window_runtime
from brain.os.window.window_runtime import WindowRuntime


class SecurityRuntime(ISecurityRuntime):
    """Thread-safe runtime coordinator for the Security Subsystem."""

    def __init__(
        self,
        provider: Optional[ISecurityProvider] = None,
        os_runtime: Optional[OperatingSystemRuntime] = None,
        filesystem_runtime: Optional[FilesystemRuntime] = None,
        application_runtime: Optional[ApplicationRuntime] = None,
        process_runtime: Optional[ProcessRuntime] = None,
        desktop_runtime: Optional[DesktopRuntime] = None,
        window_runtime: Optional[WindowRuntime] = None,
        device_runtime: Optional[DeviceRuntime] = None,
    ) -> None:
        self._lock = threading.RLock()
        self._provider = provider
        self._os_runtime = os_runtime
        self._fs_runtime = filesystem_runtime
        self._app_runtime = application_runtime
        self._proc_runtime = process_runtime
        self._desktop_runtime = desktop_runtime
        self._window_runtime = window_runtime
        self._device_runtime = device_runtime
        self._state = "Initializing"
        self._start_time: Optional[float] = None

    def initialize(self) -> None:
        """Initialize security runtime and bind underlying OS runtimes."""
        with self._lock:
            if self._state == "Running":
                return

            if self._os_runtime is None:
                self._os_runtime = get_os_runtime()

            if self._fs_runtime is None:
                self._fs_runtime = get_filesystem_runtime()

            if self._app_runtime is None:
                self._app_runtime = get_application_runtime()

            if self._proc_runtime is None:
                self._proc_runtime = get_process_runtime()

            if self._desktop_runtime is None:
                self._desktop_runtime = get_desktop_runtime()

            if self._window_runtime is None:
                self._window_runtime = get_window_runtime()

            if self._device_runtime is None:
                self._device_runtime = get_device_runtime()

            if self._provider is None:
                self._provider = SecurityProvider()

            self._state = "Running"
            self._start_time = time.time()

    def shutdown(self) -> None:
        """Shutdown security runtime."""
        with self._lock:
            self._state = "Stopped"

    def register_provider(self, provider: ISecurityProvider) -> None:
        """Register security provider."""
        with self._lock:
            if not isinstance(provider, ISecurityProvider):
                raise TypeError("Provider must implement ISecurityProvider")
            self._provider = provider

    def get_provider(self) -> Optional[ISecurityProvider]:
        """Get registered security provider."""
        with self._lock:
            return self._provider

    def evaluate_request(self, request: SecurityRequest) -> SecurityDecision:
        """Evaluate a security decision request."""
        with self._lock:
            if self._provider is None:
                self._provider = SecurityProvider()
            return self._provider.evaluate_request(request)

    def get_statistics(self) -> SecurityStatistics:
        """Get security runtime performance statistics."""
        with self._lock:
            if self._provider is not None:
                return self._provider.get_statistics()
            return SecurityStatistics()

    def get_health(self) -> SecurityRuntimeStatus:
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

            return SecurityRuntimeStatus(
                state=self._state,
                healthy=healthy,
                provider_registered=self._provider is not None,
                total_evaluations=stats.total_requests_evaluated,
                denied_evaluations=stats.denied_requests,
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
                "total_evaluations": stats.total_requests_evaluated,
                "denied_evaluations": stats.denied_requests,
                "provider_diagnostics": provider_diag,
            }
