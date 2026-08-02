"""Exception hierarchy for the Auralis Command Execution Orchestrator (Phase 12.3).

Defines exception types for preparation, routing, coordination, and abort errors.
"""


class ExecutionOrchestratorException(Exception):
    """Base exception for all Command Execution Orchestrator subsystem errors in Auralis."""

    pass


class ExecutionPreparationError(ExecutionOrchestratorException):
    """Raised when execution request preparation or context creation fails."""

    pass


class ExecutionRoutingError(ExecutionOrchestratorException):
    """Raised when stage routing or subsystem dispatch fails."""

    pass


class ExecutionCoordinationError(ExecutionOrchestratorException):
    """Raised when execution coordination across subsystems encounters an unrecoverable failure."""

    pass


class ExecutionAbortError(ExecutionOrchestratorException):
    """Raised when an execution orchestration is explicitly aborted or cancelled."""

    pass
