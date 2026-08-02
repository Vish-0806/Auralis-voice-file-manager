"""Exception hierarchy for the Auralis Execution Analytics & Observability Runtime (Phase 12.7).

Defines exception types for metric collection, trace recording, audit logging, and analytics storage.
"""


class AnalyticsException(Exception):
    """Base exception for all Execution Analytics subsystem errors in Auralis."""

    pass


class MetricCollectionError(AnalyticsException):
    """Raised when metric collection encounters an error."""

    pass


class TraceError(AnalyticsException):
    """Raised when span tracing or correlation tracking encounters an error."""

    pass


class AuditError(AnalyticsException):
    """Raised when audit record creation or logging encounters an error."""

    pass


class AnalyticsStorageError(AnalyticsException):
    """Raised when analytics persistence or snapshot querying fails."""

    pass
