"""Abstract Base Class interfaces for the Auralis Execution Analytics & Observability Runtime (Phase 12.7).

Defines canonical interfaces for metric collector, trace collector, audit logger, analytics provider, and runtime.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from brain.execution.analytics.analytics_models import (
    AuditSeverity,
    ExecutionAuditRecord,
    ExecutionHealth,
    ExecutionMetric,
    ExecutionOutcome,
    ExecutionStatistics,
    ExecutionTrace,
    MetricType,
    TraceLevel,
)


class IMetricCollector(ABC):
    """Interface for collecting execution duration, memory, CPU time, success/failure rates, retries, and queue wait times."""

    @abstractmethod
    def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType = MetricType.COUNTER,
        unit: str = "",
        tags: Optional[Dict[str, str]] = None,
    ) -> ExecutionMetric:
        """Record metric value."""
        pass

    @abstractmethod
    def get_metrics(self, name_filter: Optional[str] = None) -> List[ExecutionMetric]:
        """Fetch recorded metrics matching filter."""
        pass


class ITraceCollector(ABC):
    """Interface for managing trace spans, correlation IDs, and nested execution timing."""

    @abstractmethod
    def start_trace(
        self,
        span_name: str,
        correlation_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Start a trace span and return span_id."""
        pass

    @abstractmethod
    def stop_trace(
        self,
        span_id: str,
        level: TraceLevel = TraceLevel.INFO,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> ExecutionTrace:
        """Stop trace span and record ExecutionTrace."""
        pass

    @abstractmethod
    def get_traces(self, correlation_id_filter: Optional[str] = None) -> List[ExecutionTrace]:
        """Fetch recorded traces matching correlation ID filter."""
        pass


class IAuditLogger(ABC):
    """Interface for logging immutable audit records across workflow, task, automation, and security events."""

    @abstractmethod
    def log_audit(
        self,
        event_type: str,
        subsystem: str,
        action: str,
        severity: AuditSeverity = AuditSeverity.MEDIUM,
        outcome: ExecutionOutcome = ExecutionOutcome.SUCCESS,
        details: Optional[Dict[str, Any]] = None,
    ) -> ExecutionAuditRecord:
        """Record an audit trail log entry."""
        pass

    @abstractmethod
    def get_audit_records(self, subsystem_filter: Optional[str] = None) -> List[ExecutionAuditRecord]:
        """Fetch audit records matching subsystem filter."""
        pass


class IAnalyticsProvider(ABC):
    """Interface for aggregate Analytics Provider."""

    @abstractmethod
    def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType = MetricType.COUNTER,
        unit: str = "",
        tags: Optional[Dict[str, str]] = None,
    ) -> ExecutionMetric:
        """Record metric point."""
        pass

    @abstractmethod
    def log_audit(
        self,
        event_type: str,
        subsystem: str,
        action: str,
        severity: AuditSeverity = AuditSeverity.MEDIUM,
        outcome: ExecutionOutcome = ExecutionOutcome.SUCCESS,
        details: Optional[Dict[str, Any]] = None,
    ) -> ExecutionAuditRecord:
        """Record audit log."""
        pass

    @abstractmethod
    def health_check(self) -> ExecutionHealth:
        """Report component health statuses."""
        pass

    @abstractmethod
    def get_statistics(self) -> ExecutionStatistics:
        """Return snapshot of aggregated analytics statistics."""
        pass


class IAnalyticsRuntime(ABC):
    """Interface for the thread-safe singleton lifecycle manager."""

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize analytics runtime lifecycle."""
        pass

    @abstractmethod
    def shutdown(self) -> bool:
        """Gracefully shut down analytics runtime lifecycle."""
        pass

    @abstractmethod
    def health_check(self) -> ExecutionHealth:
        """Fetch real-time health diagnostic status."""
        pass

    @abstractmethod
    def get_statistics(self) -> ExecutionStatistics:
        """Fetch snapshot of analytics execution statistics."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Reset analytics statistics and transient state."""
        pass
