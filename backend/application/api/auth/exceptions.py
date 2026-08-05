"""API Authentication & Authorization Exceptions (Phase 15.4).

Defines the exception hierarchy for identity management, authentication failures,
authorization evaluation errors, and session operations.
"""


class AuthenticationException(Exception):
    """Base exception for all authentication and authorization errors."""

    pass


class IdentityException(AuthenticationException):
    """Raised when identity registration or lookup fails."""

    pass


class AuthenticationFailureException(AuthenticationException):
    """Raised when authentication credentials or context validation fails."""

    pass


class AuthorizationException(AuthenticationException):
    """Raised when authorization checks or permission evaluations fail."""

    pass


class SessionException(AuthenticationException):
    """Raised when session creation, lookup, or revocation fails."""

    pass
