"""Decision & Reasoning Coordinator Exception Hierarchy (Phase 13.4).

Defines custom exception classes for decision validation, policy routing,
candidate resolution, and runtime errors.
"""


class DecisionException(Exception):
    """Base exception class for all Decision & Reasoning Coordinator errors."""

    pass


class DecisionValidationError(DecisionException):
    """Raised when an invalid DecisionRequest or context payload is provided."""

    pass


class DecisionPolicyError(DecisionException):
    """Raised when policy evaluation encounters invalid rules or conflicting definitions."""

    pass


class DecisionRoutingError(DecisionException):
    """Raised when candidate scoring or routing resolution fails to produce a valid action."""

    pass


class DecisionRuntimeError(DecisionException):
    """Raised when an operational failure occurs in the Reasoning Coordinator runtime."""

    pass
