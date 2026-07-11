"""Registry of supported system goals in Auralis.

This module acts as a store for all registered goals and provides default goals
such as START_CODING, STUDY, MEETING, ORGANIZE_DOWNLOADS, CLEAN_WORKSPACE,
OPEN_APPLICATION, and LOCK_COMPUTER.
"""

from __future__ import annotations

import logging
from typing import Final

from .models import Goal, GoalCategory


class GoalRegistry:
    """Maintains the supported system goals and provides lookup capabilities."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes the GoalRegistry with default supported goals.

        Args:
            logger: Optional custom logger for registry diagnostics.
        """
        self._logger = logger or logging.getLogger(__name__)
        self._goals: dict[str, Goal] = {}
        self._register_default_goals()

    def register_goal(self, goal: Goal) -> None:
        """Registers a new goal in the registry.

        Args:
            goal: The Goal definition to register.
        """
        name_upper = goal.name.upper()
        self._goals[name_upper] = goal
        self._logger.debug(
            "Registered new goal",
            extra={"goal_name": goal.name, "category": goal.category.value},
        )

    def get_goal(self, name: str) -> Goal | None:
        """Retrieves a registered goal by name.

        Args:
            name: The canonical name of the goal.

        Returns:
            The Goal object if found, otherwise None.
        """
        return self._goals.get(name.upper())

    def list_goals(self) -> list[Goal]:
        """Returns all registered goals.

        Returns:
            A list of all registered Goal objects.
        """
        return list(self._goals.values())

    def _register_default_goals(self) -> None:
        """Registers default goals requested by the system specification."""
        defaults: Final[list[Goal]] = [
            Goal(
                name="START_CODING",
                category=GoalCategory.DEVELOPMENT,
                description="Initialize development environment, launch editor and project workspace.",
            ),
            Goal(
                name="STUDY",
                category=GoalCategory.STUDY,
                description="Activate study session mode, load reference materials, and minimize distractions.",
            ),
            Goal(
                name="MEETING",
                category=GoalCategory.PRODUCTIVITY,
                description="Prepare workspace for a meeting or video call.",
            ),
            Goal(
                name="ORGANIZE_DOWNLOADS",
                category=GoalCategory.FILE_MANAGEMENT,
                description="Automatically clean, sort, and organize files in the Downloads directory.",
            ),
            Goal(
                name="CLEAN_WORKSPACE",
                category=GoalCategory.PRODUCTIVITY,
                description="Close unnecessary applications and perform lightweight workspace tidy-up.",
            ),
            Goal(
                name="OPEN_APPLICATION",
                category=GoalCategory.DESKTOP,
                description="Launch a specified desktop application.",
            ),
            Goal(
                name="LOCK_COMPUTER",
                category=GoalCategory.SYSTEM_CONTROL,
                description="Securely lock the host computer session.",
            ),
            Goal(
                name="UNKNOWN",
                category=GoalCategory.GENERAL,
                description="An unrecognized or unclassified user goal.",
            ),
        ]

        for goal in defaults:
            self.register_goal(goal)
