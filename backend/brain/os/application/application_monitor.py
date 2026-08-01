"""Application Monitor implementation (Phase 11.3).

Provides thread-safe monitoring of active launched processes, status tracking,
launch history, process metrics, and statistics generation.
"""

from datetime import datetime, timezone
import threading
import time
from typing import Dict, List, Optional

from brain.os.application.application_models import (
    ApplicationState,
    ApplicationStatistics,
    RunningApplication,
)
from brain.os.application.interfaces import IApplicationMonitor


class ApplicationMonitor(IApplicationMonitor):
    """Thread-safe application monitor for process tracking and metrics."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._running_apps: Dict[int, RunningApplication] = {}
        self._total_launches = 0
        self._successful_launches = 0
        self._failed_launches = 0
        self._total_launch_duration_ms = 0.0

    def register_process(
        self, process_id: int, app_id: str, executable_path: str, name: str
    ) -> RunningApplication:
        """Register a launched application process for monitoring."""
        with self._lock:
            app = RunningApplication(
                process_id=process_id,
                app_id=app_id,
                name=name,
                executable_path=executable_path,
                state=ApplicationState.RUNNING,
                launch_time=datetime.now(timezone.utc),
            )
            self._running_apps[process_id] = app
            return app

    def unregister_process(self, process_id: int) -> bool:
        """Remove a process from active monitoring."""
        with self._lock:
            if process_id in self._running_apps:
                del self._running_apps[process_id]
                return True
            return False

    def record_launch(self, success: bool, duration_ms: float = 0.0) -> None:
        """Record launch statistics."""
        with self._lock:
            self._total_launches += 1
            if success:
                self._successful_launches += 1
                self._total_launch_duration_ms += duration_ms
            else:
                self._failed_launches += 1

    def get_running_applications(self) -> List[RunningApplication]:
        """Get list of all currently tracked running applications."""
        with self._lock:
            return list(self._running_apps.values())

    def get_running_application(self, process_id: int) -> Optional[RunningApplication]:
        """Get details for a specific running process ID."""
        with self._lock:
            return self._running_apps.get(process_id)

    def get_statistics(self) -> ApplicationStatistics:
        """Get application launch and performance statistics."""
        with self._lock:
            avg_ms = 0.0
            if self._successful_launches > 0:
                avg_ms = self._total_launch_duration_ms / self._successful_launches

            return ApplicationStatistics(
                total_launches=self._total_launches,
                successful_launches=self._successful_launches,
                failed_launches=self._failed_launches,
                active_applications_count=len(self._running_apps),
                average_launch_time_ms=avg_ms,
            )
