"""DefaultExecutionMonitor implementation for tracking plan step execution metrics (Phase 10.6).

Tracks step lifecycle across PENDING, RUNNING, COMPLETED, FAILED, and SKIPPED states,
recording timestamps, execution duration, outputs, and failure reasons.
"""

import time
import logging
from datetime import datetime, timezone
from typing import Any, Dict

from brain.ai.planning.exceptions import ExecutionMonitoringError
from brain.ai.planning.interfaces import ExecutionMonitorInterface
from brain.ai.planning.planning_models import ExecutionResult, StepStatus

logger = logging.getLogger(__name__)


class DefaultExecutionMonitor(ExecutionMonitorInterface):
    """Tracks step lifecycle states and metrics."""

    def __init__(self) -> None:
        self._start_times: Dict[str, float] = {}
        self._results: Dict[str, ExecutionResult] = {}

    def track_step_start(self, step_id: str) -> None:
        """Record start of step execution."""
        if not step_id:
            raise ExecutionMonitoringError("step_id cannot be empty.")
        self._start_times[step_id] = time.perf_counter()
        logger.debug(f"Step '{step_id}' started.")

    def track_step_complete(
        self,
        step_id: str,
        output: Any = None,
        duration_ms: float = 0.0,
    ) -> ExecutionResult:
        """Record successful step completion."""
        if not step_id:
            raise ExecutionMonitoringError("step_id cannot be empty.")

        calculated_duration = self._calculate_duration(step_id, duration_ms)

        result = ExecutionResult(
            step_id=step_id,
            status=StepStatus.COMPLETED,
            output=output,
            error_message=None,
            execution_time_ms=calculated_duration,
            timestamp=datetime.now(timezone.utc),
        )
        self._results[step_id] = result
        logger.info(f"Step '{step_id}' completed in {calculated_duration}ms.")
        return result

    def track_step_fail(
        self,
        step_id: str,
        error_message: str,
        duration_ms: float = 0.0,
    ) -> ExecutionResult:
        """Record step execution failure."""
        if not step_id:
            raise ExecutionMonitoringError("step_id cannot be empty.")

        calculated_duration = self._calculate_duration(step_id, duration_ms)

        result = ExecutionResult(
            step_id=step_id,
            status=StepStatus.FAILED,
            output=None,
            error_message=error_message,
            execution_time_ms=calculated_duration,
            timestamp=datetime.now(timezone.utc),
        )
        self._results[step_id] = result
        logger.warning(f"Step '{step_id}' failed: {error_message} ({calculated_duration}ms).")
        return result

    def track_step_skip(self, step_id: str, reason: str = "Dependency failed") -> ExecutionResult:
        """Record skipped step due to upstream failure."""
        result = ExecutionResult(
            step_id=step_id,
            status=StepStatus.SKIPPED,
            output=None,
            error_message=reason,
            execution_time_ms=0.0,
            timestamp=datetime.now(timezone.utc),
        )
        self._results[step_id] = result
        logger.info(f"Step '{step_id}' skipped: {reason}.")
        return result

    def get_execution_summary(self) -> Dict[str, Any]:
        """Retrieve overall execution summary metrics dictionary."""
        total_tracked = len(self._results)
        completed = [r for r in self._results.values() if r.status == StepStatus.COMPLETED]
        failed = [r for r in self._results.values() if r.status == StepStatus.FAILED]
        skipped = [r for r in self._results.values() if r.status == StepStatus.SKIPPED]

        total_duration = sum(r.execution_time_ms for r in self._results.values())

        return {
            "total_steps_tracked": total_tracked,
            "completed_count": len(completed),
            "failed_count": len(failed),
            "skipped_count": len(skipped),
            "total_execution_time_ms": round(total_duration, 2),
            "results": {sid: res.model_dump() for sid, res in self._results.items()},
        }

    def _calculate_duration(self, step_id: str, provided_duration: float) -> float:
        """Calculate duration from start time or return provided_duration."""
        if provided_duration > 0.0:
            return round(provided_duration, 2)

        start_time = self._start_times.pop(step_id, None)
        if start_time is not None:
            return round((time.perf_counter() - start_time) * 1000, 2)

        return 0.0
