"""Assistant Memory & Context Integration Exception Hierarchy (Phase 13.5).

Defines custom exception classes for context retrieval, context merge, preference processing,
and memory validation errors.
"""


class AssistantMemoryException(Exception):
    """Base exception class for all Assistant Memory & Context Integration errors."""

    pass


class AssistantMemoryRetrievalError(AssistantMemoryException):
    """Raised when memory context cannot be retrieved from a subsystem."""

    pass


class AssistantContextMergeError(AssistantMemoryException):
    """Raised when context variables or scoped units fail to merge cleanly."""

    pass


class AssistantPreferenceError(AssistantMemoryException):
    """Raised when user, assistant, or runtime preference validation or merge fails."""

    pass


class AssistantMemoryValidationError(AssistantMemoryException):
    """Raised when invalid memory context models or invalid parameters are supplied."""

    pass
