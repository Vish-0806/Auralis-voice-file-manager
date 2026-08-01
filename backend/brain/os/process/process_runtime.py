"""Process Runtime Coordinator (Phase 11.4).

Manages the lifecycle, health checks, statistics tracking, provider registration,
and thread safety for the Process Subsystem using threading.RLock().
Integrates with OperatingSystemRuntime (Phase 11.1) and ApplicationRuntime (Phase 11.3).
"""

import threading
import time
from typing import Any, Dict, Optional

from brain.os.application.application_runtime import ApplicationRuntime
from brain.os.application.runtime import get_application_runtime
from brain.os.os_runtime import OperatingSystemRuntime
from brain.os.process.interfaces import IProcessProvider, IProcessRuntime
from brain.os.process.process_models import ProcessRuntimeStatus, ProcessStatistics
from brain.os.process.process_provider import ProcessProvider
from brain.os.runtime import get_os_runtime


class ProcessRuntime(IProcessRuntime):
    """Thread-safe runtime coordinator for the Process Subsystem."""

    def __init__(
        self,
        provider: Optional[IProcessProvider] = None,
        os_runtime: Optional[OperatingSystemRuntime] = None,
        application_runtime: Optional[ApplicationRuntime] = None,
    ) -> None:
        self._lock = threading.RLock()
        self._provider = provider
        self._os_runtime = os_runtime
        self._app_runtime = application_runtime
        self._state = "Initializing"
        self._start_time: Optional[float] = None

    def initialize(self) -> None:
        """Initialize process runtime and bind OS/Application runtimes."""
        with self._lock:
            if self._state == "Running":
                return

            if self._os_runtime is None:
                self._os_runtime = get_os_runtime()

            if self._app_runtime is None:
                self._app_runtime = get_application_runtime()

            if self._provider is None:
                self._provider = ProcessProvider()

            self._state = "Running"
            self._start_time = time.time()

    def shutdown(self) -> None:
        """Shutdown process runtime."""
        with self._lock:
            self._state = "Stopped"

    def register_provider(self, provider: IProcessProvider) -> None:
        """Register process provider."""
        with self._lock:
            if not isinstance(provider, IProcessProvider):
                raise TypeError("Provider must implement IProcessProvider")
            self._provider = provider

    def get_provider(self) -> Optional[IProcessProvider]:
        """Get registered process provider."""
        with self._lock:
            return self._provider

    def get_statistics(self) -> ProcessStatistics:
        """Get process runtime performance statistics."""
        with self._lock:
            if self._provider is not None:
                return self._provider.get_statistics()
            return ProcessStatistics()

    def get_health(self) -> ProcessRuntimeStatus:
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

            return ProcessRuntimeStatus(
                state=self._state,
                healthy=healthy,
                provider_registered=self._provider is not None,
                monitored_processes_count=stats.active_monitored_processes,
                total_terminations=stats.total_terminations,
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
                "monitored_count": stats.active_monitored_processes,
                "total_terminations": stats.total_terminations,
                "provider_diagnostics": provider_diag,
            }
