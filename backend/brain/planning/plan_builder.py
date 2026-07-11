"""Plan builder generating execution steps from objectives and constraints."""

from __future__ import annotations

import logging
# pyrefly: ignore [missing-import]
from brain.reasoning.models import ReasoningResult
from core.intents import Intent
from .models import ExecutionStep, ExecutionSequence


class PlanBuilder:
    """Generates execution steps dynamically based on reasoning results."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes the PlanBuilder.

        Args:
            logger: Optional custom logger for plan building diagnostics.
        """
        self._logger = logger or logging.getLogger(__name__)

    def build_steps(self, reasoning: ReasoningResult) -> ExecutionSequence:
        """Generates raw execution steps and dependencies from a ReasoningResult.

        Args:
            reasoning: The structured reasoning result from the Reasoning Engine.

        Returns:
            An ExecutionSequence containing steps and their default dependencies.
        """
        goal_name = reasoning.goal_name.upper()
        objective = reasoning.objective
        steps: list[ExecutionStep] = []

        # 1. Inspect constraints and dynamically inject preparation/remediation steps
        prep_step_ids: list[str] = []
        for constraint in reasoning.constraints:
            if not constraint.satisfied:
                if constraint.type == "internet":
                    step_id = "prep_enable_wifi"
                    steps.append(
                        ExecutionStep(
                            step_id=step_id,
                            intent=Intent.ENABLE_WIFI,
                            can_parallel=False,
                        )
                    )
                    prep_step_ids.append(step_id)
                elif constraint.type == "file_system" and goal_name == "ORGANIZE_DOWNLOADS":
                    step_id = "prep_create_downloads"
                    import os
                    downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
                    steps.append(
                        ExecutionStep(
                            step_id=step_id,
                            intent=Intent.CREATE_FOLDER,
                            target=downloads_path,
                            can_parallel=False,
                        )
                    )
                    prep_step_ids.append(step_id)

        # 2. Map high-level goal to core execution steps
        action_step_ids: list[str] = []
        if goal_name == "START_CODING":
            action_step_ids.append("step_launch_vscode")
            steps.append(
                ExecutionStep(
                    step_id="step_launch_vscode",
                    intent=Intent.OPEN_APPLICATION,
                    target="VS Code",
                )
            )
            action_step_ids.append("step_launch_terminal")
            steps.append(
                ExecutionStep(
                    step_id="step_launch_terminal",
                    intent=Intent.OPEN_APPLICATION,
                    target="Terminal",
                    can_parallel=True,
                )
            )
            action_step_ids.append("step_set_volume")
            steps.append(
                ExecutionStep(
                    step_id="step_set_volume",
                    intent=Intent.SET_VOLUME,
                    target="30",
                    can_parallel=True,
                )
            )
        elif goal_name == "STUDY":
            action_step_ids.append("step_launch_browser")
            steps.append(
                ExecutionStep(
                    step_id="step_launch_browser",
                    intent=Intent.OPEN_APPLICATION,
                    target="Microsoft Edge",
                )
            )
            action_step_ids.append("step_mute_sys")
            steps.append(
                ExecutionStep(
                    step_id="step_mute_sys",
                    intent=Intent.MUTE,
                    can_parallel=True,
                )
            )
        elif goal_name == "MEETING":
            action_step_ids.append("step_launch_notepad")
            steps.append(
                ExecutionStep(
                    step_id="step_launch_notepad",
                    intent=Intent.OPEN_APPLICATION,
                    target="Notepad",
                )
            )
            action_step_ids.append("step_mute_sys")
            steps.append(
                ExecutionStep(
                    step_id="step_mute_sys",
                    intent=Intent.MUTE,
                    can_parallel=True,
                )
            )
            action_step_ids.append("step_show_desktop")
            steps.append(
                ExecutionStep(
                    step_id="step_show_desktop",
                    intent=Intent.SHOW_DESKTOP,
                )
            )
        elif goal_name == "ORGANIZE_DOWNLOADS":
            action_step_ids.append("step_organize_downloads")
            steps.append(
                ExecutionStep(
                    step_id="step_organize_downloads",
                    intent=Intent.ORGANIZE_FOLDER,
                    target="Downloads",
                )
            )
        elif goal_name == "CLEAN_WORKSPACE":
            action_step_ids.append("step_close_chrome")
            steps.append(
                ExecutionStep(
                    step_id="step_close_chrome",
                    intent=Intent.CLOSE_APPLICATION,
                    target="Chrome",
                )
            )
            action_step_ids.append("step_close_vscode")
            steps.append(
                ExecutionStep(
                    step_id="step_close_vscode",
                    intent=Intent.CLOSE_APPLICATION,
                    target="VS Code",
                    can_parallel=True,
                )
            )
            action_step_ids.append("step_show_desktop")
            steps.append(
                ExecutionStep(
                    step_id="step_show_desktop",
                    intent=Intent.SHOW_DESKTOP,
                )
            )
        elif goal_name == "OPEN_APPLICATION":
            app_name = objective.target or "Application"
            action_step_ids.append("step_open_app")
            steps.append(
                ExecutionStep(
                    step_id="step_open_app",
                    intent=Intent.OPEN_APPLICATION,
                    target=app_name,
                )
            )
        elif goal_name == "LOCK_COMPUTER":
            action_step_ids.append("step_lock_pc")
            steps.append(
                ExecutionStep(
                    step_id="step_lock_pc",
                    intent=Intent.LOCK_PC,
                )
            )
        else:
            action_step_ids.append("step_fallback")
            steps.append(
                ExecutionStep(
                    step_id="step_fallback",
                    intent=Intent.UNKNOWN,
                    target=objective.target,
                )
            )

        from .models import ExecutionDependency
        dependencies: list[ExecutionDependency] = []
        if prep_step_ids:
            for action_id in action_step_ids:
                dependencies.append(
                    ExecutionDependency(
                        step_id=action_id,
                        depends_on=prep_step_ids.copy(),
                    )
                )

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
            "Built execution steps",
            extra={"goal_name": goal_name, "steps_count": len(steps)},
        )
        return ExecutionSequence(steps=steps, dependencies=dependencies)
