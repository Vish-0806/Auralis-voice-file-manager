"""Execution history logger auditing executed steps for Auralis."""

from __future__ import annotations

import logging
from .models import ExecutionRecord


class ExecutionHistory:
    """Stores a log history of execution records completed during session lifetimes."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes the ExecutionHistory tracker.

        Args:
            logger: Optional custom logger for history diagnostics.
        """
        self._logger = logger or logging.getLogger(__name__)
        self._history: list[ExecutionRecord] = []

    def record_step(self, record: ExecutionRecord) -> None:
        """Saves an execution record to the history log.

        Args:
            record: The step execution record.
        """
        self._history.append(record)
        self._logger.info(
            "Logged step execution to history",
            extra={
                "step_id": record.step_id,
                "intent": record.intent.value,
                "capability": record.capability,
                "status": record.status.value,
                "duration_ms": int(record.duration * 1000),
            },
        )

    def get_history(self) -> list[ExecutionRecord]:
        """Returns all logged step records."""
        return self._history.copy()

    def clear_history(self) -> None:
        """Clears all historical records in this session tracker."""
        self._history.clear()
