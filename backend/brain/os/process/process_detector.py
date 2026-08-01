"""Process Detector implementation (Phase 11.4).

Provides platform-independent process discovery, enumeration, and lookup by PID,
name, or executable path using psutil.
"""

from datetime import datetime, timezone
import os
import psutil
from typing import List, Optional

from brain.os.environment_service import EnvironmentService
from brain.os.interfaces import IEnvironmentService, IPlatformDetector
from brain.os.platform_detector import PlatformDetector
from brain.os.process.interfaces import IProcessDetector
from brain.os.process.process_models import ProcessInfo, ProcessState


class ProcessDetector(IProcessDetector):
    """Platform-independent process detector."""

    def __init__(
        self,
        environment_service: Optional[IEnvironmentService] = None,
        platform_detector: Optional[IPlatformDetector] = None,
    ) -> None:
        self._detector = platform_detector or PlatformDetector()
        self._env_service = environment_service or EnvironmentService(
            platform_detector=self._detector
        )

    def _map_state(self, status: str) -> ProcessState:
        """Map psutil status string to ProcessState enum."""
        st_lower = status.lower()
        if st_lower in ("running", "active"):
            return ProcessState.RUNNING
        elif st_lower in ("sleeping", "idle"):
            return ProcessState.SLEEPING
        elif st_lower in ("stopped", "tracing stop"):
            return ProcessState.STOPPED
        elif st_lower in ("zombie", "dead"):
            return ProcessState.ZOMBIE
        return ProcessState.UNKNOWN

    def _build_info(self, proc: psutil.Process) -> Optional[ProcessInfo]:
        """Safely extract ProcessInfo model from psutil Process."""
        try:
            pinfo = proc.as_dict(
                attrs=["pid", "ppid", "name", "exe", "cmdline", "status", "create_time", "username"]
            )
            create_t = None
            if pinfo.get("create_time"):
                create_t = datetime.fromtimestamp(pinfo["create_time"], timezone.utc)

            return ProcessInfo(
                process_id=pinfo.get("pid") or 0,
                parent_process_id=pinfo.get("ppid"),
                name=pinfo.get("name") or "",
                executable_path=pinfo.get("exe") or "",
                command_line=pinfo.get("cmdline") or [],
                state=self._map_state(pinfo.get("status") or ""),
                create_time=create_t,
                username=pinfo.get("username") or "",
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None

    def enumerate_processes(self) -> List[ProcessInfo]:
        """Enumerate all active processes on host system."""
        results: List[ProcessInfo] = []
        for proc in psutil.process_iter(
            attrs=["pid", "ppid", "name", "exe", "cmdline", "status", "create_time", "username"]
        ):
            info = self._build_info(proc)
            if info:
                results.append(info)
        return results

    def get_by_pid(self, pid: int) -> Optional[ProcessInfo]:
        """Lookup process by Process ID (PID)."""
        try:
            proc = psutil.Process(pid)
            return self._build_info(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None

    def get_by_executable(self, executable_path: str) -> List[ProcessInfo]:
        """Lookup processes matching executable path."""
        norm_target = executable_path.lower().replace("/", "\\")
        results: List[ProcessInfo] = []
        for info in self.enumerate_processes():
            if info.executable_path:
                norm_exe = info.executable_path.lower().replace("/", "\\")
                if norm_exe == norm_target:
                    results.append(info)
        return results

    def get_by_name(self, name: str) -> List[ProcessInfo]:
        """Lookup processes matching process name."""
        target_name = name.lower()
        results: List[ProcessInfo] = []
        for info in self.enumerate_processes():
            if info.name and info.name.lower() == target_name:
                results.append(info)
        return results
