"""Application Runtime Coordinator (Phase 11.3).

Manages the lifecycle, health checks, statistics tracking, provider registration,
and thread safety for the Application Subsystem using threading.RLock().
Integrates with Phase 11.1 OperatingSystemRuntime.
"""

import threading
import time
from typing import Any, Dict, Optional

from brain.os.application.application_models import (
    ApplicationRuntimeStatus,
    ApplicationStatistics,
)
from brain.os.application.application_provider import ApplicationProvider
from brain.os.application.interfaces import (
    IApplicationProvider,
    IApplicationRuntime,
)
from brain.os.os_runtime import OperatingSystemRuntime
from brain.os.runtime import get_os_runtime


class ApplicationRuntime(IApplicationRuntime):
    """Thread-safe runtime coordinator for the Application Subsystem."""

    def __init__(
        self,
        provider: Optional[IApplicationProvider] = None,
        os_runtime: Optional[OperatingSystemRuntime] = None,
    ) -> None:
        self._lock = threading.RLock()
        self._provider = provider
        self._os_runtime = os_runtime
        self._state = "Initializing"
        self._start_time: Optional[float] = None

    def initialize(self) -> None:
        """Initialize application runtime and bind OS runtime."""
        with self._lock:
            if self._state == "Running":
                return

            if self._os_runtime is None:
                self._os_runtime = get_os_runtime()

            if self._provider is None:
                self._provider = ApplicationProvider()

            self._state = "Running"
            self._start_time = time.time()

    def shutdown(self) -> None:
        """Shutdown application runtime."""
        with self._lock:
            self._state = "Stopped"

    def register_provider(self, provider: IApplicationProvider) -> None:
        """Register application provider."""
        with self._lock:
            if not isinstance(provider, IApplicationProvider):
                raise TypeError("Provider must implement IApplicationProvider")
            self._provider = provider

    def get_provider(self) -> Optional[IApplicationProvider]:
        """Get registered application provider."""
        with self._lock:
            return self._provider

    def get_statistics(self) -> ApplicationStatistics:
        """Get application runtime performance statistics."""
        with self._lock:
            if self._provider is not None:
                return self._provider.get_statistics()
            return ApplicationStatistics()

    def get_health(self) -> ApplicationRuntimeStatus:
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

            return ApplicationRuntimeStatus(
                state=self._state,
                healthy=healthy,
                provider_registered=self._provider is not None,
                total_launches=stats.total_launches,
                active_apps=stats.active_applications_count,
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
                "total_launches": stats.total_launches,
                "active_apps": stats.active_applications_count,
                "provider_diagnostics": provider_diag,
            }
