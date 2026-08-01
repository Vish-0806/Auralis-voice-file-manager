"""Integration Runtime Coordinator (Phase 11.9).

Manages the lifecycle, health checks, statistics tracking, provider registration,
and thread safety for the Integration Subsystem using threading.RLock().
Serves as the single unified gateway between Brain Runtime / AI Runtime and every OS capability.
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
from brain.os.integration.integration_models import (
    ExecutionStatistics,
    IntegrationStatus,
    OperationRequest,
    OperationResponse,
)
from brain.os.integration.integration_provider import IntegrationProvider
from brain.os.integration.interfaces import (
    IIntegrationProvider,
    IIntegrationRuntime,
)
from brain.os.os_runtime import OperatingSystemRuntime
from brain.os.process.process_runtime import ProcessRuntime
from brain.os.process.runtime import get_process_runtime
from brain.os.runtime import get_os_runtime
from brain.os.security.runtime import get_security_runtime
from brain.os.security.security_runtime import SecurityRuntime
from brain.os.window.runtime import get_window_runtime
from brain.os.window.window_runtime import WindowRuntime


class IntegrationRuntime(IIntegrationRuntime):
    """Thread-safe runtime coordinator for the OS Integration Subsystem."""

    def __init__(
        self,
        provider: Optional[IIntegrationProvider] = None,
        os_runtime: Optional[OperatingSystemRuntime] = None,
        filesystem_runtime: Optional[FilesystemRuntime] = None,
        application_runtime: Optional[ApplicationRuntime] = None,
        process_runtime: Optional[ProcessRuntime] = None,
        desktop_runtime: Optional[DesktopRuntime] = None,
        window_runtime: Optional[WindowRuntime] = None,
        device_runtime: Optional[DeviceRuntime] = None,
        security_runtime: Optional[SecurityRuntime] = None,
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
        self._security_runtime = security_runtime
        self._state = "Initializing"
        self._start_time: Optional[float] = None

    def initialize(self) -> None:
        """Initialize integration runtime and bind all underlying OS runtimes."""
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

            if self._security_runtime is None:
                self._security_runtime = get_security_runtime()

            if self._provider is None:
                self._provider = IntegrationProvider()

            self._state = "Running"
            self._start_time = time.time()

    def shutdown(self) -> None:
        """Shutdown integration runtime."""
        with self._lock:
            self._state = "Stopped"

    def register_provider(self, provider: IIntegrationProvider) -> None:
        """Register integration provider."""
        with self._lock:
            if not isinstance(provider, IIntegrationProvider):
                raise TypeError("Provider must implement IIntegrationProvider")
            self._provider = provider

    def get_provider(self) -> Optional[IIntegrationProvider]:
        """Get registered integration provider."""
        with self._lock:
            return self._provider

    def execute(self, request: OperationRequest) -> OperationResponse:
        """Execute an operation request."""
        with self._lock:
            if self._provider is None:
                self._provider = IntegrationProvider()
            return self._provider.execute(request)

    def get_statistics(self) -> ExecutionStatistics:
        """Get integration runtime performance statistics."""
        with self._lock:
            if self._provider is not None:
                return self._provider.get_statistics()
            return ExecutionStatistics()

    def get_health(self) -> IntegrationStatus:
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
            health_info = self._provider.get_health() if self._provider else None
            caps_reg = health_info.capabilities_count if health_info else 0

            return IntegrationStatus(
                state=self._state,
                healthy=healthy,
                provider_registered=self._provider is not None,
                capabilities_registered=caps_reg,
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
                "total_operations": stats.total_operations,
                "provider_diagnostics": provider_diag,
            }
