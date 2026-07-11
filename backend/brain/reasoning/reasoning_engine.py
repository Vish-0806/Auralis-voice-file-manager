"""Reasoning engine converting structured Goals into Reasoning Results."""

from __future__ import annotations

import logging
from typing import Final
# pyrefly: ignore [missing-import]
from brain.goal.models import Goal
from .models import Objective, Constraint, Priority, ReasoningResult
from .objective_builder import ObjectiveBuilder
from .constraint_analyzer import ConstraintAnalyzer
from .priority_manager import PriorityManager


class ReasoningEngine:
    """Orchestrates goal analysis to produce structured reasoning and dependency checks."""

    def __init__(
        self,
        objective_builder: ObjectiveBuilder | None = None,
        constraint_analyzer: ConstraintAnalyzer | None = None,
        priority_manager: PriorityManager | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initializes the ReasoningEngine.

        Args:
            objective_builder: The ObjectiveBuilder helper.
            constraint_analyzer: The ConstraintAnalyzer helper.
            priority_manager: The PriorityManager helper.
            logger: Optional custom logger for diagnostics.
        """
        self._logger = logger or logging.getLogger(__name__)
        self._objective_builder = objective_builder or ObjectiveBuilder(logger=self._logger)
        self._constraint_analyzer = constraint_analyzer or ConstraintAnalyzer(logger=self._logger)
        self._priority_manager = priority_manager or PriorityManager(logger=self._logger)

    def reason(self, goal: Goal) -> ReasoningResult:
        """Converts a structured Goal into a structured ReasoningResult.

        Args:
            goal: The identified User Goal.

        Returns:
            A ReasoningResult populated with objectives, capabilities, constraints, and priorities.
        """
        self._logger.info("Starting reasoning process for goal", extra={"goal_name": goal.name})

        objective = self._objective_builder.build_objective(goal)
        required_capabilities = self._determine_capabilities(goal)
        constraints = self._constraint_analyzer.analyze_constraints(goal)
        priority = self._priority_manager.determine_priority(goal)
        complexity = self._estimate_complexity(goal)

        result = ReasoningResult(
            goal_name=goal.name,
            objective=objective,
            required_capabilities=required_capabilities,
            constraints=constraints,
            priority=priority,
            estimated_complexity=complexity,
        )

        self._logger.info(
            "Reasoning analysis completed",
            extra={
                "goal_name": goal.name,
                "priority": priority.value,
                "complexity": complexity,
                "capabilities": required_capabilities,
            },
        )
        return result

    def _determine_capabilities(self, goal: Goal) -> list[str]:
        """Resolves capability modules required by the goal.

        Args:
            goal: The Goal to check.

        Returns:
            A list of registered capability identifiers.
        """
        goal_name = goal.name.upper()

        mapping: Final[dict[str, list[str]]] = {
            "START_CODING": ["desktop", "workflow"],
            "STUDY": ["desktop", "workflow"],
            "MEETING": ["desktop", "workflow"],
            "ORGANIZE_DOWNLOADS": ["mock_file"],
            "CLEAN_WORKSPACE": ["desktop", "workflow"],
            "OPEN_APPLICATION": ["desktop"],
            "LOCK_COMPUTER": ["desktop"],
        }

        return mapping.get(goal_name, [])

    def _estimate_complexity(self, goal: Goal) -> str:
        """Calculates complexity rating (LOW, MEDIUM, HIGH) for the goal.

        Args:
            goal: The Goal to evaluate.

        Returns:
            A complexity string.
        """
        goal_name = goal.name.upper()

        mapping: Final[dict[str, str]] = {
            "START_CODING": "MEDIUM",
            "STUDY": "MEDIUM",
            "MEETING": "MEDIUM",
            "ORGANIZE_DOWNLOADS": "MEDIUM",
            "CLEAN_WORKSPACE": "MEDIUM",
            "OPEN_APPLICATION": "LOW",
            "LOCK_COMPUTER": "LOW",
        }

        return mapping.get(goal_name, "LOW")
