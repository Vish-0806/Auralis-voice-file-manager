"""Exception hierarchy for the Auralis Workflow Execution Engine (Phase 12.4).

Defines exception types for validation, dependency graph, execution, and cancellation errors.
"""


class WorkflowException(Exception):
    """Base exception for all Workflow Execution Engine subsystem errors in Auralis."""

    pass


class WorkflowValidationError(WorkflowException):
    """Raised when workflow validation fails (e.g. cycles, missing steps, duplicate IDs)."""

    pass


class WorkflowDependencyError(WorkflowException):
    """Raised when dependency resolution or step ordering encounters an error."""

    pass


class WorkflowExecutionError(WorkflowException):
    """Raised when a workflow step or pipeline execution fails unrecoverably."""

    pass


class WorkflowCancellationError(WorkflowException):
    """Raised when a workflow execution is cancelled."""

    pass
