"""Process Controller implementation (Phase 11.4).

Provides safe process termination, process tree cleanup, timeout waiting,
and validation preventing termination of critical system processes or PID 0/1/current PID.
"""

import os
import psutil
import time
from typing import List, Optional

from brain.os.process.exceptions import (
    ProcessNotFoundError,
    ProcessPermissionError,
    ProcessTerminationError,
    ProcessTimeoutError,
)
from brain.os.process.interfaces import IProcessController, IProcessService
from brain.os.process.process_models import (
    ProcessTerminationResult,
    TerminationMode,
)
from brain.os.process.process_service import ProcessService


class ProcessController(IProcessController):
    """Provides safe process lifecycle management, termination, and tree cleanup."""

    def __init__(self, service: Optional[IProcessService] = None) -> None:
        self._service = service or ProcessService()

    def _validate_safety(self, pid: int) -> None:
        """Validate safety constraints before process termination."""
        current_pid = os.getpid()
        if pid == current_pid:
            raise ProcessPermissionError(
                f"Cannot terminate self (current PID {current_pid})", process_id=pid
            )

        # Critical system PIDs
        if pid <= 4:
            raise ProcessPermissionError(
                f"Cannot terminate critical system PID {pid}", process_id=pid
            )

        try:
            info = self._service.get_running_process(pid)
            if info.is_system_process and info.info.name.lower() in (
                "system",
                "smss.exe",
                "csrss.exe",
                "wininit.exe",
                "services.exe",
                "lsass.exe",
                "init",
                "systemd",
            ):
                raise ProcessPermissionError(
                    f"Cannot terminate protected system process '{info.info.name}' (PID {pid})",
                    process_id=pid,
                )
        except (ProcessNotFoundError, ProcessPermissionError):
            raise

    def wait_for_completion(
        self, pid: int, timeout_seconds: float = 5.0
    ) -> Optional[int]:
        """Wait for process completion and return exit code."""
        try:
            proc = psutil.Process(pid)
            gone, _ = psutil.wait_procs([proc], timeout=timeout_seconds)
            if gone:
                return gone[0].returncode
            return None
        except psutil.NoSuchProcess:
            return 0

    def terminate_process(
        self,
        pid: int,
        mode: TerminationMode = TerminationMode.GRACEFUL,
        timeout_seconds: float = 5.0,
    ) -> ProcessTerminationResult:
        """Safely terminate a process."""
        start_t = time.time()
        self._validate_safety(pid)

        try:
            proc = psutil.Process(pid)
        except psutil.NoSuchProcess:
            raise ProcessNotFoundError(f"Process PID {pid} not found", process_id=pid)

        try:
            if mode == TerminationMode.GRACEFUL:
                proc.terminate()
            else:
                proc.kill()

            gone, _ = psutil.wait_procs([proc], timeout=timeout_seconds)
            duration = (time.time() - start_t) * 1000.0

            if gone:
                exit_code = gone[0].returncode
                return ProcessTerminationResult(
                    success=True,
                    process_id=pid,
                    mode=mode,
                    exit_code=exit_code,
                    duration_ms=duration,
                )
            else:
                # Fallback to force kill if graceful timed out
                if mode == TerminationMode.GRACEFUL:
                    proc.kill()
                    gone, _ = psutil.wait_procs([proc], timeout=2.0)
                    duration = (time.time() - start_t) * 1000.0
                    return ProcessTerminationResult(
                        success=True,
                        process_id=pid,
                        mode=TerminationMode.FORCE,
                        exit_code=gone[0].returncode if gone else None,
                        duration_ms=duration,
                    )
                raise ProcessTimeoutError(f"Process PID {pid} did not exit within {timeout_seconds}s", process_id=pid)
        except (psutil.AccessDenied, ProcessPermissionError) as e:
            duration = (time.time() - start_t) * 1000.0
            raise ProcessPermissionError(f"Permission denied terminating PID {pid}: {e}", process_id=pid)
        except Exception as e:
            duration = (time.time() - start_t) * 1000.0
            raise ProcessTerminationError(f"Failed to terminate PID {pid}: {e}", process_id=pid)

    def terminate_process_tree(
        self, pid: int, mode: TerminationMode = TerminationMode.GRACEFUL
    ) -> List[ProcessTerminationResult]:
        """Safely terminate a process and all its child processes."""
        self._validate_safety(pid)

        results: List[ProcessTerminationResult] = []
        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
        except psutil.NoSuchProcess:
            raise ProcessNotFoundError(f"Process PID {pid} not found", process_id=pid)

        # Terminate children first (leaf to root)
        for child in reversed(children):
            try:
                res = self.terminate_process(child.pid, mode=mode, timeout_seconds=2.0)
                results.append(res)
            except Exception as e:
                results.append(
                    ProcessTerminationResult(
                        success=False,
                        process_id=child.pid,
                        mode=mode,
                        error=str(e),
                    )
                )

        # Terminate parent
        parent_res = self.terminate_process(pid, mode=mode, timeout_seconds=3.0)
        results.append(parent_res)
        return results
