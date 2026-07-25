"""Objective analyzer extracting user objectives from Goal reasoning in Auralis."""

from __future__ import annotations

import logging
from brain.reasoning.models import Objective, ReasoningResult
from .objective_graph import ObjectiveGraph


class ObjectiveAnalyzer:
    """Extracts high-level execution objectives from ReasoningResult or ObjectiveGraph structures."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes the ObjectiveAnalyzer.

        Args:
            logger: Optional custom logger for diagnostics.
        """
        self._logger = logger or logging.getLogger(__name__)

    def analyze(self, target: ObjectiveGraph | ReasoningResult) -> Objective:
        """Extracts the Objective from a ReasoningResult or ObjectiveGraph.

        Args:
            target: The ObjectiveGraph or ReasoningResult source.

        Returns:
            The structured Objective.
        """
        if isinstance(target, ReasoningResult):
            self._logger.info(
                "Extracting user objective from legacy ReasoningResult",
                extra={"goal_name": target.goal_name, "objective_title": target.objective.title},
            )
            return target.objective

        self._logger.info(
            "Extracting user objective from ObjectiveGraph root node",
            extra={"root_id": target.root_id},
        )
        return target.nodes[target.root_id].objective
