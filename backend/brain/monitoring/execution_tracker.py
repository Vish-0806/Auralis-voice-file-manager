"""Observational execution progress tracker for Auralis."""

from __future__ import annotations

import logging
import time
from .models import ExecutionProgress


class ExecutionTracker:
    """Calculates and reports step progress metrics during an execution session."""

    def __init__(self, execution_id: str, total_steps: list[str], logger: logging.Logger | None = None) -> None:
        """Initializes the ExecutionTracker.

        Args:
            execution_id: Unique execution identifier.
            total_steps: Ordered list of all planned step IDs.
            logger: Optional custom logger.
        """
        self._logger = logger or logging.getLogger(__name__)
        self._execution_id = execution_id
        self._total_steps = total_steps.copy()
        self._completed_steps: list[str] = []
        self._remaining_steps = total_steps.copy()
        self._current_step: str | None = None
        self._start_time = time.perf_counter()

    def start_step(self, step_id: str) -> None:
        """Updates tracker state when a step starts.

        Args:
            step_id: The ID of the step starting.
        """
        self._current_step = step_id
        if step_id in self._remaining_steps:
            self._remaining_steps.remove(step_id)

    def complete_step(self, step_id: str) -> None:
        """Marks a step completed.

        Args:
            step_id: The ID of the step completed.
        """
        self._current_step = None
        if step_id not in self._completed_steps:
            self._completed_steps.append(step_id)
        if step_id in self._remaining_steps:
            self._remaining_steps.remove(step_id)

    def get_progress(self) -> ExecutionProgress:
        """Computes and returns the ExecutionProgress metrics."""
        elapsed = time.perf_counter() - self._start_time
        total_count = len(self._total_steps)
        completed_count = len(self._completed_steps)
        remaining_count = len(self._remaining_steps)

        percent = (completed_count / total_count * 100.0) if total_count > 0 else 0.0

        est_remaining = 0.0
        if completed_count > 0:
            avg_duration = elapsed / completed_count
            est_remaining = remaining_count * avg_duration
        else:
            est_remaining = remaining_count * 1.0

        return ExecutionProgress(
            execution_id=self._execution_id,
            current_step=self._current_step,
            completed_steps=self._completed_steps.copy(),
            remaining_steps=self._remaining_steps.copy(),
            elapsed_time=elapsed,
            estimated_remaining_time=est_remaining,
            percent_complete=percent,
        )
