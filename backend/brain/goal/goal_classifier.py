"""Goal classification logic for Auralis.

This module exposes capabilities to classify goals and raw text queries into
GoalCategory groupings based on registered identifiers and keyword mapping.
"""

from __future__ import annotations

import logging
from typing import Final

from .models import GoalCategory


class GoalClassifier:
    """Classifies goals and text into canonical GoalCategories."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes the GoalClassifier.

        Args:
            logger: Optional custom logger for classification diagnostics.
        """
        self._logger = logger or logging.getLogger(__name__)

    def classify_goal(self, goal_name: str) -> GoalCategory:
        """Categorizes a goal name into its corresponding GoalCategory.

        Args:
            goal_name: The canonical name of the goal (e.g., 'START_CODING').

        Returns:
            The corresponding GoalCategory.
        """
        mapping: Final[dict[str, GoalCategory]] = {
            "START_CODING": GoalCategory.DEVELOPMENT,
            "STUDY": GoalCategory.STUDY,
            "MEETING": GoalCategory.PRODUCTIVITY,
            "ORGANIZE_DOWNLOADS": GoalCategory.FILE_MANAGEMENT,
            "CLEAN_WORKSPACE": GoalCategory.PRODUCTIVITY,
            "OPEN_APPLICATION": GoalCategory.DESKTOP,
            "LOCK_COMPUTER": GoalCategory.SYSTEM_CONTROL,
        }

        category = mapping.get(goal_name.upper(), GoalCategory.GENERAL)
        self._logger.debug(
            "Classified goal name to category",
            extra={"goal_name": goal_name, "category": category.value},
        )
        return category

    def classify_text(self, text: str) -> GoalCategory:
        """Heuristically categorizes a normalized text input into a GoalCategory.

        Args:
            text: The normalized request string.

        Returns:
            The predicted GoalCategory.
        """
        import re

        category_keywords: Final[dict[GoalCategory, list[str]]] = {
            GoalCategory.DEVELOPMENT: ["code", "coding", "program", "programming", "ide", "vscode", "develop", "developer", "developing", "python", "git"],
            GoalCategory.STUDY: ["study", "studying", "learn", "learning", "read", "reading", "book", "books", "lecture", "homework", "course", "courses"],
            GoalCategory.PRODUCTIVITY: ["meeting", "meetings", "call", "calls", "schedule", "scheduling", "calendar", "clean workspace", "tidy", "organize", "organizing"],
            GoalCategory.FILE_MANAGEMENT: ["downloads", "organize", "organizing", "file", "files", "folder", "folders", "directory", "directories", "clean folder"],
            GoalCategory.DESKTOP: ["open app", "launch", "launching", "application", "applications", "window", "windows", "display", "displays"],
            GoalCategory.SYSTEM_CONTROL: ["lock", "locking", "pc", "computer", "computers", "sleep", "shutdown", "restart", "restarting"],
        }

        normalized = text.lower()
        for category, keywords in category_keywords.items():
            for keyword in keywords:
                # Use word boundaries to avoid matching substrings (e.g. "ide" in "inside")
                pattern = rf"\b{re.escape(keyword)}\b"
                if re.search(pattern, normalized):
                    self._logger.debug(
                        "Classified text to category via keyword match",
                        extra={"text": text, "category": category.value},
                    )
                    return category

        return GoalCategory.GENERAL
