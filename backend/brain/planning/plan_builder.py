"""Plan builder generating execution steps from objectives and constraints.

This class is maintained for backward compatibility. It delegates internally to
SubtaskGenerator and DependencyBuilder.
"""

from __future__ import annotations

import logging
from brain.reasoning.models import ReasoningResult
from .models import ExecutionSequence
from .subtask_generator import SubtaskGenerator
from .dependency_builder import DependencyBuilder


class PlanBuilder:
    """Generates execution steps dynamically based on reasoning results.

    Delegates internally to SubtaskGenerator and DependencyBuilder to satisfy
    existing system dependencies and tests.
    """

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes the PlanBuilder.

        Args:
            logger: Optional custom logger for plan building diagnostics.
        """
        self._logger = logger or logging.getLogger(__name__)
        self._subtask_generator = SubtaskGenerator(logger=self._logger)
        self._dependency_builder = DependencyBuilder(logger=self._logger)

    def build_steps(self, reasoning: ReasoningResult) -> ExecutionSequence:
        """Generates raw execution steps and dependencies from a ReasoningResult.

        Args:
            reasoning: The structured reasoning result from the Reasoning Engine.

        Returns:
            An ExecutionSequence containing steps and their default dependencies.
        """
        self._logger.info("Delegating build_steps to SubtaskGenerator and DependencyBuilder")
        steps = self._subtask_generator.generate_steps(reasoning)
        dependencies = self._dependency_builder.build_dependencies(reasoning, steps)
        return ExecutionSequence(steps=steps, dependencies=dependencies)
