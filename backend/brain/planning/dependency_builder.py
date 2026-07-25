"""Dependency builder module for Auralis."""

from __future__ import annotations

import logging
from brain.reasoning.models import ReasoningResult
from .models import ExecutionDependency, ExecutionStep
from .objective_graph import ObjectiveGraph


class DependencyBuilder:
    """Builds step-to-step dependency relations for planned actions."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes DependencyBuilder.

        Args:
            logger: Optional custom logger.
        """
        self._logger = logger or logging.getLogger(__name__)

    def build_dependencies(
        self, target: ObjectiveGraph | ReasoningResult, steps: list[ExecutionStep]
    ) -> list[ExecutionDependency]:
        """Formulates dependency matrices for execution sequences.

        Args:
            target: The ObjectiveGraph or ReasoningResult source context.
            steps: List of generated execution steps.

        Returns:
            A list of ExecutionDependency mappings.
        """
        if isinstance(target, ReasoningResult):
            self._logger.info("Building dependencies via legacy ReasoningResult path")
            return self._legacy_build_dependencies(target, steps)

        self._logger.info("Building dependencies via ObjectiveGraph path")
        dependencies: list[ExecutionDependency] = []
        for node_id, node in target.nodes.items():
            if node.dependencies:
                dependencies.append(
                    ExecutionDependency(
                        step_id=node_id,
                        depends_on=node.dependencies.copy(),
                    )
                )
        return dependencies

    def _legacy_build_dependencies(
        self, reasoning: ReasoningResult, steps: list[ExecutionStep]
    ) -> list[ExecutionDependency]:
        goal_name = reasoning.goal_name.upper()
        dependencies: list[ExecutionDependency] = []

        # Extract step IDs
        prep_step_ids = [s.step_id for s in steps if s.step_id.startswith("prep_")]
        action_step_ids = [s.step_id for s in steps if s.step_id.startswith("step_")]

        # 1. Map constraints preparation dependencies
        if prep_step_ids:
            for action_id in action_step_ids:
                dependencies.append(
                    ExecutionDependency(
                        step_id=action_id,
                        depends_on=prep_step_ids.copy(),
                    )
                )

        # 2. Add custom sequence dependencies
        if goal_name == "START_CODING":
            dependencies.append(
                ExecutionDependency(
                    step_id="step_launch_terminal",
                    depends_on=["step_launch_vscode"],
                )
            )
            dependencies.append(
                ExecutionDependency(
                    step_id="step_set_volume",
                    depends_on=["step_launch_terminal"],
                )
            )
        elif goal_name == "MEETING":
            dependencies.append(
                ExecutionDependency(
                    step_id="step_show_desktop",
                    depends_on=["step_launch_notepad", "step_mute_sys"],
                )
            )
        elif goal_name == "CLEAN_WORKSPACE":
            dependencies.append(
                ExecutionDependency(
                    step_id="step_show_desktop",
                    depends_on=["step_close_chrome", "step_close_vscode"],
                )
            )

        return dependencies
