"""API Integration Exceptions (Phase 15.9).

Defines the exception hierarchy for request coordination, response formatting,
gateway orchestration, and pipeline execution operations.
"""


class ApiIntegrationException(Exception):
    """Base exception for all API integration runtime errors."""

    pass


class RequestCoordinationException(ApiIntegrationException):
    """Raised when request context creation or metadata validation fails."""

    pass


class ResponseCoordinationException(ApiIntegrationException):
    """Raised when response formatting or context encapsulation fails."""

    pass


class PipelineExecutionException(ApiIntegrationException):
    """Raised when pipeline stage execution encounters an unhandled failure."""

    pass
