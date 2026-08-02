"""Unit test suite for Phase 12.7 — Execution Analytics & Observability Runtime.

Covers:
- Analytics models, enums, defaults, and immutability
- Subsystem exception hierarchy
- MetricCollector counter, gauge, histogram, and timer recording
- TraceCollector span creation, correlation ID tracking, and nested timing
- AuditLogger audit trail record creation and subsystem filtering
- AnalyticsProvider end-to-end aggregation, health reporting, and statistics
- AnalyticsRuntime singleton lifecycle, status management, and thread safety under concurrency
"""

from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from brain.execution.analytics import (
    AnalyticsException,
    AnalyticsProvider,

    AnalyticsRuntime,
    AnalyticsRuntimeStatus,
    AuditLogger,
    AuditSeverity,
    ExecutionAuditRecord,
    ExecutionHealth,
    ExecutionMetric,
    ExecutionOutcome,
    ExecutionStatistics,
    ExecutionTrace,
    MetricCollector,
    MetricType,
    TraceCollector,
    TraceLevel,
    get_analytics_runtime,
    reset_analytics_runtime,
)


@pytest.fixture(autouse=True)
def cleanup_runtime() -> None:
    """Fixture resetting global analytics runtime before and after each test."""
    reset_analytics_runtime()
    yield
    reset_analytics_runtime()


def test_analytics_models_defaults_and_immutability() -> None:
    """Verifies analytics model default properties and Pydantic v2 immutability."""
    metric = ExecutionMetric(name="cpu_usage", value=45.2, metric_type=MetricType.GAUGE, unit="%")
    assert metric.name == "cpu_usage"
    assert metric.value == 45.2

    with pytest.raises((TypeError, ValidationError)):
        metric.value = 50.0  # type: ignore

    trace = ExecutionTrace(span_name="Execute Workflow", duration_ms=120.5)
    assert trace.span_name == "Execute Workflow"
    assert trace.duration_ms == 120.5

    with pytest.raises((TypeError, ValidationError)):
        trace.span_name = "Modified Span"  # type: ignore


def test_analytics_exceptions_hierarchy() -> None:
    """Verifies exception inheritance hierarchy."""
    exc = MetricCollector()
    assert isinstance(AnalyticsException("Test Exception"), Exception)


def test_metric_collector_recording_and_filtering() -> None:
    """Verifies MetricCollector counter and gauge recording and filtering."""
    collector = MetricCollector()
    m1 = collector.record_metric("exec_duration", 150.0, metric_type=MetricType.TIMER, unit="ms")
    m2 = collector.record_metric("memory_used", 512.0, metric_type=MetricType.GAUGE, unit="MB")

    assert m1.name == "exec_duration"
    assert collector.count_metrics() == 2

    dur_metrics = collector.get_metrics("duration")
    assert len(dur_metrics) == 1
    assert dur_metrics[0].name == "exec_duration"


def test_trace_collector_span_creation_and_timing() -> None:
    """Verifies TraceCollector start/stop span timing, correlation IDs, and nested parent spans."""
    collector = TraceCollector()

    span1_id = collector.start_trace("Parent Workflow", correlation_id="c-100")
    span2_id = collector.start_trace("Child Task", correlation_id="c-100", parent_span_id=span1_id)

    trace2 = collector.stop_trace(span2_id, level=TraceLevel.INFO)
    trace1 = collector.stop_trace(span1_id, level=TraceLevel.INFO)

    assert trace2.correlation_id == "c-100"
    assert trace2.parent_span_id == span1_id
    assert trace1.correlation_id == "c-100"
    assert collector.count_traces() == 2

    corr_traces = collector.get_traces("c-100")
    assert len(corr_traces) == 2


def test_audit_logger_event_logging() -> None:
    """Verifies AuditLogger log creation and subsystem filtering."""
    logger_inst = AuditLogger()

    rec1 = logger_inst.log_audit("WORKFLOW", "WorkflowEngine", "Execute Graph", severity=AuditSeverity.HIGH)
    rec2 = logger_inst.log_audit("SECURITY", "SecurityRuntime", "Review Permission", severity=AuditSeverity.CRITICAL)

    assert rec1.subsystem == "WorkflowEngine"
    assert logger_inst.count_records() == 2

    sec_records = logger_inst.get_audit_records("Security")
    assert len(sec_records) == 1
    assert sec_records[0].subsystem == "SecurityRuntime"


def test_analytics_provider_end_to_end_and_health_check() -> None:
    """Verifies AnalyticsProvider metric, trace, and audit log aggregation, health reporting, and statistics."""
    provider = AnalyticsProvider()

    provider.record_metric("step_count", 5.0, metric_type=MetricType.COUNTER)
    span_id = provider.start_trace("Command Step", correlation_id="corr-1")
    provider.stop_trace(span_id)
    provider.log_audit("COMMAND", "Orchestrator", "Dispatched Command", outcome=ExecutionOutcome.SUCCESS)

    health = provider.health_check()
    assert isinstance(health, ExecutionHealth)
    assert health.healthy is True
    assert len(health.components) == 3

    stats = provider.get_statistics()
    assert isinstance(stats, ExecutionStatistics)
    assert stats.total_metrics_collected == 1
    assert stats.total_traces_recorded == 1
    assert stats.total_audit_records == 1
    assert stats.success_rate_percentage == 100.0

    provider.clear()
    assert provider.get_statistics().total_metrics_collected == 0


def test_analytics_runtime_lifecycle_and_singleton() -> None:
    """Verifies AnalyticsRuntime initialization, recording, health reporting, and singleton identity."""
    rt = get_analytics_runtime()
    assert rt.status == AnalyticsRuntimeStatus.READY

    rt2 = get_analytics_runtime()
    assert rt is rt2

    rt.record_metric("test_metric", 10.0)
    rt.log_audit("EVENT", "Subsystem", "Action")

    health = rt.health_check()
    assert health.healthy is True

    stats = rt.get_statistics()
    assert stats.total_metrics_collected == 1
    assert stats.total_audit_records == 1

    rt.clear()
    assert rt.get_statistics().total_metrics_collected == 0

    assert rt.shutdown() is True
    assert rt.status == AnalyticsRuntimeStatus.SHUTDOWN


def test_analytics_runtime_thread_safety() -> None:
    """Verifies thread-safe analytics recording across concurrent worker threads."""
    rt = get_analytics_runtime()

    def worker(i: int) -> str:
        span_id = rt.start_trace(f"Worker Span {i}", correlation_id=f"corr_{i % 3}")
        rt.record_metric(f"metric_{i}", float(i))
        rt.log_audit("WORKER", "WorkerSubsystem", f"Worker Action {i}")
        rt.stop_trace(span_id)
        return span_id

    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(worker, range(15)))

    assert len(results) == 15

    stats = rt.get_statistics()
    assert stats.total_metrics_collected == 15
    assert stats.total_traces_recorded == 15
    assert stats.total_audit_records == 15
