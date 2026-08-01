"""Process Monitor implementation (Phase 11.4).

Provides thread-safe lifecycle tracking of monitored processes, resource usage metrics,
and subsystem statistics generation.
"""

import threading
from typing import Dict, List, Optional

from brain.os.process.interfaces import IProcessDetector, IProcessMonitor, IProcessService
from brain.os.process.process_detector import ProcessDetector
from brain.os.process.process_models import ProcessStatistics, RunningProcess
from brain.os.process.process_service import ProcessService


class ProcessMonitor(IProcessMonitor):
    """Thread-safe process monitor for tracking active system processes."""

    def __init__(
        self,
        detector: Optional[IProcessDetector] = None,
        service: Optional[IProcessService] = None,
    ) -> None:
        self._lock = threading.RLock()
        self._detector = detector or ProcessDetector()
        self._service = service or ProcessService(detector=self._detector)
        self._monitored_pids: Dict[int, RunningProcess] = {}
        self._total_inspected = 0
        self._total_terminations = 0
        self._successful_terminations = 0
        self._failed_terminations = 0

    def start_monitoring(self, pid: int) -> RunningProcess:
        """Begin monitoring an active process."""
        with self._lock:
            running = self._service.get_running_process(pid)
            self._monitored_pids[pid] = running
            self._total_inspected += 1
            return running

    def stop_monitoring(self, pid: int) -> bool:
        """Stop monitoring a process."""
        with self._lock:
            if pid in self._monitored_pids:
                del self._monitored_pids[pid]
                return True
            return False

    def record_termination(self, success: bool) -> None:
        """Record termination attempt metric."""
        with self._lock:
            self._total_terminations += 1
            if success:
                self._successful_terminations += 1
            else:
                self._failed_terminations += 1

    def get_monitored_processes(self) -> List[RunningProcess]:
        """List all currently monitored processes."""
        with self._lock:
            active: List[RunningProcess] = []
            stale_pids: List[int] = []
            for pid in list(self._monitored_pids.keys()):
                try:
                    proc_info = self._service.get_running_process(pid)
                    self._monitored_pids[pid] = proc_info
                    active.append(proc_info)
                except Exception:
                    stale_pids.append(pid)

            for spid in stale_pids:
                self._monitored_pids.pop(spid, None)

            return active

    def get_statistics(self) -> ProcessStatistics:
        """Get process subsystem performance statistics."""
        with self._lock:
            return ProcessStatistics(
                total_processes_inspected=self._total_inspected,
                active_monitored_processes=len(self._monitored_pids),
                total_terminations=self._total_terminations,
                successful_terminations=self._successful_terminations,
                failed_terminations=self._failed_terminations,
            )
