"""Proactive Assistant & Notification Exception Hierarchy (Phase 13.8).

Defines custom exception classes for proactive evaluations, recommendations,
notification management, and rule validation errors.
"""


class ProactiveException(Exception):
    """Base exception class for all Proactive Assistant & Notification errors."""

    pass


class ProactiveEvaluationException(ProactiveException):
    """Raised when proactive context evaluation fails."""

    pass


class RecommendationException(ProactiveException):
    """Raised when recommendation generation, scoring, or ranking encounters an error."""

    pass


class NotificationException(ProactiveException):
    """Raised when notification creation, dismissal, or archiving fails."""

    pass


class RuleValidationException(ProactiveException):
    """Raised when an invalid ProactiveRule model or rule definition is provided."""

    pass
