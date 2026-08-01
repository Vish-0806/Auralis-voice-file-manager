"""Process Provider implementation (Phase 11.4).

Aggregates ProcessDetector, ProcessService, ProcessMonitor, and ProcessController
into a unified provider. Provides health tracking, statistics, capabilities, and diagnostics.
"""

from datetime import datetime, timezone
import time
from typing import Any, Dict, Optional

from brain.os.environment_service import EnvironmentService
from brain.os.interfaces import IEnvironmentService, IPlatformDetector
from brain.os.platform_detector import PlatformDetector
from brain.os.process.interfaces import (
    IProcessController,
    IProcessDetector,
    IProcessMonitor,
    IProcessProvider,
    IProcessService,
)
from brain.os.process.process_controller import ProcessController
from brain.os.process.process_detector import ProcessDetector
from brain.os.process.process_models import (
    ProcessCapabilities,
    ProcessHealth,
    ProcessStatistics,
)
from brain.os.process.process_monitor import ProcessMonitor
from brain.os.process.process_service import ProcessService


class ProcessProvider(IProcessProvider):
    """Canonical process subsystem provider."""

    def __init__(
        self,
        detector: Optional[IProcessDetector] = None,
        service: Optional[IProcessService] = None,
        monitor: Optional[IProcessMonitor] = None,
        controller: Optional[IProcessController] = None,
        environment_service: Optional[IEnvironmentService] = None,
        platform_detector: Optional[IPlatformDetector] = None,
    ) -> None:
        self._detector_comp = platform_detector or PlatformDetector()
        self._env_service = environment_service or EnvironmentService(
            platform_detector=self._detector_comp
        )

        self._detector = detector or ProcessDetector(
            environment_service=self._env_service,
            platform_detector=self._detector_comp,
        )
        self._service = service or ProcessService(detector=self._detector)
        self._monitor = monitor or ProcessMonitor(
            detector=self._detector, service=self._service
        )
        self._controller = controller or ProcessController(service=self._service)

        self._created_at = datetime.now(timezone.utc)
        self._start_time = time.time()
        self._healthy = True

    def get_detector(self) -> IProcessDetector:
        """Return process detector."""
        return self._detector

    def get_service(self) -> IProcessService:
        """Return process service."""
        return self._service

    def get_monitor(self) -> IProcessMonitor:
        """Return process monitor."""
        return self._monitor

    def get_controller(self) -> IProcessController:
        """Return process controller."""
        return self._controller

    def get_health(self) -> ProcessHealth:
        """Return provider health status."""
        uptime = max(0.0, time.time() - self._start_time)
        stats = self.get_statistics()

        return ProcessHealth(
            healthy=self._healthy,
            status="READY" if self._healthy else "DEGRADED",
            monitored_count=stats.active_monitored_processes,
            total_inspected=stats.total_processes_inspected,
            uptime_seconds=uptime,
            details={"provider_type": "ProcessProvider"},
        )

    def get_statistics(self) -> ProcessStatistics:
        """Return process statistics."""
        return self._monitor.get_statistics()

    def get_capabilities(self) -> ProcessCapabilities:
        """Return process capabilities."""
        return ProcessCapabilities(
            supports_process_enumeration=True,
            supports_tree_termination=True,
            supports_resource_metrics=True,
            supports_graceful_termination=True,
        )

    def get_diagnostics(self) -> Dict[str, Any]:
        """Return diagnostic information."""
        health = self.get_health()
        stats = self.get_statistics()

        return {
            "provider_type": "ProcessProvider",
            "healthy": health.healthy,
            "monitored_count": health.monitored_count,
            "total_inspected": health.total_inspected,
            "total_terminations": stats.total_terminations,
            "uptime_seconds": health.uptime_seconds,
            "created_at": self._created_at.isoformat(),
        }
