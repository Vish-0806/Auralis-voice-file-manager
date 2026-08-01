"""Desktop Provider implementation (Phase 11.5).

Aggregates DesktopService, ClipboardService, and NotificationService into a unified provider.
Provides health tracking, statistics, capabilities, and diagnostics.
"""

from datetime import datetime, timezone
import time
from typing import Any, Dict, Optional

from brain.os.desktop.clipboard_service import ClipboardService
from brain.os.desktop.desktop_models import (
    DesktopCapabilities,
    DesktopHealth,
    DesktopStatistics,
)
from brain.os.desktop.desktop_service import DesktopService
from brain.os.desktop.interfaces import (
    IClipboardService,
    IDesktopProvider,
    IDesktopService,
    INotificationService,
)
from brain.os.desktop.notification_service import NotificationService
from brain.os.environment_service import EnvironmentService
from brain.os.interfaces import IEnvironmentService, IPathService, IPlatformDetector
from brain.os.path_service import PathService
from brain.os.platform_detector import PlatformDetector


class DesktopProvider(IDesktopProvider):
    """Canonical desktop subsystem provider."""

    def __init__(
        self,
        desktop_service: Optional[IDesktopService] = None,
        clipboard_service: Optional[IClipboardService] = None,
        notification_service: Optional[INotificationService] = None,
        environment_service: Optional[IEnvironmentService] = None,
        path_service: Optional[IPathService] = None,
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

        self._desktop_service = desktop_service or DesktopService(
            environment_service=self._env_service,
            path_service=self._path_service,
            platform_detector=self._detector_comp,
        )
        self._clipboard_service = clipboard_service or ClipboardService()
        self._notification_service = notification_service or NotificationService()

        self._created_at = datetime.now(timezone.utc)
        self._start_time = time.time()
        self._healthy = True

    def get_desktop_service(self) -> IDesktopService:
        """Return desktop service."""
        return self._desktop_service

    def get_clipboard_service(self) -> IClipboardService:
        """Return clipboard service."""
        return self._clipboard_service

    def get_notification_service(self) -> INotificationService:
        """Return notification service."""
        return self._notification_service

    def get_health(self) -> DesktopHealth:
        """Return provider health status."""
        uptime = max(0.0, time.time() - self._start_time)
        info = self._desktop_service.get_desktop_info()

        return DesktopHealth(
            healthy=self._healthy,
            status="READY" if self._healthy else "DEGRADED",
            desktop_env=info.environment,
            uptime_seconds=uptime,
            details={"provider_type": "DesktopProvider"},
        )

    def get_statistics(self) -> DesktopStatistics:
        """Return desktop statistics."""
        info = self._desktop_service.get_desktop_info()
        notifs = len(self._notification_service.get_history())

        return DesktopStatistics(
            total_notifications_sent=notifs,
            total_clipboard_reads=0,
            total_clipboard_writes=0,
            known_folders_count=len(info.known_folders),
        )

    def get_capabilities(self) -> DesktopCapabilities:
        """Return desktop capabilities."""
        return DesktopCapabilities(
            supports_clipboard_text=True,
            supports_clipboard_files=True,
            supports_notifications=True,
            supports_known_folders=True,
        )

    def get_diagnostics(self) -> Dict[str, Any]:
        """Return diagnostic information."""
        health = self.get_health()
        stats = self.get_statistics()

        return {
            "provider_type": "DesktopProvider",
            "healthy": health.healthy,
            "desktop_env": health.desktop_env.value,
            "known_folders_count": stats.known_folders_count,
            "total_notifications_sent": stats.total_notifications_sent,
            "uptime_seconds": health.uptime_seconds,
            "created_at": self._created_at.isoformat(),
        }
