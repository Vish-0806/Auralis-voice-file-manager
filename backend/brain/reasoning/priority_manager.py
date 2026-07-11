"""Priority manager evaluating goal priorities for Auralis."""

from __future__ import annotations

import logging
# pyrefly: ignore [missing-import]
from brain.goal.models import Goal
from .models import Priority


class PriorityManager:
    """Manages and assigns execution priority levels to structured goals."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes the PriorityManager.

        Args:
            logger: Optional custom logger for priority assignment diagnostics.
        """
        self._logger = logger or logging.getLogger(__name__)

    def determine_priority(self, goal: Goal) -> Priority:
        """Determines the Priority of a Goal.

        Args:
            goal: The Goal to evaluate.

        Returns:
            The assigned Priority enum value.
        """
        goal_name = goal.name.upper()

        if goal_name == "LOCK_COMPUTER":
            priority = Priority.CRITICAL
        elif goal_name in ["MEETING", "OPEN_APPLICATION"]:
            priority = Priority.HIGH
        elif goal_name in ["START_CODING", "STUDY"]:
            priority = Priority.MEDIUM
        elif goal_name in ["ORGANIZE_DOWNLOADS", "CLEAN_WORKSPACE"]:
            priority = Priority.LOW
        else:
            priority = Priority.LOW

        self._logger.debug(
            "Assigned priority to goal",
            extra={"goal_name": goal.name, "priority": priority.value},
        )
        return priority
