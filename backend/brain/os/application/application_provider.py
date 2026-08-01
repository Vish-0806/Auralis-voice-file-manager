"""Application Provider implementation (Phase 11.3).

Aggregates ApplicationRegistry, ApplicationDetector, LauncherService, and ApplicationMonitor
into a unified provider. Provides health tracking, statistics, capabilities, and diagnostics.
"""

from datetime import datetime, timezone
import time
from typing import Any, Dict, Optional

from brain.os.application.application_detector import ApplicationDetector
from brain.os.application.application_models import (
    ApplicationCapabilities,
    ApplicationHealth,
    ApplicationStatistics,
)
from brain.os.application.application_monitor import ApplicationMonitor
from brain.os.application.application_registry import ApplicationRegistry
from brain.os.application.interfaces import (
    IApplicationDetector,
    IApplicationMonitor,
    IApplicationProvider,
    IApplicationRegistry,
    ILauncherService,
)
from brain.os.application.launcher_service import LauncherService
from brain.os.environment_service import EnvironmentService
from brain.os.interfaces import IEnvironmentService, IPathService, IPlatformDetector
from brain.os.path_service import PathService
from brain.os.platform_detector import PlatformDetector


class ApplicationProvider(IApplicationProvider):
    """Canonical application subsystem provider."""

    def __init__(
        self,
        registry: Optional[IApplicationRegistry] = None,
        detector: Optional[IApplicationDetector] = None,
        launcher: Optional[ILauncherService] = None,
        monitor: Optional[IApplicationMonitor] = None,
        path_service: Optional[IPathService] = None,
        environment_service: Optional[IEnvironmentService] = None,
        platform_detector: Optional[IPlatformDetector] = None,
    ) -> None:
        self._detector_comp = platform_detector or PlatformDetector()
        self._env_service = environment_service or EnvironmentService(
            platform_detector=self._detector_comp
        )
        self._path_service = path_service or PathService(
            environment_service=self._env_service,
            platform_detector=self._detector_comp,
        )

        self._registry = registry or ApplicationRegistry()
        self._detector = detector or ApplicationDetector(
            path_service=self._path_service,
            environment_service=self._env_service,
            platform_detector=self._detector_comp,
        )
        self._launcher = launcher or LauncherService(
            registry=self._registry,
            detector=self._detector,
            path_service=self._path_service,
            environment_service=self._env_service,
            platform_detector=self._detector_comp,
        )
        self._monitor = monitor or ApplicationMonitor()

        self._created_at = datetime.now(timezone.utc)
        self._start_time = time.time()
        self._healthy = True

    def get_registry(self) -> IApplicationRegistry:
        """Return application registry."""
        return self._registry

    def get_detector(self) -> IApplicationDetector:
        """Return application detector."""
        return self._detector

    def get_launcher(self) -> ILauncherService:
        """Return launcher service."""
        return self._launcher

    def get_monitor(self) -> IApplicationMonitor:
        """Return application monitor."""
        return self._monitor

    def get_health(self) -> ApplicationHealth:
        """Return provider health status."""
        uptime = max(0.0, time.time() - self._start_time)
        reg_count = len(self._registry.list_applications())
        active_count = len(self._monitor.get_running_applications())

        return ApplicationHealth(
            healthy=self._healthy,
            status="READY" if self._healthy else "DEGRADED",
            registered_count=reg_count,
            active_count=active_count,
            uptime_seconds=uptime,
            details={"provider_type": "ApplicationProvider"},
        )

    def get_statistics(self) -> ApplicationStatistics:
        """Return provider statistics."""
        return self._monitor.get_statistics()

    def get_capabilities(self) -> ApplicationCapabilities:
        """Return application capabilities."""
        return ApplicationCapabilities(
            supports_background_launch=True,
            supports_window_modes=True,
            supports_alias_launch=True,
            supports_discovery=True,
        )

    def get_diagnostics(self) -> Dict[str, Any]:
        """Return diagnostic information."""
        health = self.get_health()
        stats = self.get_statistics()

        return {
            "provider_type": "ApplicationProvider",
            "healthy": health.healthy,
            "registered_count": health.registered_count,
            "active_count": health.active_count,
            "total_launches": stats.total_launches,
            "uptime_seconds": health.uptime_seconds,
            "created_at": self._created_at.isoformat(),
        }
