"""Assistant Runtime Integration Layer Exception Hierarchy (Phase 13.9).

Defines custom exception classes for integration gateway pipeline execution,
routing, runtime synchronization, and validation errors.
"""


class AssistantIntegrationException(Exception):
    """Base exception class for all Assistant Runtime Integration errors."""

    pass


class AssistantPipelineException(AssistantIntegrationException):
    """Raised when pipeline stage execution or stage transition fails."""

    pass


class AssistantRoutingException(AssistantIntegrationException):
    """Raised when request routing between sub-runtimes fails."""

    pass


class AssistantSynchronizationException(AssistantIntegrationException):
    """Raised when runtime lifecycle synchronization or state consistency check fails."""

    pass


class AssistantValidationException(AssistantIntegrationException):
    """Raised when invalid parameters or integration models are provided."""

    pass
