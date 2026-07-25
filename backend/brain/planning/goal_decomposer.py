"""Goal decomposer subsystem for Auralis."""

from __future__ import annotations

import logging
from brain.reasoning.models import ReasoningResult
from .objective_graph import ObjectiveGraph
from .decomposition_rules import DecompositionRules
from .decomposition_validator import DecompositionValidator


class GoalDecomposer:
    """Decomposes reasoning goals into ObjectiveGraphs using rule engines."""

    def __init__(
        self,
        rules: DecompositionRules | None = None,
        validator: DecompositionValidator | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initializes GoalDecomposer.

        Args:
            rules: Rules engine mapping goals to sub-objectives.
            validator: Structural cycle and dependency checker.
            logger: Optional custom logger.
        """
        self._logger = logger or logging.getLogger(__name__)
        self._rules = rules or DecompositionRules(logger=self._logger)
        self._validator = validator or DecompositionValidator(logger=self._logger)

    def decompose(self, reasoning: ReasoningResult) -> ObjectiveGraph:
        """Decomposes ReasoningResult into a validated ObjectiveGraph.

        Args:
            reasoning: ReasoningResult input from ReasoningEngine.

        Returns:
            A validated ObjectiveGraph.
        """
        self._logger.info("Decomposing reasoning objectives", extra={"goal_name": reasoning.goal_name})
        graph = self._rules.decompose(reasoning)
        self._validator.validate(graph)
        return graph
