"""Task Management & Long-Running Execution Runtime package for Auralis (Phase 12.5).

Exports domain models, enums, exceptions, interfaces, scheduler, executor, monitor,
persistence, provider, runtime lifecycle manager, and global singleton accessors.
"""

from .exceptions import (
    TaskCancellationError,
    TaskException,
    TaskExecutionError,
    TaskPersistenceError,
    TaskRecoveryError,
)

from .interfaces import (
    ITaskExecutor,
    ITaskMonitor,
    ITaskPersistence,
    ITaskProvider,
    ITaskRuntime,
    ITaskScheduler,
)
from .runtime import get_task_runtime, reset_task_runtime
from .task_executor import TaskExecutor
from .task_models import (
    TaskContext,
    TaskExecution,
    TaskExecutionMode,
    TaskFailureReason,
    TaskHealth,
    TaskPriority,
    TaskProgress,
    TaskRecoveryMode,
    TaskRequest,
    TaskResult,
    TaskStatistics,
    TaskStatus,
)
from .task_monitor import TaskMonitor
from .task_persistence import TaskPersistence
from .task_provider import TaskProvider
from .task_runtime import TaskRuntime, TaskRuntimeStatus
from .task_scheduler import TaskScheduler

__all__ = [
    # Enums & Models
    "TaskStatus",
    "TaskPriority",
    "TaskExecutionMode",
    "TaskFailureReason",
    "TaskRecoveryMode",
    "TaskRequest",
    "TaskContext",
    "TaskProgress",
    "TaskResult",
    "TaskExecution",
    "TaskStatistics",
    "TaskHealth",
    # Exceptions
    "TaskException",
    "TaskExecutionError",
    "TaskCancellationError",
    "TaskPersistenceError",
    "TaskRecoveryError",
    # Interfaces
    "ITaskScheduler",
    "ITaskExecutor",
    "ITaskMonitor",
    "ITaskPersistence",
    "ITaskProvider",
    "ITaskRuntime",
    # Core Components
    "TaskScheduler",
    "TaskExecutor",
    "TaskMonitor",
    "TaskPersistence",
    "TaskProvider",
    "TaskRuntime",
    "TaskRuntimeStatus",
    # Global Accessors
    "get_task_runtime",
    "reset_task_runtime",
]
