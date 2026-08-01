"""Process Subsystem for Auralis Operating System Abstraction (Phase 11.4).

Exports domain models, enums, exceptions, abstract interfaces, services,
provider, runtime coordinator, and singleton accessors.
"""

from brain.os.process.exceptions import (
    ProcessException,
    ProcessNotFoundError,
    ProcessPermissionError,
    ProcessTerminationError,
    ProcessTimeoutError,
)
from brain.os.process.interfaces import (
    IProcessController,
    IProcessDetector,
    IProcessMonitor,
    IProcessProvider,
    IProcessRuntime,
    IProcessService,
)

from brain.os.process.process_controller import ProcessController
from brain.os.process.process_detector import ProcessDetector
from brain.os.process.process_models import (
    ProcessCapabilities,
    ProcessHealth,
    ProcessInfo,
    ProcessLaunchInfo,
    ProcessResourceUsage,
    ProcessRuntimeStatus,
    ProcessState,
    ProcessStatistics,
    ProcessTerminationResult,
    RunningProcess,
    TerminationMode,
    TimeoutPolicy,
)
from brain.os.process.process_monitor import ProcessMonitor
from brain.os.process.process_provider import ProcessProvider
from brain.os.process.process_runtime import ProcessRuntime
from brain.os.process.process_service import ProcessService
from brain.os.process.runtime import get_process_runtime, reset_process_runtime

__all__ = [
    # Enums
    "ProcessState",
    "TerminationMode",
    "TimeoutPolicy",
    # Models
    "ProcessInfo",
    "RunningProcess",
    "ProcessResourceUsage",
    "ProcessLaunchInfo",
    "ProcessTerminationResult",
    "ProcessStatistics",
    "ProcessCapabilities",
    "ProcessHealth",
    "ProcessRuntimeStatus",
    # Exceptions
    "ProcessException",
    "ProcessNotFoundError",
    "ProcessTerminationError",
    "ProcessPermissionError",
    "ProcessTimeoutError",
    # Interfaces
    "IProcessDetector",
    "IProcessService",
    "IProcessMonitor",
    "IProcessController",
    "IProcessProvider",
    "IProcessRuntime",
    # Services & Implementations
    "ProcessDetector",
    "ProcessService",
    "ProcessMonitor",
    "ProcessController",
    "ProcessProvider",
    "ProcessRuntime",
    # Singleton Accessors
    "get_process_runtime",
    "reset_process_runtime",
]
