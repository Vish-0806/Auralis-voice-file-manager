"""Custom exception hierarchy for Integration Subsystem (Phase 11.9)."""


class IntegrationException(Exception):
    """Base exception for Integration Subsystem errors."""

    def __init__(self, message: str, request_id: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.request_id = request_id


class CapabilityNotFoundError(IntegrationException):
    """Raised when a requested OS capability is not registered or found."""

    pass


class OperationDispatchError(IntegrationException):
    """Raised when an operation cannot be dispatched to the target runtime."""

    pass


class ExecutionPipelineError(IntegrationException):
    """Raised when an error occurs during execution pipeline processing."""

    pass


class OperationValidationError(IntegrationException):
    """Raised when an operation request fails validation criteria."""

    pass
