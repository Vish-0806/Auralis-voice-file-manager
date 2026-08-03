"""Conversation Runtime Exception Hierarchy (Phase 13.2).

Defines custom exception classes for conversation operations, lifecycle states,
validations, lookups, and storage errors.
"""


class ConversationException(Exception):
    """Base exception class for all Conversation Runtime errors."""

    pass


class ConversationNotFoundError(ConversationException):
    """Raised when a requested conversation session cannot be found."""

    pass


class ConversationStateError(ConversationException):
    """Raised when an invalid state transition or operation is attempted on a conversation."""

    pass


class ConversationValidationError(ConversationException):
    """Raised when invalid conversation parameters or message payloads are supplied."""

    pass


class ConversationStorageError(ConversationException):
    """Raised when an error occurs reading or writing conversation data."""

    pass
