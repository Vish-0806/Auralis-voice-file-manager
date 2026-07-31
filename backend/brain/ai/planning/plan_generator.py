"""DefaultPlanGenerator implementation for building structured execution plans (Phase 10.6).

Converts a PlanningGoal into an ordered, step-numbered Plan model containing tool references,
step dependencies, arguments, and expected output descriptions.
"""

import uuid
import logging
from typing import Any, Dict, List, Optional

from brain.ai.planning.exceptions import PlanGenerationError
from brain.ai.planning.interfaces import PlanGeneratorInterface
from brain.ai.planning.planning_models import (
    Plan,
    PlanningGoal,
    PlanStatus,
    PlanStep,
    StepDependency,
    StepStatus,
)

logger = logging.getLogger(__name__)


class DefaultPlanGenerator(PlanGeneratorInterface):
    """Deterministic, template-driven PlanGenerator implementation."""

    def generate_plan(self, goal: PlanningGoal) -> Plan:
        """Convert a PlanningGoal into a structured Plan.

        Args:
            goal: Analyzed PlanningGoal instance.

        Returns:
            Plan model with populated steps and dependencies.

        Raises:
            PlanGenerationError: If plan generation fails.
        """
        try:
            plan_id = f"plan-{uuid.uuid4().hex[:8]}"
            steps: List[PlanStep] = []

            capabilities = goal.required_capabilities or ["filesystem"]
            read_only = goal.constraints.get("read_only", False)

            # Generate step pipeline based on primary capabilities
            if "filesystem" in capabilities and "organize" in goal.normalized_goal.lower():
                steps = self._build_file_organization_steps(goal, read_only)
            elif "memory" in capabilities:
                steps = self._build_memory_steps(goal)
            else:
                steps = self._build_generic_steps(goal, capabilities)

            return Plan(
                plan_id=plan_id,
                goal_id=goal.goal_id,
                steps=steps,
                status=PlanStatus.DRAFT,
                metadata={
                    "generator": "DefaultPlanGenerator",
                    "step_count": len(steps),
                    "read_only": read_only,
                },
            )

        except Exception as exc:
            raise PlanGenerationError(f"Failed to generate plan for goal '{goal.goal_id}': {exc}") from exc

    def _build_file_organization_steps(
        self,
        goal: PlanningGoal,
        read_only: bool,
    ) -> List[PlanStep]:
        """Build sequential steps for file organization workflows."""
        step1_id = "step-1-scan"
        step2_id = "step-2-organize"

        step1 = PlanStep(
            step_id=step1_id,
            step_number=1,
            description="Scan target directory for unorganized files",
            required_tool_name="list_directory",
            arguments={"path": goal.constraints.get("directory", "/workspace")},
            dependencies=[],
            expected_output_description="List of files to organize",
            status=StepStatus.PENDING,
        )

        step2_tool = "preview_file_move" if read_only else "move_file"
        step2_dep = StepDependency(step_id=step2_id, depends_on_step_id=step1_id)

        step2 = PlanStep(
            step_id=step2_id,
            step_number=2,
            description=f"Execute file moves to category subfolders ({step2_tool})",
            required_tool_name=step2_tool,
            arguments={"read_only": read_only},
            dependencies=[step2_dep],
            expected_output_description="Execution summary of moved files",
            status=StepStatus.PENDING,
        )

        return [step1, step2]

    def _build_memory_steps(self, goal: PlanningGoal) -> List[PlanStep]:
        """Build steps for memory operations."""
        step1_id = "step-1-query-mem"

        step1 = PlanStep(
            step_id=step1_id,
            step_number=1,
            description="Query memory context for user preferences",
            required_tool_name="store_memory",
            arguments={"query": goal.normalized_goal},
            dependencies=[],
            expected_output_description="Retrieved memory context items",
            status=StepStatus.PENDING,
        )

        return [step1]

    def _build_generic_steps(
        self,
        goal: PlanningGoal,
        capabilities: List[str],
    ) -> List[PlanStep]:
        """Build fallback sequential steps."""
        primary_cap = capabilities[0] if capabilities else "filesystem"
        tool_name = f"read_{primary_cap}" if "read" in goal.normalized_goal.lower() else f"execute_{primary_cap}"

        step1 = PlanStep(
            step_id="step-1-exec",
            step_number=1,
            description=f"Execute step for goal: {goal.normalized_goal[:50]}",
            required_tool_name=tool_name,
            arguments={"query": goal.raw_text},
            dependencies=[],
            expected_output_description="Step completion output",
            status=StepStatus.PENDING,
        )

        return [step1]
