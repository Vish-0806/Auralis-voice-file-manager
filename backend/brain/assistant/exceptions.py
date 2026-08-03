"""Assistant Runtime Exception Hierarchy (Phase 13.1).

Defines the custom exception hierarchy for Assistant Runtime initialization, configuration,
session management, and execution errors.
"""


class AssistantException(Exception):
    """Base exception class for all Assistant Runtime errors."""

    pass


class AssistantInitializationError(AssistantException):
    """Raised when the Assistant Runtime fails to initialize cleanly."""

    pass


class AssistantRuntimeError(AssistantException):
    """Raised when an error occurs during runtime execution or service operations."""

    pass


class AssistantConfigurationError(AssistantException):
    """Raised when invalid or incompatible configuration settings are supplied."""

    pass


class AssistantSessionError(AssistantException):
    """Raised when an invalid session operation is performed."""

    pass
