"""Objective builder mapping goals to high-level user objectives."""

from __future__ import annotations

import logging
# pyrefly: ignore [missing-import]
from brain.goal.models import Goal
from .models import Objective


class ObjectiveBuilder:
    """Translates structured goals into high-level objectives."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes the ObjectiveBuilder.

        Args:
            logger: Optional custom logger for objective construction diagnostics.
        """
        self._logger = logger or logging.getLogger(__name__)

    def build_objective(self, goal: Goal) -> Objective:
        """Translates a Goal into a structured Objective.

        Args:
            goal: The Goal to translate.

        Returns:
            An Objective instance with title, description, and target.
        """
        goal_name = goal.name.upper()
        app_target = goal.parameters.get("application")

        if goal_name == "START_CODING":
            return Objective(
                title="Initialize Development Workspace",
                description="Set up local IDEs, development environments, and activate coding layout.",
                target="VS Code",
            )
        elif goal_name == "STUDY":
            return Objective(
                title="Activate Study Environment",
                description="Open study notes/documents, load educational material, and minimize distractions.",
                target="Study Mode",
            )
        elif goal_name == "MEETING":
            return Objective(
                title="Prepare Meeting Environment",
                description="Open active calendars, check links, and configure video call software.",
                target="Meeting Mode",
            )
        elif goal_name == "ORGANIZE_DOWNLOADS":
            return Objective(
                title="Tidy Downloads Directory",
                description="Examine files inside Downloads and categorize them by file extension types.",
                target="Downloads",
            )
        elif goal_name == "CLEAN_WORKSPACE":
            return Objective(
                title="Tidy Current Desktop Workspace",
                description="Close non-essential application windows and clean temporary cache systems.",
                target="Workspace",
            )
        elif goal_name == "OPEN_APPLICATION":
            app_name = app_target or "Application"
            return Objective(
                title="Launch Application",
                description=f"Request host OS to open the application: '{app_name}'",
                target=app_name,
            )
        elif goal_name == "LOCK_COMPUTER":
            return Objective(
                title="Secure Host Computer Session",
                description="Securely lock the host computer screen and session details.",
                target="PC",
            )

        self._logger.debug("Building default objective for unknown goal", extra={"goal_name": goal.name})
        return Objective(
            title=f"Achieve Objective: {goal.name.title()}",
            description=goal.description or "Process structured goal request.",
            target=str(app_target) if app_target else None,
        )
