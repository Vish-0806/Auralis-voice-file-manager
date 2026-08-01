"""Window Provider implementation (Phase 11.6).

Aggregates WindowDetector, WindowService, WindowController, and WindowMonitor
into a unified provider. Provides health tracking, statistics, capabilities, and diagnostics.
"""

from datetime import datetime, timezone
import time
from typing import Any, Dict, Optional

from brain.os.environment_service import EnvironmentService
from brain.os.interfaces import IEnvironmentService, IPlatformDetector
from brain.os.platform_detector import PlatformDetector
from brain.os.window.interfaces import (
    IWindowController,
    IWindowDetector,
    IWindowMonitor,
    IWindowProvider,
    IWindowService,
)
from brain.os.window.window_controller import WindowController
from brain.os.window.window_detector import WindowDetector
from brain.os.window.window_models import (
    WindowCapabilities,
    WindowHealth,
    WindowStatistics,
)
from brain.os.window.window_monitor import WindowMonitor
from brain.os.window.window_service import WindowService


class WindowProvider(IWindowProvider):
    """Canonical window subsystem provider."""

    def __init__(
        self,
        detector: Optional[IWindowDetector] = None,
        service: Optional[IWindowService] = None,
        controller: Optional[IWindowController] = None,
        monitor: Optional[IWindowMonitor] = None,
        environment_service: Optional[IEnvironmentService] = None,
        platform_detector: Optional[IPlatformDetector] = None,
    ) -> None:
        self._detector_comp = platform_detector or PlatformDetector()
        self._env_service = environment_service or EnvironmentService(
            platform_detector=self._detector_comp
        )

        self._detector = detector or WindowDetector(
            environment_service=self._env_service,
            platform_detector=self._detector_comp,
        )
        self._service = service or WindowService(detector=self._detector)
        self._controller = controller or WindowController(service=self._service)
        self._monitor = monitor or WindowMonitor(
            detector=self._detector, service=self._service
        )

        self._created_at = datetime.now(timezone.utc)
        self._start_time = time.time()
        self._healthy = True

    def get_detector(self) -> IWindowDetector:
        """Return window detector."""
        return self._detector

    def get_service(self) -> IWindowService:
        """Return window service."""
        return self._service

    def get_controller(self) -> IWindowController:
        """Return window controller."""
        return self._controller

    def get_monitor(self) -> IWindowMonitor:
        """Return window monitor."""
        return self._monitor

    def get_health(self) -> WindowHealth:
        """Return provider health status."""
        uptime = max(0.0, time.time() - self._start_time)
        stats = self.get_statistics()

        return WindowHealth(
            healthy=self._healthy,
            status="READY" if self._healthy else "DEGRADED",
            active_windows=stats.active_windows_count,
            uptime_seconds=uptime,
            details={"provider_type": "WindowProvider"},
        )

    def get_statistics(self) -> WindowStatistics:
        """Return window statistics."""
        return self._monitor.get_statistics()

    def get_capabilities(self) -> WindowCapabilities:
        """Return window capabilities."""
        return WindowCapabilities(
            supports_window_enumeration=True,
            supports_window_manipulation=True,
            supports_focus=True,
            supports_bounds_adjustment=True,
        )

    def get_diagnostics(self) -> Dict[str, Any]:
        """Return diagnostic information."""
        health = self.get_health()
        stats = self.get_statistics()

        return {
            "provider_type": "WindowProvider",
            "healthy": health.healthy,
            "active_windows": health.active_windows,
            "total_operations": stats.total_operations,
            "uptime_seconds": health.uptime_seconds,
            "created_at": self._created_at.isoformat(),
        }
