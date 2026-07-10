"""Module for managing desktop application processes safely using subprocess and psutil."""

from __future__ import annotations

import logging
import os
import subprocess
from typing import Any
import psutil


class ProcessManager:
    """Manages application processes and execution status.

    Enforces safety boundaries to avoid terminating critical OS processes.
    """

    # Core system processes that must not be terminated
    PROTECTED_PROCESSES = {
        "system",
        "registry",
        "smss.exe",
        "csrss.exe",
        "wininit.exe",
        "services.exe",
        "lsass.exe",
        "svchost.exe",
        "explorer.exe",
        "winlogon.exe",
        "spoolsv.exe",
        "taskhostw.exe",
        "dwm.exe",
    }

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes the ProcessManager.

        Args:
            logger: Optional logger for process lifecycle logs.
        """

        self._logger = logger or logging.getLogger(__name__)

    def start_process(self, executable_path: str, arguments: list[str] | None = None) -> int:
        """Starts a process in the background.

        Args:
            executable_path: The absolute path to the application executable.
            arguments: Optional list of command-line arguments to pass.

        Returns:
            The PID of the newly started process.

        Raises:
            FileNotFoundError: If the executable path is invalid or missing.
            OSError: If the execution fails.
        """

        if not os.path.exists(executable_path) or not os.path.isfile(executable_path):
            raise FileNotFoundError(f"Executable not found at path: {executable_path}")

        args = [executable_path] + (arguments or [])
        self._logger.info("Starting process", extra={"command": args})

        try:
            creation_flags = 0
            if os.name == "nt":
                # CREATE_BREAKAWAY_FROM_JOB | DETACHED_PROCESS
                # 0x00000008 | 0x00000010
                creation_flags = 0x00000008 | 0x00000010

            proc = subprocess.Popen(
                args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creation_flags,
                close_fds=True,
            )
            self._logger.info("Process started successfully", extra={"pid": proc.pid})
            return proc.pid
        except Exception as exc:
            self._logger.exception("Failed to start process", extra={"path": executable_path})
            raise OSError(f"Failed to start process {executable_path}: {exc}") from exc

    def terminate_process(self, app_name: str, executable_name: str | None = None) -> bool:
        """Terminates running instances of an application.

        Args:
            app_name: The human-readable application name.
            executable_name: Optional base filename of the executable (e.g., 'chrome.exe').

        Returns:
            True if one or more processes were successfully terminated, False otherwise.

        Raises:
            PermissionError: If attempting to terminate a protected system process.
        """

        target_names = {app_name.lower()}
        if executable_name:
            target_names.add(executable_name.lower())
            if executable_name.lower().endswith(".exe"):
                target_names.add(executable_name.lower()[:-4])

        terminated_count = 0
        protected_ids = self._get_protected_pids()

        for proc in psutil.process_iter(["pid", "name"]):
            try:
                proc_name = proc.info["name"]
                if not proc_name:
                    continue

                if proc_name.lower() in target_names or any(t in proc_name.lower() for t in target_names):
                    pid = proc.info["pid"]
                    if pid in protected_ids or proc_name.lower() in self.PROTECTED_PROCESSES:
                        self._logger.warning(
                            "Blocked termination of protected process",
                            extra={"pid": pid, "process_name": proc_name},
                        )
                        raise PermissionError(f"Termination of system process '{proc_name}' (PID {pid}) is blocked.")

                    self._logger.info("Terminating process", extra={"pid": pid, "process_name": proc_name})
                    proc.terminate()
                    try:
                        proc.wait(timeout=2)
                    except psutil.TimeoutExpired:
                        self._logger.warning("Process did not exit gracefully, killing it", extra={"pid": pid})
                        proc.kill()
                    terminated_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return terminated_count > 0

    def is_running(self, app_name: str, executable_name: str | None = None) -> bool:
        """Checks if an application process is currently running.

        Args:
            app_name: The human-readable application name.
            executable_name: Optional base filename of the executable.

        Returns:
            True if a matching running process is found, False otherwise.
        """

        target_names = {app_name.lower()}
        if executable_name:
            target_names.add(executable_name.lower())
            if executable_name.lower().endswith(".exe"):
                target_names.add(executable_name.lower()[:-4])

        for proc in psutil.process_iter(["name"]):
            try:
                proc_name = proc.info["name"]
                if proc_name and (proc_name.lower() in target_names or any(t in proc_name.lower() for t in target_names)):
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False

    def list_running_pids(self, app_name: str, executable_name: str | None = None) -> list[int]:
        """Returns PIDs of running instances of an application.

        Args:
            app_name: The human-readable application name.
            executable_name: Optional base filename of the executable.

        Returns:
            A list of active process IDs (PIDs).
        """

        target_names = {app_name.lower()}
        if executable_name:
            target_names.add(executable_name.lower())
            if executable_name.lower().endswith(".exe"):
                target_names.add(executable_name.lower()[:-4])

        pids = []
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                proc_name = proc.info["name"]
                if proc_name and (proc_name.lower() in target_names or any(t in proc_name.lower() for t in target_names)):
                    pids.append(proc.info["pid"])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return pids

    def _get_protected_pids(self) -> set[int]:
        """Retrieves PIDs of protected processes that should never be terminated."""

        protected = {0, 4, os.getpid()}

        try:
            parent = psutil.Process(os.getpid()).parent()
            if parent:
                protected.add(parent.pid)
        except Exception:
            pass

        return protected
