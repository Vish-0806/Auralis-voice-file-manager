"""Exception hierarchy for the Auralis Automation & Scheduling Runtime (Phase 12.6).

Defines exception types for trigger evaluation, scheduling, execution, and persistence errors.
"""


class AutomationException(Exception):
    """Base exception for all Automation & Scheduling Runtime subsystem errors in Auralis."""

    pass


class AutomationTriggerError(AutomationException):
    """Raised when trigger evaluation or matching fails."""

    pass


class AutomationScheduleError(AutomationException):
    """Raised when schedule parsing or next run calculation fails."""

    pass


class AutomationExecutionError(AutomationException):
    """Raised when automation rule execution fails unrecoverably."""

    pass


class AutomationPersistenceError(AutomationException):
    """Raised when saving or querying automation history fails."""

    pass
