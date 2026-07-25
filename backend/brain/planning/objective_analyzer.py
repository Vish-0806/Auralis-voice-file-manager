"""Objective analyzer extracting user objectives from Goal reasoning in Auralis."""

from __future__ import annotations

import logging
from brain.reasoning.models import Objective, ReasoningResult


class ObjectiveAnalyzer:
    """Extracts high-level execution objectives from ReasoningResult structures."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes the ObjectiveAnalyzer.

        Args:
            logger: Optional custom logger for diagnostics.
        """
        self._logger = logger or logging.getLogger(__name__)

    def analyze(self, reasoning: ReasoningResult) -> Objective:
        """Extracts the Objective from a ReasoningResult.

        Args:
            reasoning: The structured reasoning from the Reasoning Engine.

        Returns:
            The structured Objective.
        """
        self._logger.info(
            "Extracting user objective",
            extra={"goal_name": reasoning.goal_name, "objective_title": reasoning.objective.title},
        )
        return reasoning.objective
