"""Metrics collector accumulating step duration, success/failure rate, and recovery counts for Auralis."""

from __future__ import annotations

import logging
from .models import ExecutionMetrics


class MetricsCollector:
    """Observes execution outcomes to aggregate performance metrics."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes the MetricsCollector.

        Args:
            logger: Optional custom logger.
        """
        self._logger = logger or logging.getLogger(__name__)
        self._step_durations: list[float] = []
        self._success_count = 0
        self._failure_count = 0
        self._recovery_count = 0
        self._execution_duration = 0.0

    def record_step_result(self, duration: float, success: bool) -> None:
        """Logs the completion duration and status result of an execution step."""
        self._step_durations.append(duration)
        if success:
            self._success_count += 1
        else:
            self._failure_count += 1

    def record_recovery(self) -> None:
        """Increments the recorded self-correction recovery action count."""
        self._recovery_count += 1

    def set_execution_duration(self, duration: float) -> None:
        """Sets total session run duration."""
        self._execution_duration = duration

    def get_metrics(self) -> ExecutionMetrics:
        """Computes and returns the ExecutionMetrics snapshot."""
        total_steps = self._success_count + self._failure_count
        avg_step = sum(self._step_durations) / len(self._step_durations) if self._step_durations else 0.0

        success_rate = (self._success_count / total_steps * 100.0) if total_steps > 0 else 0.0
        failure_rate = (self._failure_count / total_steps * 100.0) if total_steps > 0 else 0.0

        return ExecutionMetrics(
            execution_duration=self._execution_duration,
            average_step_duration=avg_step,
            success_rate=success_rate,
            failure_rate=failure_rate,
            recovery_count=self._recovery_count,
        )
