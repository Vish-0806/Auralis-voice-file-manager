"""API Middleware Exceptions (Phase 15.3).

Defines the exception hierarchy for middleware registration, pipeline construction,
execution engine operations, and duplicate middleware detection.
"""


class MiddlewareException(Exception):
    """Base exception for all middleware runtime errors."""

    pass


class MiddlewareRegistrationException(MiddlewareException):
    """Raised when registering or modifying middleware fails."""

    pass


class MiddlewareExecutionException(MiddlewareException):
    """Raised when executing a middleware component fails."""

    pass


class PipelineException(MiddlewareException):
    """Raised when building or validating a middleware pipeline fails."""

    pass


class DuplicateMiddlewareException(MiddlewareRegistrationException):
    """Raised when attempting to register a duplicate middleware component."""

    pass
