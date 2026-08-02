"""Analytics Provider for the Auralis Execution Analytics & Observability Runtime (Phase 12.7).

Aggregates MetricCollector, TraceCollector, and AuditLogger into a unified, thread-safe gateway provider.
"""

from datetime import datetime, timezone
import logging
import threading
from typing import Any, Dict, List, Optional

from brain.execution.analytics.interfaces import (
    IAuditLogger,
    IAnalyticsProvider,
    IMetricCollector,
    ITraceCollector,
)
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
from brain.execution.analytics.audit_logger import AuditLogger
from brain.execution.analytics.metric_collector import MetricCollector
from brain.execution.analytics.trace_collector import TraceCollector

logger = logging.getLogger(__name__)


class AnalyticsProvider(IAnalyticsProvider):
    """Thread-safe provider aggregating metric collector, trace collector, and audit logger."""

    def __init__(
        self,
        metric_collector: Optional[IMetricCollector] = None,
        trace_collector: Optional[ITraceCollector] = None,
        audit_logger: Optional[IAuditLogger] = None,
    ) -> None:
        """Initializes AnalyticsProvider with injected or default components."""
        self._lock = threading.RLock()
        self._metric_collector = metric_collector or MetricCollector()
        self._trace_collector = trace_collector or TraceCollector()
        self._audit_logger = audit_logger or AuditLogger()

    def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType = MetricType.COUNTER,
        unit: str = "",
        tags: Optional[Dict[str, str]] = None,
    ) -> ExecutionMetric:
        """Record metric value."""
        return self._metric_collector.record_metric(
            name=name,
            value=value,
            metric_type=metric_type,
            unit=unit,
            tags=tags,
        )

    def start_trace(
        self,
        span_name: str,
        correlation_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Start a new trace span."""
        return self._trace_collector.start_trace(
            span_name=span_name,
            correlation_id=correlation_id,
            parent_span_id=parent_span_id,
            attributes=attributes,
        )

    def stop_trace(
        self,
        span_id: str,
        level: TraceLevel = TraceLevel.INFO,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> ExecutionTrace:
        """Stop running trace span."""
        return self._trace_collector.stop_trace(
            span_id=span_id,
            level=level,
            attributes=attributes,
        )

    def log_audit(
        self,
        event_type: str,
        subsystem: str,
        action: str,
        severity: AuditSeverity = AuditSeverity.MEDIUM,
        outcome: ExecutionOutcome = ExecutionOutcome.SUCCESS,
        details: Optional[Dict[str, Any]] = None,
    ) -> ExecutionAuditRecord:
        """Log audit record."""
        return self._audit_logger.log_audit(
            event_type=event_type,
            subsystem=subsystem,
            action=action,
            severity=severity,
            outcome=outcome,
            details=details,
        )

    def get_metrics(self, name_filter: Optional[str] = None) -> List[ExecutionMetric]:
        """Get metrics matching name filter."""
        return self._metric_collector.get_metrics(name_filter=name_filter)

    def get_traces(self, correlation_id_filter: Optional[str] = None) -> List[ExecutionTrace]:
        """Get traces matching correlation ID filter."""
        return self._trace_collector.get_traces(correlation_id_filter=correlation_id_filter)

    def get_audit_records(self, subsystem_filter: Optional[str] = None) -> List[ExecutionAuditRecord]:
        """Get audit records matching subsystem filter."""
        return self._audit_logger.get_audit_records(subsystem_filter=subsystem_filter)

    def health_check(self) -> ExecutionHealth:
        """Report component health statuses."""
        with self._lock:
            registered = {
                "MetricCollector": self._metric_collector is not None,
                "TraceCollector": self._trace_collector is not None,
                "AuditLogger": self._audit_logger is not None,
            }
            all_ok = all(registered.values())

            return ExecutionHealth(
                status="READY" if all_ok else "ERROR",
                healthy=all_ok,
                components=registered,
                statistics=self.get_statistics().model_dump(),
                detected_issues=[] if all_ok else ["One or more analytics sub-components are unavailable"],
                metadata={"thread_safety": "PROTECTED"},
            )

    def get_statistics(self) -> ExecutionStatistics:
        """Return snapshot of aggregated analytics statistics."""
        with self._lock:
            m_count = getattr(self._metric_collector, "count_metrics", lambda: len(self.get_metrics()))()
            t_count = getattr(self._trace_collector, "count_traces", lambda: len(self.get_traces()))()
            a_count = getattr(self._audit_logger, "count_records", lambda: len(self.get_audit_records()))()

            traces = self.get_traces()
            avg_duration = (sum(t.duration_ms for t in traces) / len(traces)) if traces else 0.0

            audits = self.get_audit_records()
            successes = sum(1 for a in audits if a.outcome == ExecutionOutcome.SUCCESS)
            succ_rate = round((successes / len(audits)) * 100.0, 2) if audits else 100.0

            return ExecutionStatistics(
                total_metrics_collected=m_count,
                total_traces_recorded=t_count,
                total_audit_records=a_count,
                average_execution_time_ms=round(avg_duration, 2),
                success_rate_percentage=succ_rate,
                metadata={"thread_safety": "PROTECTED"},
            )

    def clear(self) -> None:
        """Clear all analytics components."""
        with self._lock:
            if hasattr(self._metric_collector, "clear"):
                self._metric_collector.clear()
            if hasattr(self._trace_collector, "clear"):
                self._trace_collector.clear()
            if hasattr(self._audit_logger, "clear"):
                self._audit_logger.clear()
