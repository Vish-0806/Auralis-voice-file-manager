"""Exception hierarchy for the Auralis Execution Recovery & State Management Runtime (Phase 12.8).

Defines exception types for checkpoint, state store, recovery, and rollback errors.
"""


class RecoveryException(Exception):
    """Base exception for all Execution Recovery subsystem errors in Auralis."""

    pass


class CheckpointError(RecoveryException):
    """Raised when checkpoint creation, loading, or validation fails."""

    pass


class StateStoreError(RecoveryException):
    """Raised when persisting or querying execution state snapshots fails."""

    pass


class RecoveryExecutionError(RecoveryException):
    """Raised when executing a recovery strategy fails unrecoverably."""

    pass


class RollbackError(RecoveryException):
    """Raised when executing a rollback operation fails."""

    pass
