"""API Versioning Exceptions (Phase 15.6).

Defines the exception hierarchy for version registration, compatibility evaluation,
documentation management, and deprecation operations.
"""


class VersioningException(Exception):
    """Base exception for all API versioning runtime errors."""

    pass


class VersionRegistrationException(VersioningException):
    """Raised when registering or looking up an API version fails."""

    pass


class CompatibilityException(VersioningException):
    """Raised when version compatibility evaluation fails."""

    pass


class DocumentationException(VersioningException):
    """Raised when documentation page management or export fails."""

    pass


class DeprecationException(VersioningException):
    """Raised when deprecation processing fails."""

    pass
