"""Dependency builder module for Auralis."""

from __future__ import annotations

import logging
from brain.reasoning.models import ReasoningResult
from .models import ExecutionDependency, ExecutionStep


class DependencyBuilder:
    """Builds step-to-step dependency relations for planned actions."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes DependencyBuilder.

        Args:
            logger: Optional custom logger.
        """
        self._logger = logger or logging.getLogger(__name__)

    def build_dependencies(
        self, reasoning: ReasoningResult, steps: list[ExecutionStep]
    ) -> list[ExecutionDependency]:
        """Formulates dependency matrices for execution sequences.

        Args:
            reasoning: ReasoningResult detailing goal types and attributes.
            steps: List of generated execution steps.

        Returns:
            A list of ExecutionDependency mappings.
        """
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

        self._logger.debug(
            "Compiled dependencies",
            extra={"goal_name": goal_name, "dependencies_count": len(dependencies)},
        )
        return dependencies
