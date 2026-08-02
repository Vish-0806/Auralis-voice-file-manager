"""Execution Analytics & Observability Runtime package for Auralis (Phase 12.7).

Exports domain models, enums, exceptions, interfaces, metric collector, trace collector,
audit logger, provider, runtime lifecycle manager, and global singleton accessors.
"""

from .analytics_models import (
    AnalyticsContext,
    AnalyticsStatus,
    AuditSeverity,
    ExecutionAuditRecord,
    ExecutionHealth,
    ExecutionMetric,
    ExecutionOutcome,
    ExecutionStatistics,
    ExecutionSummary,
    ExecutionTrace,
    MetricType,
    TraceLevel,
)
from .analytics_provider import AnalyticsProvider
from .analytics_runtime import AnalyticsRuntime, AnalyticsRuntimeStatus
from .audit_logger import AuditLogger

from .exceptions import (
    AnalyticsException,
    AnalyticsStorageError,
    AuditError,
    MetricCollectionError,
    TraceError,
)

from .interfaces import (
    IAnalyticsProvider,
    IAnalyticsRuntime,
    IAuditLogger,
    IMetricCollector,
    ITraceCollector,
)
from .metric_collector import MetricCollector
from .runtime import get_analytics_runtime, reset_analytics_runtime
from .trace_collector import TraceCollector

__all__ = [
    # Enums & Models
    "MetricType",
    "TraceLevel",
    "AuditSeverity",
    "ExecutionOutcome",
    "AnalyticsStatus",
    "ExecutionMetric",
    "ExecutionTrace",
    "ExecutionAuditRecord",
    "ExecutionSummary",
    "ExecutionStatistics",
    "ExecutionHealth",
    "AnalyticsContext",
    # Exceptions
    "AnalyticsException",
    "MetricCollectionError",
    "TraceError",
    "AuditError",
    "AnalyticsStorageError",
    # Interfaces
    "IMetricCollector",
    "ITraceCollector",
    "IAuditLogger",
    "IAnalyticsProvider",
    "IAnalyticsRuntime",
    # Core Components
    "MetricCollector",
    "TraceCollector",
    "AuditLogger",
    "AnalyticsProvider",
    "AnalyticsRuntime",
    "AnalyticsRuntimeStatus",
    # Global Accessors
    "get_analytics_runtime",
    "reset_analytics_runtime",
]
