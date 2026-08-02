"""Exception hierarchy for the Auralis Intent Resolution Subsystem (Phase 12.2).

Defines exception types for intent recognition, resolution, entity extraction, and ambiguity errors.
"""


class IntentException(Exception):
    """Base exception for all Intent Resolution subsystem errors in Auralis."""

    pass


class IntentRecognitionError(IntentException):
    """Raised when intent recognition fails or input text is invalid."""

    pass


class IntentResolutionError(IntentException):
    """Raised when intent resolution or candidate scoring encounters an unrecoverable failure."""

    pass


class EntityExtractionError(IntentException):
    """Raised when entity extraction processing fails."""

    pass


class AmbiguousIntentError(IntentException):
    """Raised when intent ambiguity exceeds resolution threshold requiring clarification."""

    pass
