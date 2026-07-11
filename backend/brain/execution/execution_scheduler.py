"""Execution scheduler determining the operational queue for Auralis."""

from __future__ import annotations

import logging
from brain.capability.models import CapabilityRoute


class ExecutionScheduler:
    """Schedules step executions sequentially, with hooks for future parallel tracks."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes the ExecutionScheduler.

        Args:
            logger: Optional custom logger for scheduler operations.
        """
        self._logger = logger or logging.getLogger(__name__)

    def schedule_steps(self, routes: list[CapabilityRoute]) -> list[CapabilityRoute]:
        """Orders and schedules execution steps (currently sequential).

        Args:
            routes: The capability routes of the steps.

        Returns:
            An ordered list of capability routes for scheduling.
        """
        self._logger.info("Scheduling execution steps sequentially", extra={"steps_count": len(routes)})
        return routes.copy()
