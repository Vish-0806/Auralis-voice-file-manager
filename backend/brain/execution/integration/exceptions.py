"""Exception hierarchy for the Auralis Execution Runtime Integration (Phase 12.9).

Defines exception types for capability registration, routing, pipeline execution, and runtime errors.
"""


class IntegrationException(Exception):
    """Base exception for all Execution Runtime Integration subsystem errors in Auralis."""

    pass


class CapabilityError(IntegrationException):
    """Raised when capability registration, validation, or lookup fails."""

    pass


class RoutingError(IntegrationException):
    """Raised when execution request routing fails or target is unavailable."""

    pass


class PipelineExecutionError(IntegrationException):
    """Raised when multi-stage pipeline orchestration fails."""

    pass


class IntegrationRuntimeError(IntegrationException):
    """Raised when the Integration Runtime encounters an unrecoverable operational failure."""

    pass
