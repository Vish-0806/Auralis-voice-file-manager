"""DefaultPlanValidator implementation for plan structure and dependency validation (Phase 10.6).

Validates:
- Empty plans
- Duplicate step IDs
- Missing dependencies
- Cyclic dependencies (topological graph cycle detection)
- Invalid/missing tool references in ToolRegistry
"""

import logging
from typing import Any, Dict, List, Optional, Set

from brain.ai.planning.interfaces import PlanValidatorInterface
from brain.ai.planning.planning_models import Plan, PlanStep

logger = logging.getLogger(__name__)


class DefaultPlanValidator(PlanValidatorInterface):
    """Concrete implementation of PlanValidatorInterface."""

    def validate_plan(
        self,
        plan: Plan,
        tool_registry: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Validate plan structure for errors and warnings.

        Args:
            plan: Plan model to validate.
            tool_registry: Optional ToolRegistry instance to check registered tools.

        Returns:
            Dictionary with keys 'is_valid', 'errors', 'warnings'.
        """
        errors: List[str] = []
        warnings: List[str] = []

        # 1. Empty Plan check
        if not plan.steps:
            errors.append(f"Plan '{plan.plan_id}' contains zero steps.")
            return {"is_valid": False, "errors": errors, "warnings": warnings}

        step_ids: Set[str] = set()
        step_map: Dict[str, PlanStep] = {}

        # 2. Duplicate Step IDs check
        for step in plan.steps:
            if step.step_id in step_ids:
                errors.append(f"Duplicate step ID '{step.step_id}' found in plan.")
            else:
                step_ids.add(step.step_id)
                step_map[step.step_id] = step

        # 3. Missing Dependencies & Invalid Tool References check
        for step in plan.steps:
            # Check required tool in registry if provided
            if tool_registry is not None:
                if hasattr(tool_registry, "tool_exists") and not tool_registry.tool_exists(step.required_tool_name):
                    warnings.append(f"Step '{step.step_id}': Tool '{step.required_tool_name}' is not registered in ToolRegistry.")

            # Check dependencies
            for dep in step.dependencies:
                if dep.depends_on_step_id not in step_map:
                    errors.append(
                        f"Step '{step.step_id}' depends on missing step '{dep.depends_on_step_id}'."
                    )

        # 4. Cyclic Dependencies check using Graph Depth-First Search (DFS)
        if not errors:
            cycle_found = self._detect_cycles(plan.steps, step_map)
            if cycle_found:
                errors.append(f"Cyclic dependency detected in plan steps: {cycle_found}")

        is_valid = len(errors) == 0
        return {
            "is_valid": is_valid,
            "errors": errors,
            "warnings": warnings,
        }

    def _detect_cycles(
        self,
        steps: List[PlanStep],
        step_map: Dict[str, PlanStep],
    ) -> Optional[str]:
        """Detect cycles using DFS graph traversal.

        Returns string description of cycle if found, else None.
        """
        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        def dfs(step_id: str, path: List[str]) -> Optional[List[str]]:
            visited.add(step_id)
            rec_stack.add(step_id)

            step = step_map.get(step_id)
            if step:
                for dep in step.dependencies:
                    dep_id = dep.depends_on_step_id
                    if dep_id in step_map:
                        if dep_id not in visited:
                            cycle = dfs(dep_id, path + [dep_id])
                            if cycle:
                                return cycle
                        elif dep_id in rec_stack:
                            return path + [dep_id]

            rec_stack.remove(step_id)
            return None

        for step in steps:
            if step.step_id not in visited:
                cycle_path = dfs(step.step_id, [step.step_id])
                if cycle_path:
                    return " -> ".join(cycle_path)

        return None
