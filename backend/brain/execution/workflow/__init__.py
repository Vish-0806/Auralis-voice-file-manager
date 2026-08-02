"""Workflow Execution Engine subsystem package for Auralis (Phase 12.4).

Exports domain models, enums, exceptions, interfaces, builder, validator, scheduler,
executor, provider, runtime lifecycle manager, and global singleton accessors.
"""

from .exceptions import (
    WorkflowCancellationError,
    WorkflowDependencyError,
    WorkflowException,
    WorkflowExecutionError,
    WorkflowValidationError,
)

from .interfaces import (
    IWorkflowBuilder,
    IWorkflowExecutor,
    IWorkflowProvider,
    IWorkflowScheduler,
    IWorkflowRuntime,
    IWorkflowValidator,
)
from .runtime import get_workflow_runtime, reset_workflow_runtime
from .workflow_builder import WorkflowBuilder
from .workflow_executor import WorkflowExecutor
from .workflow_models import (
    DependencyType,
    WorkflowContext,
    WorkflowDependency,
    WorkflowExecution,
    WorkflowExecutionMode,
    WorkflowHealth,
    WorkflowPriority,
    WorkflowRequest,
    WorkflowResult,
    WorkflowStatistics,
    WorkflowStatus,
    WorkflowStep,
    WorkflowStepStatus,
)
from .workflow_provider import WorkflowProvider
from .workflow_runtime import WorkflowRuntime, WorkflowRuntimeStatus
from .workflow_scheduler import WorkflowScheduler
from .workflow_validator import WorkflowValidator

__all__ = [
    # Enums & Models
    "WorkflowStatus",
    "WorkflowStepStatus",
    "WorkflowExecutionMode",
    "DependencyType",
    "WorkflowPriority",
    "WorkflowDependency",
    "WorkflowStep",
    "WorkflowRequest",
    "WorkflowContext",
    "WorkflowExecution",
    "WorkflowResult",
    "WorkflowStatistics",
    "WorkflowHealth",
    # Exceptions
    "WorkflowException",
    "WorkflowValidationError",
    "WorkflowDependencyError",
    "WorkflowExecutionError",
    "WorkflowCancellationError",
    # Interfaces
    "IWorkflowBuilder",
    "IWorkflowValidator",
    "IWorkflowScheduler",
    "IWorkflowExecutor",
    "IWorkflowProvider",
    "IWorkflowRuntime",
    # Core Components
    "WorkflowBuilder",
    "WorkflowValidator",
    "WorkflowScheduler",
    "WorkflowExecutor",
    "WorkflowProvider",
    "WorkflowRuntime",
    "WorkflowRuntimeStatus",
    # Global Accessors
    "get_workflow_runtime",
    "reset_workflow_runtime",
]
