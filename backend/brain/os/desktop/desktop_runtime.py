"""Desktop Runtime Coordinator (Phase 11.5).

Manages the lifecycle, health checks, statistics tracking, provider registration,
and thread safety for the Desktop Subsystem using threading.RLock().
Integrates with OperatingSystemRuntime (Phase 11.1).
"""

import threading
import time
from typing import Any, Dict, Optional

from brain.os.desktop.desktop_models import DesktopRuntimeStatus, DesktopStatistics
from brain.os.desktop.desktop_provider import DesktopProvider
from brain.os.desktop.interfaces import IDesktopProvider, IDesktopRuntime
from brain.os.os_runtime import OperatingSystemRuntime
from brain.os.runtime import get_os_runtime


class DesktopRuntime(IDesktopRuntime):
    """Thread-safe runtime coordinator for the Desktop Subsystem."""

    def __init__(
        self,
        provider: Optional[IDesktopProvider] = None,
        os_runtime: Optional[OperatingSystemRuntime] = None,
    ) -> None:
        self._lock = threading.RLock()
        self._provider = provider
        self._os_runtime = os_runtime
        self._state = "Initializing"
        self._start_time: Optional[float] = None

    def initialize(self) -> None:
        """Initialize desktop runtime and bind OS runtime."""
        with self._lock:
            if self._state == "Running":
                return

            if self._os_runtime is None:
                self._os_runtime = get_os_runtime()

            if self._provider is None:
                self._provider = DesktopProvider()

            self._state = "Running"
            self._start_time = time.time()

    def shutdown(self) -> None:
        """Shutdown desktop runtime."""
        with self._lock:
            self._state = "Stopped"

    def register_provider(self, provider: IDesktopProvider) -> None:
        """Register desktop provider."""
        with self._lock:
            if not isinstance(provider, IDesktopProvider):
                raise TypeError("Provider must implement IDesktopProvider")
            self._provider = provider

    def get_provider(self) -> Optional[IDesktopProvider]:
        """Get registered desktop provider."""
        with self._lock:
            return self._provider

    def get_statistics(self) -> DesktopStatistics:
        """Get desktop runtime performance statistics."""
        with self._lock:
            if self._provider is not None:
                return self._provider.get_statistics()
            return DesktopStatistics()

    def get_health(self) -> DesktopRuntimeStatus:
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

            return DesktopRuntimeStatus(
                state=self._state,
                healthy=healthy,
                provider_registered=self._provider is not None,
                uptime_seconds=uptime,
                total_notifications=stats.total_notifications_sent,
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
                "total_notifications": stats.total_notifications_sent,
                "provider_diagnostics": provider_diag,
            }
