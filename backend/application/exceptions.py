"""Application Layer Exceptions (Phase 14.1).

Defines the exception hierarchy for application bootstrap, runtime lifecycle,
subsystem registration, initialization, startup validation, and shutdown errors.
"""


class ApplicationException(Exception):
    """Base exception for all application layer errors."""

    pass


class ApplicationBootstrapError(ApplicationException):
    """Raised when application bootstrapping fails."""

    pass


class RuntimeRegistrationError(ApplicationException):
    """Raised when registering or unregistering a sub-runtime fails."""

    pass


class InitializationError(ApplicationException):
    """Raised when subsystem initialization fails."""

    pass


class StartupValidationError(ApplicationException):
    """Raised when pre-startup verification checks fail."""

    pass


class ApplicationShutdownError(ApplicationException):
    """Raised when application shutdown operations fail."""

    pass
