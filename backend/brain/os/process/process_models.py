"""Process Subsystem Domain Models for Auralis (Phase 11.4).

Defines immutable Pydantic v2 models and enums representing operating system processes,
running process metadata, resource usage metrics, termination requests/results,
performance statistics, capabilities, health status, and runtime state.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


class ProcessState(str, Enum):
    """Execution state of an OS process."""

    RUNNING = "running"
    SLEEPING = "sleeping"
    STOPPED = "stopped"
    ZOMBIE = "zombie"
    TERMINATED = "terminated"
    UNKNOWN = "unknown"


class TerminationMode(str, Enum):
    """Termination signal modes."""

    GRACEFUL = "graceful"
    FORCE = "force"


class TimeoutPolicy(str, Enum):
    """Timeout policies for process completion waiting."""

    WAIT = "wait"
    NOWAIT = "nowait"


class ProcessInfo(BaseModel):
    """Immutable basic process identification metadata."""

    model_config = ConfigDict(frozen=True)

    process_id: int = 0
    parent_process_id: Optional[int] = None
    name: str = ""
    executable_path: str = ""
    command_line: List[str] = Field(default_factory=list)
    state: ProcessState = ProcessState.UNKNOWN
    create_time: Optional[datetime] = None
    username: str = ""


class RunningProcess(BaseModel):
    """Immutable detailed metadata for a running process."""

    model_config = ConfigDict(frozen=True)

    info: ProcessInfo = Field(default_factory=ProcessInfo)
    cpu_percent: float = 0.0
    memory_bytes: int = 0
    memory_percent: float = 0.0
    num_threads: int = 1
    num_handles: int = 0
    is_system_process: bool = False


class ProcessResourceUsage(BaseModel):
    """Immutable process resource consumption metrics snapshot."""

    model_config = ConfigDict(frozen=True)

    process_id: int = 0
    cpu_percent: float = 0.0
    memory_rss_bytes: int = 0
    memory_vms_bytes: int = 0
    num_threads: int = 1
    open_files_count: int = 0
    io_read_bytes: int = 0
    io_write_bytes: int = 0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProcessLaunchInfo(BaseModel):
    """Immutable process launch info metadata."""

    model_config = ConfigDict(frozen=True)

    executable_path: str = ""
    arguments: List[str] = Field(default_factory=list)
    working_directory: Optional[str] = None
    process_id: int = 0
    launched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProcessTerminationResult(BaseModel):
    """Immutable result of a process termination request."""

    model_config = ConfigDict(frozen=True)

    success: bool = True
    process_id: int = 0
    mode: TerminationMode = TerminationMode.GRACEFUL
    exit_code: Optional[int] = None
    duration_ms: float = 0.0
    error: Optional[str] = None


class ProcessStatistics(BaseModel):
    """Immutable process subsystem runtime statistics."""

    model_config = ConfigDict(frozen=True)

    total_processes_inspected: int = 0
    active_monitored_processes: int = 0
    total_terminations: int = 0
    successful_terminations: int = 0
    failed_terminations: int = 0


class ProcessCapabilities(BaseModel):
    """Immutable process runtime capabilities report."""

    model_config = ConfigDict(frozen=True)

    supports_process_enumeration: bool = True
    supports_tree_termination: bool = True
    supports_resource_metrics: bool = True
    supports_graceful_termination: bool = True


class ProcessHealth(BaseModel):
    """Immutable health summary for the Process Subsystem."""

    model_config = ConfigDict(frozen=True)

    healthy: bool = True
    status: str = "READY"
    monitored_count: int = 0
    total_inspected: int = 0
    uptime_seconds: float = 0.0
    details: Dict[str, Any] = Field(default_factory=dict)


class ProcessRuntimeStatus(BaseModel):
    """Immutable overall Process Runtime status report."""

    model_config = ConfigDict(frozen=True)

    state: str = "Initializing"
    healthy: bool = True
    provider_registered: bool = False
    monitored_processes_count: int = 0
    total_terminations: int = 0
    uptime_seconds: float = 0.0
