"""Process Service implementation (Phase 11.4).

Provides detailed inspection of process CPU, memory usage, thread count, handle count,
parent/child relationships, command line arguments, and working directory details.
"""

from datetime import datetime, timezone
import os
import psutil
from typing import List, Optional

from brain.os.process.exceptions import ProcessNotFoundError, ProcessPermissionError
from brain.os.process.interfaces import IProcessDetector, IProcessService
from brain.os.process.process_detector import ProcessDetector
from brain.os.process.process_models import (
    ProcessInfo,
    ProcessResourceUsage,
    RunningProcess,
)


class ProcessService(IProcessService):
    """Provides detailed process metrics and relationship inspection."""

    def __init__(self, detector: Optional[IProcessDetector] = None) -> None:
        self._detector = detector or ProcessDetector()

    def _get_psutil_proc(self, pid: int) -> psutil.Process:
        """Helper to retrieve psutil.Process or raise custom exception."""
        try:
            return psutil.Process(pid)
        except psutil.NoSuchProcess:
            raise ProcessNotFoundError(f"Process PID {pid} not found", process_id=pid)
        except psutil.AccessDenied:
            raise ProcessPermissionError(f"Permission denied accessing PID {pid}", process_id=pid)

    def get_running_process(self, pid: int) -> RunningProcess:
        """Retrieve comprehensive running process metadata."""
        proc = self._get_psutil_proc(pid)
        info = self._detector.get_by_pid(pid)
        if not info:
            raise ProcessNotFoundError(f"Process PID {pid} not found", process_id=pid)

        try:
            cpu_p = proc.cpu_percent(interval=None)
            mem_info = proc.memory_info()
            mem_p = proc.memory_percent()
            num_t = proc.num_threads()
            try:
                num_h = proc.num_handles() if hasattr(proc, "num_handles") else 0
            except Exception:
                num_h = 0

            # System process check (PID <= 4 on Windows, PID <= 2 on Unix)
            is_sys = pid <= 4 or info.username.lower() in ("system", "root")

            return RunningProcess(
                info=info,
                cpu_percent=cpu_p,
                memory_bytes=mem_info.rss,
                memory_percent=mem_p,
                num_threads=num_t,
                num_handles=num_h,
                is_system_process=is_sys,
            )
        except psutil.AccessDenied:
            raise ProcessPermissionError(f"Permission denied inspecting PID {pid}", process_id=pid)
        except psutil.NoSuchProcess:
            raise ProcessNotFoundError(f"Process PID {pid} exited", process_id=pid)

    def get_resource_usage(self, pid: int) -> ProcessResourceUsage:
        """Retrieve process resource consumption snapshot."""
        proc = self._get_psutil_proc(pid)
        try:
            cpu_p = proc.cpu_percent(interval=None)
            mem = proc.memory_info()
            num_t = proc.num_threads()

            open_files_cnt = 0
            try:
                open_files_cnt = len(proc.open_files())
            except Exception:
                pass

            io_r = 0
            io_w = 0
            try:
                io_counters = proc.io_counters()
                io_r = io_counters.read_bytes
                io_w = io_counters.write_bytes
            except Exception:
                pass

            return ProcessResourceUsage(
                process_id=pid,
                cpu_percent=cpu_p,
                memory_rss_bytes=mem.rss,
                memory_vms_bytes=mem.vms,
                num_threads=num_t,
                open_files_count=open_files_cnt,
                io_read_bytes=io_r,
                io_write_bytes=io_w,
                timestamp=datetime.now(timezone.utc),
            )
        except psutil.AccessDenied:
            raise ProcessPermissionError(f"Permission denied inspecting PID {pid}", process_id=pid)
        except psutil.NoSuchProcess:
            raise ProcessNotFoundError(f"Process PID {pid} exited", process_id=pid)

    def get_parent_process_id(self, pid: int) -> Optional[int]:
        """Get parent PID for a process."""
        proc = self._get_psutil_proc(pid)
        try:
            parent = proc.parent()
            return parent.pid if parent else None
        except Exception:
            return None

    def get_child_process_ids(self, pid: int) -> List[int]:
        """Get child process PIDs for a process."""
        proc = self._get_psutil_proc(pid)
        try:
            children = proc.children(recursive=True)
            return [c.pid for c in children]
        except Exception:
            return []

    def get_command_line(self, pid: int) -> List[str]:
        """Get command line arguments for a process."""
        proc = self._get_psutil_proc(pid)
        try:
            return proc.cmdline()
        except Exception:
            return []

    def get_working_directory(self, pid: int) -> Optional[str]:
        """Get working directory path for a process."""
        proc = self._get_psutil_proc(pid)
        try:
            return proc.cwd()
        except Exception:
            return None
