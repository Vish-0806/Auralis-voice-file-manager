"""Metric Collector for the Auralis Execution Analytics & Observability Runtime (Phase 12.7).

Collects execution metrics: duration, memory usage, CPU time, success/failure rates, retry counts, and queue wait times.
Does not contain execution logic.
"""

from datetime import datetime, timezone
import threading
from typing import Dict, List, Optional

from brain.execution.analytics.interfaces import IMetricCollector
from brain.execution.analytics.analytics_models import ExecutionMetric, MetricType


class MetricCollector(IMetricCollector):
    """Thread-safe metric collector storing counters, gauges, histograms, and timers."""

    def __init__(self) -> None:
        """Initializes MetricCollector."""
        self._lock = threading.RLock()
        self._metrics: List[ExecutionMetric] = []

    def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType = MetricType.COUNTER,
        unit: str = "",
        tags: Optional[Dict[str, str]] = None,
    ) -> ExecutionMetric:
        """Record a metric point.

        Args:
            name: Metric name string.
            value: Numerical metric value.
            metric_type: MetricType enum (COUNTER, GAUGE, HISTOGRAM, TIMER).
            unit: Metric unit string.
            tags: Optional key-value tags dict.

        Returns:
            ExecutionMetric model.
        """
        with self._lock:
            metric = ExecutionMetric(
                name=name,
                metric_type=metric_type,
                value=float(value),
                unit=unit,
                tags=dict(tags or {}),
                timestamp=datetime.now(timezone.utc),
            )
            self._metrics.append(metric)
            return metric

    def get_metrics(self, name_filter: Optional[str] = None) -> List[ExecutionMetric]:
        """Fetch recorded metrics matching optional name filter.

        Args:
            name_filter: Optional substring filter for metric name.

        Returns:
            List of ExecutionMetric objects.
        """
        with self._lock:
            if not name_filter:
                return list(self._metrics)
            filt = name_filter.lower()
            return [m for m in self._metrics if filt in m.name.lower()]

    def count_metrics(self) -> int:
        """Return count of collected metrics."""
        with self._lock:
            return len(self._metrics)

    def clear(self) -> None:
        """Clear recorded metrics."""
        with self._lock:
            self._metrics.clear()
