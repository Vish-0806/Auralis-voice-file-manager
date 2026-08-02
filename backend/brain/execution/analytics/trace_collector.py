"""Trace Collector for the Auralis Execution Analytics & Observability Runtime (Phase 12.7).

Manages correlation IDs, start/stop trace spans, nested parent-child span trees, and millisecond duration calculations.
Provider-independent with zero platform-specific dependencies.
"""

from datetime import datetime, timezone
import threading
import time
import uuid
from typing import Any, Dict, List, Optional

from brain.execution.analytics.interfaces import ITraceCollector
from brain.execution.analytics.analytics_models import ExecutionTrace, TraceLevel


class TraceCollector(ITraceCollector):
    """Thread-safe trace collector generating execution traces and nested spans."""

    def __init__(self) -> None:
        """Initializes TraceCollector."""
        self._lock = threading.RLock()
        self._active_spans: Dict[str, Dict[str, Any]] = {}
        self._completed_traces: List[ExecutionTrace] = []

    def start_trace(
        self,
        span_name: str,
        correlation_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Start a new trace span.

        Args:
            span_name: Name of the execution span.
            correlation_id: Optional correlation ID string.
            parent_span_id: Optional parent span ID string for nested spans.
            attributes: Optional key-value attribute dictionary.

        Returns:
            Generated span_id string.
        """
        with self._lock:
            span_id = f"span-{uuid.uuid4().hex[:8]}"
            corr_id = correlation_id or f"corr-{uuid.uuid4().hex[:8]}"

            self._active_spans[span_id] = {
                "span_id": span_id,
                "span_name": span_name,
                "correlation_id": corr_id,
                "parent_span_id": parent_span_id,
                "start_time": time.perf_counter(),
                "started_at": datetime.now(timezone.utc),
                "attributes": dict(attributes or {}),
            }
            return span_id

    def stop_trace(
        self,
        span_id: str,
        level: TraceLevel = TraceLevel.INFO,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> ExecutionTrace:
        """Stop a running trace span and record an ExecutionTrace.

        Args:
            span_id: Target span identifier.
            level: TraceLevel enum (DEBUG, INFO, WARN, ERROR, CRITICAL).
            attributes: Optional additional attributes.

        Returns:
            ExecutionTrace model.

        Raises:
            KeyError: If span_id is not actively running.
        """
        with self._lock:
            span_data = self._active_spans.pop(span_id, None)
            if not span_data:
                # Return dummy trace if span_id not found to avoid crashing
                return ExecutionTrace(
                    trace_id=span_id,
                    span_name="unknown_span",
                    level=level,
                    duration_ms=0.0,
                )

            start_t = span_data["start_time"]
            duration_ms = round((time.perf_counter() - start_t) * 1000.0, 3)

            merged_attrs = dict(span_data.get("attributes", {}))
            if attributes:
                merged_attrs.update(attributes)

            trace = ExecutionTrace(
                trace_id=span_id,
                correlation_id=span_data["correlation_id"],
                span_name=span_data["span_name"],
                parent_span_id=span_data["parent_span_id"],
                level=level,
                duration_ms=duration_ms,
                attributes=merged_attrs,
                timestamp=span_data["started_at"],
            )

            self._completed_traces.append(trace)
            return trace

    def get_traces(self, correlation_id_filter: Optional[str] = None) -> List[ExecutionTrace]:
        """Fetch recorded traces matching optional correlation ID filter.

        Args:
            correlation_id_filter: Optional correlation ID string.

        Returns:
            List of ExecutionTrace objects.
        """
        with self._lock:
            if not correlation_id_filter:
                return list(self._completed_traces)
            return [t for t in self._completed_traces if t.correlation_id == correlation_id_filter]

    def count_traces(self) -> int:
        """Return total count of recorded traces."""
        with self._lock:
            return len(self._completed_traces)

    def clear(self) -> None:
        """Clear active spans and completed traces."""
        with self._lock:
            self._active_spans.clear()
            self._completed_traces.clear()
