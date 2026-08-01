"""Custom exception hierarchy for Security Subsystem (Phase 11.8)."""


class SecurityException(Exception):
    """Base exception for Security Subsystem errors."""

    def __init__(self, message: str, request_id: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.request_id = request_id


class PermissionDeniedError(SecurityException):
    """Raised when an operation is denied due to insufficient permissions."""

    pass


class PolicyViolationError(SecurityException):
    """Raised when an operation violates configured execution policies."""

    pass


class SecurityRiskError(SecurityException):
    """Raised when an operation exceeds maximum acceptable risk limits."""

    pass


class ConfirmationRequiredError(SecurityException):
    """Raised when an operation requires explicit user confirmation before execution."""

    pass
