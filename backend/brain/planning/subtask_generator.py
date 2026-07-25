"""Subtask generator module for Auralis."""

from __future__ import annotations

import logging
import os
from brain.reasoning.models import ReasoningResult
from core.intents import Intent
from .models import ExecutionStep


class SubtaskGenerator:
    """Converts reasoning results into a list of required ExecutionSteps."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes SubtaskGenerator.

        Args:
            logger: Optional custom logger.
        """
        self._logger = logger or logging.getLogger(__name__)

    def generate_steps(self, reasoning: ReasoningResult) -> list[ExecutionStep]:
        """Converts reasoning results and constraints into execution steps.

        Args:
            reasoning: ReasoningResult structure from the reasoning engine.

        Returns:
            A list of ExecutionStep structures.
        """
        goal_name = reasoning.goal_name.upper()
        objective = reasoning.objective
        steps: list[ExecutionStep] = []

        # 1. Inspect constraints and dynamically inject preparation/remediation steps
        for constraint in reasoning.constraints:
            if not constraint.satisfied:
                if constraint.type == "internet":
                    steps.append(
                        ExecutionStep(
                            step_id="prep_enable_wifi",
                            intent=Intent.ENABLE_WIFI,
                            can_parallel=False,
                        )
                    )
                elif constraint.type == "file_system" and goal_name == "ORGANIZE_DOWNLOADS":
                    downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
                    steps.append(
                        ExecutionStep(
                            step_id="prep_create_downloads",
                            intent=Intent.CREATE_FOLDER,
                            target=downloads_path,
                            can_parallel=False,
                        )
                    )

        # 2. Map high-level goal to core execution steps using modular sub-generators
        if goal_name == "START_CODING":
            steps.extend(self._generate_start_coding())
        elif goal_name == "STUDY":
            steps.extend(self._generate_study())
        elif goal_name == "MEETING":
            steps.extend(self._generate_meeting())
        elif goal_name == "ORGANIZE_DOWNLOADS":
            steps.extend(self._generate_organize_downloads())
        elif goal_name == "CLEAN_WORKSPACE":
            steps.extend(self._generate_clean_workspace())
        elif goal_name == "OPEN_APPLICATION":
            steps.extend(self._generate_open_application(objective.target or "Application"))
        elif goal_name == "LOCK_COMPUTER":
            steps.extend(self._generate_lock_computer())
        else:
            steps.extend(self._generate_fallback(objective.target))

        self._logger.debug(
            "Generated execution steps",
            extra={"goal_name": goal_name, "steps_count": len(steps)},
        )
        return steps

    def _generate_start_coding(self) -> list[ExecutionStep]:
        return [
            ExecutionStep(
                step_id="step_launch_vscode",
                intent=Intent.OPEN_APPLICATION,
                target="VS Code",
            ),
            ExecutionStep(
                step_id="step_launch_terminal",
                intent=Intent.OPEN_APPLICATION,
                target="Terminal",
                can_parallel=True,
            ),
            ExecutionStep(
                step_id="step_set_volume",
                intent=Intent.SET_VOLUME,
                target="30",
                can_parallel=True,
            ),
        ]

    def _generate_study(self) -> list[ExecutionStep]:
        return [
            ExecutionStep(
                step_id="step_launch_browser",
                intent=Intent.OPEN_APPLICATION,
                target="Microsoft Edge",
            ),
            ExecutionStep(
                step_id="step_mute_sys",
                intent=Intent.MUTE,
                can_parallel=True,
            ),
        ]

    def _generate_meeting(self) -> list[ExecutionStep]:
        return [
            ExecutionStep(
                step_id="step_launch_notepad",
                intent=Intent.OPEN_APPLICATION,
                target="Notepad",
            ),
            ExecutionStep(
                step_id="step_mute_sys",
                intent=Intent.MUTE,
                can_parallel=True,
            ),
            ExecutionStep(
                step_id="step_show_desktop",
                intent=Intent.SHOW_DESKTOP,
            ),
        ]

    def _generate_organize_downloads(self) -> list[ExecutionStep]:
        return [
            ExecutionStep(
                step_id="step_organize_downloads",
                intent=Intent.ORGANIZE_FOLDER,
                target="Downloads",
            )
        ]

    def _generate_clean_workspace(self) -> list[ExecutionStep]:
        return [
            ExecutionStep(
                step_id="step_close_chrome",
                intent=Intent.CLOSE_APPLICATION,
                target="Chrome",
            ),
            ExecutionStep(
                step_id="step_close_vscode",
                intent=Intent.CLOSE_APPLICATION,
                target="VS Code",
                can_parallel=True,
            ),
            ExecutionStep(
                step_id="step_show_desktop",
                intent=Intent.SHOW_DESKTOP,
            ),
        ]

    def _generate_open_application(self, app_name: str) -> list[ExecutionStep]:
        return [
            ExecutionStep(
                step_id="step_open_app",
                intent=Intent.OPEN_APPLICATION,
                target=app_name,
            )
        ]

    def _generate_lock_computer(self) -> list[ExecutionStep]:
        return [
            ExecutionStep(
                step_id="step_lock_pc",
                intent=Intent.LOCK_PC,
            )
        ]

    def _generate_fallback(self, target: str | None) -> list[ExecutionStep]:
        return [
            ExecutionStep(
                step_id="step_fallback",
                intent=Intent.UNKNOWN,
                target=target,
            )
        ]
