"""Window Monitor implementation (Phase 11.6).

Provides thread-safe monitoring of active windows, focus state tracking,
operation metrics, and statistics generation.
"""

import threading
from typing import Dict, List, Optional

from brain.os.window.interfaces import IWindowDetector, IWindowMonitor, IWindowService
from brain.os.window.window_detector import WindowDetector
from brain.os.window.window_models import WindowInfo, WindowStatistics
from brain.os.window.window_service import WindowService


class WindowMonitor(IWindowMonitor):
    """Thread-safe window monitor for tracking active desktop windows."""

    def __init__(
        self,
        detector: Optional[IWindowDetector] = None,
        service: Optional[IWindowService] = None,
    ) -> None:
        self._lock = threading.RLock()
        self._detector = detector or WindowDetector()
        self._service = service or WindowService(detector=self._detector)
        self._monitored_windows: Dict[str, WindowInfo] = {}
        self._total_inspected = 0
        self._total_operations = 0
        self._successful_operations = 0
        self._failed_operations = 0

    def start_monitoring(self, window_id: str) -> WindowInfo:
        """Begin tracking a window."""
        with self._lock:
            win = self._service.get_window(window_id)
            self._monitored_windows[window_id] = win
            self._total_inspected += 1
            return win

    def stop_monitoring(self, window_id: str) -> bool:
        """Stop tracking a window."""
        with self._lock:
            if window_id in self._monitored_windows:
                del self._monitored_windows[window_id]
                return True
            return False

    def record_operation(self, success: bool) -> None:
        """Record window operation metrics."""
        with self._lock:
            self._total_operations += 1
            if success:
                self._successful_operations += 1
            else:
                self._failed_operations += 1

    def get_monitored_windows(self) -> List[WindowInfo]:
        """List currently monitored windows."""
        with self._lock:
            active: List[WindowInfo] = []
            stale_ids: List[str] = []
            for wid in list(self._monitored_windows.keys()):
                try:
                    win = self._service.get_window(wid)
                    self._monitored_windows[wid] = win
                    active.append(win)
                except Exception:
                    stale_ids.append(wid)

            for sid in stale_ids:
                self._monitored_windows.pop(sid, None)

            return active

    def get_statistics(self) -> WindowStatistics:
        """Get window subsystem performance statistics."""
        with self._lock:
            return WindowStatistics(
                total_windows_inspected=self._total_inspected,
                active_windows_count=len(self._monitored_windows),
                total_operations=self._total_operations,
                successful_operations=self._successful_operations,
                failed_operations=self._failed_operations,
            )
