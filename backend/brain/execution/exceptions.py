"""Exceptions for the Auralis Brain Execution Engine Subsystem (Phase 12.1).

Defines exception types for request validation, execution routing, pipeline execution failures,
and execution cancellation.
"""


class ExecutionException(Exception):
    """Base exception for all Execution Engine subsystem errors in Auralis."""

    pass


class ExecutionValidationError(ExecutionException):
    """Raised when request validation or normalization fails."""

    pass


class ExecutionRoutingError(ExecutionException):
    """Raised when request routing or decision engine evaluation fails."""

    pass


class ExecutionFailure(ExecutionException):
    """Raised when an unrecoverable failure occurs during execution pipeline orchestration."""

    pass


class ExecutionCancelled(ExecutionException):
    """Raised when execution is cancelled by user or subsystem request."""

    pass
