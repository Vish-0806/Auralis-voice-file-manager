"""Operating System Runtime Coordinator (Phase 11.1).

Manages the lifecycle, statistics tracking, health checks, provider registration,
and thread safety for the Operating System Abstraction subsystem using threading.RLock().
"""

from datetime import datetime, timezone
import threading
import time
from typing import Any, Dict, Optional

from brain.os.interfaces import IOperatingSystemProvider, IOperatingSystemRuntime
from brain.os.os_models import (
    OSRuntimeStatus,
    RuntimeState,
    RuntimeStatistics,
)
from brain.os.os_provider import OperatingSystemProvider


class OperatingSystemRuntime(IOperatingSystemRuntime):
    """Thread-safe runtime manager for the Operating System Abstraction subsystem."""

    def __init__(self, provider: Optional[IOperatingSystemProvider] = None) -> None:
        self._lock = threading.RLock()
        self._provider = provider
        self._state = RuntimeState.INITIALIZING
        self._start_time: Optional[float] = None
        self._requests_count = 0
        self._platform_checks = 0
        self._env_snapshots = 0
        self._path_resolutions = 0
        self._errors_count = 0
        self._last_snapshot_at: Optional[datetime] = None

    def initialize(self) -> None:
        """Initialize the OS runtime coordinator."""
        with self._lock:
            if self._state == RuntimeState.RUNNING:
                return

            if self._provider is None:
                self._provider = OperatingSystemProvider()

            self._state = RuntimeState.RUNNING
            self._start_time = time.time()

    def shutdown(self) -> None:
        """Gracefully shutdown runtime coordinator."""
        with self._lock:
            if self._state in (RuntimeState.STOPPED, RuntimeState.INITIALIZING):
                self._state = RuntimeState.STOPPED
                return

            self._state = RuntimeState.STOPPING
            self._state = RuntimeState.STOPPED

    def register_provider(self, provider: IOperatingSystemProvider) -> None:
        """Register an OS provider."""
        with self._lock:
            if not isinstance(provider, IOperatingSystemProvider):
                raise TypeError("Provider must implement IOperatingSystemProvider")
            self._provider = provider

    def get_provider(self) -> Optional[IOperatingSystemProvider]:
        """Get registered OS provider."""
        with self._lock:
            return self._provider

    def record_request(
        self, request_type: str = "generic", is_error: bool = False
    ) -> None:
        """Track statistics for a runtime request."""
        with self._lock:
            self._requests_count += 1
            if request_type == "platform":
                self._platform_checks += 1
            elif request_type == "environment":
                self._env_snapshots += 1
                self._last_snapshot_at = datetime.now(timezone.utc)
            elif request_type == "path":
                self._path_resolutions += 1

            if is_error:
                self._errors_count += 1

    def get_statistics(self) -> RuntimeStatistics:
        """Get current runtime performance statistics."""
        with self._lock:
            uptime = 0.0
            if self._start_time is not None and self._state == RuntimeState.RUNNING:
                uptime = max(0.0, time.time() - self._start_time)

            return RuntimeStatistics(
                total_requests=self._requests_count,
                platform_checks=self._platform_checks,
                environment_snapshots=self._env_snapshots,
                path_resolutions=self._path_resolutions,
                errors_encountered=self._errors_count,
                uptime_seconds=uptime,
                last_snapshot_at=self._last_snapshot_at,
            )

    def get_health(self) -> OSRuntimeStatus:
        """Get current overall runtime health status."""
        with self._lock:
            uptime = 0.0
            if self._start_time is not None and self._state == RuntimeState.RUNNING:
                uptime = max(0.0, time.time() - self._start_time)

            provider_count = 1 if self._provider is not None else 0
            healthy = (
                self._state == RuntimeState.RUNNING
                and self._provider is not None
                and self._provider.is_available()
            )

            return OSRuntimeStatus(
                state=self._state,
                healthy=healthy,
                provider_count=provider_count,
                uptime_seconds=uptime,
                details={
                    "total_requests": self._requests_count,
                    "errors_count": self._errors_count,
                    "provider_registered": self._provider is not None,
                },
            )

    def get_diagnostics(self) -> Dict[str, Any]:
        """Get diagnostic information."""
        with self._lock:
            stats = self.get_statistics()
            health = self.get_health()
            provider_diag = (
                self._provider.get_diagnostics()
                if self._provider is not None
                else {}
            )

            return {
                "runtime_state": self._state.value,
                "healthy": health.healthy,
                "uptime_seconds": stats.uptime_seconds,
                "total_requests": stats.total_requests,
                "errors_encountered": stats.errors_encountered,
                "provider_diagnostics": provider_diag,
            }
