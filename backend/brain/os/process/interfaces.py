"""Abstract interfaces for Process Subsystem (Phase 11.4).

Defines canonical interfaces for Process Detector, Service, Monitor, Controller,
Provider, and Runtime.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from brain.os.process.process_models import (
    ProcessCapabilities,
    ProcessHealth,
    ProcessInfo,
    ProcessResourceUsage,
    ProcessRuntimeStatus,
    ProcessStatistics,
    ProcessTerminationResult,
    RunningProcess,
    TerminationMode,
)


class IProcessDetector(ABC):
    """Interface for process discovery and lookup."""

    @abstractmethod
    def enumerate_processes(self) -> List[ProcessInfo]:
        """Enumerate all active processes on host system."""
        pass

    @abstractmethod
    def get_by_pid(self, pid: int) -> Optional[ProcessInfo]:
        """Lookup process by Process ID (PID)."""
        pass

    @abstractmethod
    def get_by_executable(self, executable_path: str) -> List[ProcessInfo]:
        """Lookup processes matching executable path."""
        pass

    @abstractmethod
    def get_by_name(self, name: str) -> List[ProcessInfo]:
        """Lookup processes matching process name."""
        pass


class IProcessService(ABC):
    """Interface for process detailed inspection and resource metrics."""

    @abstractmethod
    def get_running_process(self, pid: int) -> RunningProcess:
        """Retrieve comprehensive running process metadata."""
        pass

    @abstractmethod
    def get_resource_usage(self, pid: int) -> ProcessResourceUsage:
        """Retrieve process resource consumption snapshot."""
        pass

    @abstractmethod
    def get_parent_process_id(self, pid: int) -> Optional[int]:
        """Get parent PID for a process."""
        pass

    @abstractmethod
    def get_child_process_ids(self, pid: int) -> List[int]:
        """Get child process PIDs for a process."""
        pass

    @abstractmethod
    def get_command_line(self, pid: int) -> List[str]:
        """Get command line arguments for a process."""
        pass

    @abstractmethod
    def get_working_directory(self, pid: int) -> Optional[str]:
        """Get working directory path for a process."""
        pass


class IProcessMonitor(ABC):
    """Interface for process lifecycle and resource usage monitoring."""

    @abstractmethod
    def start_monitoring(self, pid: int) -> RunningProcess:
        """Begin monitoring an active process."""
        pass

    @abstractmethod
    def stop_monitoring(self, pid: int) -> bool:
        """Stop monitoring a process."""
        pass

    @abstractmethod
    def get_monitored_processes(self) -> List[RunningProcess]:
        """List all currently monitored processes."""
        pass

    @abstractmethod
    def get_statistics(self) -> ProcessStatistics:
        """Get process subsystem performance statistics."""
        pass


class IProcessController(ABC):
    """Interface for process lifecycle control, termination, and tree cleanup."""

    @abstractmethod
    def terminate_process(
        self,
        pid: int,
        mode: TerminationMode = TerminationMode.GRACEFUL,
        timeout_seconds: float = 5.0,
    ) -> ProcessTerminationResult:
        """Safely terminate a process."""
        pass

    @abstractmethod
    def terminate_process_tree(
        self, pid: int, mode: TerminationMode = TerminationMode.GRACEFUL
    ) -> List[ProcessTerminationResult]:
        """Safely terminate a process and all its child processes."""
        pass

    @abstractmethod
    def wait_for_completion(
        self, pid: int, timeout_seconds: float = 5.0
    ) -> Optional[int]:
        """Wait for process completion and return exit code."""
        pass


class IProcessProvider(ABC):
    """Interface for Process Subsystem Provider."""

    @abstractmethod
    def get_detector(self) -> IProcessDetector:
        """Return process detector."""
        pass

    @abstractmethod
    def get_service(self) -> IProcessService:
        """Return process service."""
        pass

    @abstractmethod
    def get_monitor(self) -> IProcessMonitor:
        """Return process monitor."""
        pass

    @abstractmethod
    def get_controller(self) -> IProcessController:
        """Return process controller."""
        pass

    @abstractmethod
    def get_health(self) -> ProcessHealth:
        """Return provider health status."""
        pass

    @abstractmethod
    def get_statistics(self) -> ProcessStatistics:
        """Return process statistics."""
        pass

    @abstractmethod
    def get_capabilities(self) -> ProcessCapabilities:
        """Return process capabilities."""
        pass

    @abstractmethod
    def get_diagnostics(self) -> Dict[str, Any]:
        """Return diagnostic information."""
        pass


class IProcessRuntime(ABC):
    """Interface for Process Runtime coordinator."""

    @abstractmethod
    def initialize(self) -> None:
        """Initialize process runtime."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown process runtime."""
        pass

    @abstractmethod
    def register_provider(self, provider: IProcessProvider) -> None:
        """Register process provider."""
        pass

    @abstractmethod
    def get_provider(self) -> Optional[IProcessProvider]:
        """Get registered process provider."""
        pass

    @abstractmethod
    def get_statistics(self) -> ProcessStatistics:
        """Get process runtime performance statistics."""
        pass

    @abstractmethod
    def get_health(self) -> ProcessRuntimeStatus:
        """Get overall runtime health status."""
        pass

    @abstractmethod
    def get_diagnostics(self) -> Dict[str, Any]:
        """Get runtime diagnostics dictionary."""
        pass
