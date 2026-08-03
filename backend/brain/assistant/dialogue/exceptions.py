"""Dialogue Management Exception Hierarchy (Phase 13.3).

Defines custom exception classes for dialogue state transitions, policy evaluations,
session lookups, and validation errors.
"""


class DialogueException(Exception):
    """Base exception class for all Dialogue Management errors."""

    pass


class DialogueStateError(DialogueException):
    """Raised when an invalid state transition or operation occurs on a dialogue session."""

    pass


class DialoguePolicyError(DialogueException):
    """Raised when a dialogue policy evaluation encounters invalid input or rules."""

    pass


class DialogueValidationError(DialogueException):
    """Raised when invalid dialogue parameters or payload fields are supplied."""

    pass


class DialogueSessionError(DialogueException):
    """Raised when a requested dialogue session cannot be found or manipulated."""

    pass
