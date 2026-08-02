"""Analytics Runtime for the Auralis Execution Analytics & Observability Runtime (Phase 12.7).

Thread-safe singleton lifecycle manager orchestrating the AnalyticsProvider.
Manages status transitions, metric/trace/audit delegation, health monitoring, and statistics.
"""

from enum import Enum
import logging
import threading
from typing import Any, Dict, List, Optional

from brain.execution.analytics.interfaces import IAnalyticsRuntime
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
from brain.execution.analytics.analytics_provider import AnalyticsProvider

logger = logging.getLogger(__name__)


class AnalyticsRuntimeStatus(str, Enum):
    """Lifecycle status states for the Execution Analytics & Observability Runtime."""

    INITIALIZING = "INITIALIZING"
    READY = "READY"
    RECORDING = "RECORDING"
    DEGRADED = "DEGRADED"
    ERROR = "ERROR"
    SHUTDOWN = "SHUTDOWN"


class AnalyticsRuntime(IAnalyticsRuntime):
    """Thread-safe singleton runtime managing the AnalyticsProvider lifecycle."""

    def __init__(self, provider: Optional[AnalyticsProvider] = None) -> None:
        """Initializes AnalyticsRuntime with optional provider instance."""
        self._lock = threading.RLock()
        self._status = AnalyticsRuntimeStatus.INITIALIZING
        self._provider = provider or AnalyticsProvider()

    @property
    def status(self) -> AnalyticsRuntimeStatus:
        with self._lock:
            return self._status

    @property
    def provider(self) -> AnalyticsProvider:
        return self._provider

    def initialize(self) -> bool:
        """Initialize the Execution Analytics Runtime.

        Returns:
            True if initialized successfully.
        """
        with self._lock:
            if self._status == AnalyticsRuntimeStatus.READY:
                return True

            try:
                self._status = AnalyticsRuntimeStatus.READY
                logger.info("Execution Analytics Runtime Initialized")
                return True
            except Exception as exc:
                self._status = AnalyticsRuntimeStatus.ERROR
                logger.error("AnalyticsRuntime initialization failed: %s", exc)
                return False

    def shutdown(self) -> bool:
        """Gracefully shut down analytics runtime.

        Returns:
            True always.
        """
        with self._lock:
            self._status = AnalyticsRuntimeStatus.SHUTDOWN
            logger.info("Execution Analytics Runtime Shutdown")
            return True

    def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType = MetricType.COUNTER,
        unit: str = "",
        tags: Optional[Dict[str, str]] = None,
    ) -> ExecutionMetric:
        """Record metric through provider."""
        with self._lock:
            if self._status in (AnalyticsRuntimeStatus.INITIALIZING, AnalyticsRuntimeStatus.SHUTDOWN):
                self.initialize()

        return self._provider.record_metric(
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
        """Start trace span through provider."""
        with self._lock:
            if self._status in (AnalyticsRuntimeStatus.INITIALIZING, AnalyticsRuntimeStatus.SHUTDOWN):
                self.initialize()

        return self._provider.start_trace(
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
        """Stop trace span through provider."""
        return self._provider.stop_trace(
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
        """Log audit record through provider."""
        with self._lock:
            if self._status in (AnalyticsRuntimeStatus.INITIALIZING, AnalyticsRuntimeStatus.SHUTDOWN):
                self.initialize()

        return self._provider.log_audit(
            event_type=event_type,
            subsystem=subsystem,
            action=action,
            severity=severity,
            outcome=outcome,
            details=details,
        )

    def get_metrics(self, name_filter: Optional[str] = None) -> List[ExecutionMetric]:
        """Fetch recorded metrics."""
        return self._provider.get_metrics(name_filter=name_filter)

    def get_traces(self, correlation_id_filter: Optional[str] = None) -> List[ExecutionTrace]:
        """Fetch recorded traces."""
        return self._provider.get_traces(correlation_id_filter=correlation_id_filter)

    def get_audit_records(self, subsystem_filter: Optional[str] = None) -> List[ExecutionAuditRecord]:
        """Fetch recorded audit records."""
        return self._provider.get_audit_records(subsystem_filter=subsystem_filter)

    def health_check(self) -> ExecutionHealth:
        """Fetch health check diagnostic status."""
        with self._lock:
            provider_health = self._provider.health_check()
            is_healthy = (self._status in (AnalyticsRuntimeStatus.READY, AnalyticsRuntimeStatus.RECORDING)) and provider_health.healthy

            issues = list(provider_health.detected_issues)
            if self._status == AnalyticsRuntimeStatus.ERROR:
                issues.append("Analytics runtime is in ERROR status")

            return ExecutionHealth(
                status=self._status.value if is_healthy else "ERROR",
                healthy=is_healthy,
                components=provider_health.components,
                statistics=self.get_statistics().model_dump(),
                detected_issues=issues,
                metadata={"thread_safety": "PROTECTED"},
            )

    def get_statistics(self) -> ExecutionStatistics:
        """Fetch analytics execution statistics snapshot."""
        with self._lock:
            return self._provider.get_statistics()

    def clear(self) -> None:
        """Reset analytics statistics and transient state."""
        with self._lock:
            self._provider.clear()
            if self._status != AnalyticsRuntimeStatus.SHUTDOWN:
                self._status = AnalyticsRuntimeStatus.READY
            logger.info("AnalyticsRuntime cleared")
