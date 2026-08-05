"""API Protection Exceptions (Phase 15.8).

Defines the exception hierarchy for rate limiting, policy evaluation,
quota enforcement, and violation tracking operations.
"""


class ProtectionException(Exception):
    """Base exception for all API protection runtime errors."""

    pass


class RateLimitException(ProtectionException):
    """Raised when rate limit rule evaluation fails."""

    pass


class PolicyViolationException(ProtectionException):
    """Raised when client evaluation triggers an explicit policy block."""

    pass


class QuotaExceededException(ProtectionException):
    """Raised when a client quota or rate limit is exceeded."""

    pass
