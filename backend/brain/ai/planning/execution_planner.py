"""DefaultExecutionPlanner implementation for sequential step ordering (Phase 10.6).

Resolves step dependencies using topological sorting and returns strict sequential step order.
Does not support parallel scheduling.
"""

import logging
from typing import Dict, List

from brain.ai.planning.exceptions import ExecutionPlanningError
from brain.ai.planning.interfaces import ExecutionPlannerInterface
from brain.ai.planning.planning_models import Plan, PlanStep

logger = logging.getLogger(__name__)


class DefaultExecutionPlanner(ExecutionPlannerInterface):
    """Determines sequential step execution order using topological sorting."""

    def determine_execution_order(self, plan: Plan) -> List[PlanStep]:
        """Resolve step dependencies and return topologically sorted sequential step list.

        Args:
            plan: Plan model to resolve.

        Returns:
            List of PlanStep objects in valid sequential execution order.

        Raises:
            ExecutionPlanningError: If dependency resolution encounters cycles or missing steps.
        """
        if not plan.steps:
            return []

        try:
            step_map: Dict[str, PlanStep] = {step.step_id: step for step in plan.steps}
            in_degree: Dict[str, int] = {step.step_id: 0 for step in plan.steps}
            adj_list: Dict[str, List[str]] = {step.step_id: [] for step in plan.steps}

            # Build adjacency list & in-degree map
            # Dependency: Step A depends on Step B => Edge B -> A (B must run before A)
            for step in plan.steps:
                for dep in step.dependencies:
                    dep_id = dep.depends_on_step_id
                    if dep_id not in step_map:
                        raise ExecutionPlanningError(
                            f"Step '{step.step_id}' depends on non-existent step '{dep_id}'."
                        )
                    adj_list[dep_id].append(step.step_id)
                    in_degree[step.step_id] += 1

            # Kahn's Algorithm for Topological Sort
            queue: List[str] = [sid for sid, deg in in_degree.items() if deg == 0]
            # Sort initial queue by original step_number to preserve deterministic ordering
            queue.sort(key=lambda sid: step_map[sid].step_number)

            ordered_steps: List[PlanStep] = []

            while queue:
                current_id = queue.pop(0)
                ordered_steps.append(step_map[current_id])

                for neighbor in adj_list[current_id]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)
                        queue.sort(key=lambda sid: step_map[sid].step_number)

            if len(ordered_steps) != len(plan.steps):
                raise ExecutionPlanningError(
                    f"Dependency resolution failed for plan '{plan.plan_id}'. Cycle or unresolvable dependency detected."
                )

            return ordered_steps

        except Exception as exc:
            if isinstance(exc, ExecutionPlanningError):
                raise
            raise ExecutionPlanningError(f"Failed to determine execution order: {exc}") from exc
