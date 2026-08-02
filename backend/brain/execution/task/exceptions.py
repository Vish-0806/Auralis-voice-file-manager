"""Exception hierarchy for the Auralis Task Management Runtime (Phase 12.5).

Defines exception types for execution, cancellation, persistence, and recovery failures.
"""


class TaskException(Exception):
    """Base exception for all Task Management Runtime subsystem errors in Auralis."""

    pass


class TaskExecutionError(TaskException):
    """Raised when task execution fails unrecoverably."""

    pass


class TaskCancellationError(TaskException):
    """Raised when a task execution is cancelled."""

    pass


class TaskPersistenceError(TaskException):
    """Raised when persisting or restoring task state checkpoints fails."""

    pass


class TaskRecoveryError(TaskException):
    """Raised when recovering a failed task encounters an error."""

    pass
