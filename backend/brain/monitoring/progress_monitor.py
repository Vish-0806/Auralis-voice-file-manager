"""Progress Monitor orchestrator tracking active plan execution states for Auralis."""

from __future__ import annotations

import logging
import time
from .models import ExecutionEvent, ProgressUpdate, ExecutionProgress, ExecutionMetrics
from .execution_tracker import ExecutionTracker
from .metrics_collector import MetricsCollector
from .event_stream import EventStream


class ProgressMonitor:
    """Orchestrates progress tracking, metrics gathering, and event broadcasting."""

    def __init__(
        self,
        tracker: ExecutionTracker | None = None,
        metrics_collector: MetricsCollector | None = None,
        event_stream: EventStream | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initializes the ProgressMonitor.

        Args:
            tracker: Execution tracker component.
            metrics_collector: Performance statistics component.
            event_stream: Callback publisher stream.
            logger: Optional custom logger.
        """
        self._logger = logger or logging.getLogger(__name__)
        self._tracker = tracker
        self._metrics_collector = metrics_collector or MetricsCollector(logger=self._logger)
        self._event_stream = event_stream or EventStream(logger=self._logger)

    @property
    def event_stream(self) -> EventStream:
        """Returns the registered EventStream instance."""
        return self._event_stream

    def start_session(self, execution_id: str, step_ids: list[str]) -> None:
        """Hooks start execution session event state."""
        self._tracker = ExecutionTracker(execution_id, step_ids, logger=self._logger)
        self._publish_event(ExecutionEvent.ExecutionStarted)

    def start_step(self, step_id: str) -> None:
        """Hooks start of a step execution."""
        if self._tracker:
            self._tracker.start_step(step_id)
        self._publish_event(ExecutionEvent.StepStarted)

    def complete_step(self, step_id: str, duration: float) -> None:
        """Hooks successful completion of a step."""
        if self._tracker:
            self._tracker.complete_step(step_id)
        self._metrics_collector.record_step_result(duration, success=True)
        self._publish_event(ExecutionEvent.StepCompleted)

    def fail_step(self, step_id: str, duration: float) -> None:
        """Hooks step execution failures."""
        if self._tracker:
            self._tracker.complete_step(step_id)
        self._metrics_collector.record_step_result(duration, success=False)
        self._publish_event(ExecutionEvent.StepFailed)

    def start_recovery(self) -> None:
        """Hooks activation of self-correction recovery."""
        self._metrics_collector.record_recovery()
        self._publish_event(ExecutionEvent.RecoveryStarted)

    def finish_recovery(self, success: bool) -> None:
        """Hooks recovery attempt resolutions."""
        self._publish_event(ExecutionEvent.RecoveryFinished)

    def complete_session(self, success: bool, total_duration: float) -> None:
        """Hooks final execution session completions."""
        self._metrics_collector.set_execution_duration(total_duration)
        self._publish_event(ExecutionEvent.ExecutionCompleted)

    def check_stalled(self, step_elapsed: float, threshold_seconds: float = 5.0) -> bool:
        """Detects whether active step execution has stalled based on elapsed times.

        Args:
            step_elapsed: Time spent on current step in seconds.
            threshold_seconds: Timeout tolerance threshold in seconds.

        Returns:
            True if execution has stalled, otherwise False.
        """
        if step_elapsed > threshold_seconds:
            self._logger.warning(
                "Execution stall warning detected on active step",
                extra={"elapsed": step_elapsed, "threshold": threshold_seconds},
            )
            return True
        return False

    def _publish_event(self, event_type: ExecutionEvent) -> None:
        """Assembles progress metrics and broadcasts update envelope packages."""
        progress = (
            self._tracker.get_progress()
            if self._tracker
            else ExecutionProgress(
                execution_id="N/A",
                current_step=None,
                completed_steps=[],
                remaining_steps=[],
            )
        )
        metrics = self._metrics_collector.get_metrics()
        
        update = ProgressUpdate(
            event_type=event_type,
            progress=progress,
            metrics=metrics,
            timestamp=time.time(),
        )
        self._event_stream.publish(update)
