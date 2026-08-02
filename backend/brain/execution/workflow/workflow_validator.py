"""Workflow Validator for the Auralis Workflow Execution Engine (Phase 12.4).

Validates workflow graph integrity:
- empty workflow check
- duplicate step_id check
- missing dependency target references
- cyclic dependency detection (DFS topological graph cycle detection)
"""

from typing import Dict, List, Set

from brain.execution.workflow.interfaces import IWorkflowValidator
from brain.execution.workflow.workflow_models import WorkflowRequest


class WorkflowValidator(IWorkflowValidator):
    """Validator performing graph validation, cycle detection, and dependency verification."""

    def validate_workflow(self, request: WorkflowRequest) -> List[str]:
        """Validate workflow graph structure for empty steps, duplicate IDs, missing references, and cycles.

        Args:
            request: WorkflowRequest to validate.

        Returns:
            List of diagnostic messages (empty list if valid).
        """
        diagnostics: List[str] = []

        if not request.steps:
            diagnostics.append("Workflow request contains zero steps (empty workflow)")
            return diagnostics

        step_ids: Set[str] = set()
        duplicate_ids: Set[str] = set()

        for step in request.steps:
            if step.step_id in step_ids:
                duplicate_ids.add(step.step_id)
            step_ids.add(step.step_id)

        if duplicate_ids:
            diagnostics.append(f"Duplicate step_id values detected: {sorted(list(duplicate_ids))}")

        # Check missing dependency target references
        missing_refs: List[str] = []
        for step in request.steps:
            for dep_id in step.dependencies:
                if dep_id not in step_ids:
                    missing_refs.append(f"Step '{step.step_id}' references non-existent dependency '{dep_id}'")

        if missing_refs:
            diagnostics.extend(missing_refs)

        # Cycle detection using DFS graph traversal
        adj: Dict[str, List[str]] = {step.step_id: list(step.dependencies) for step in request.steps}
        visited: Dict[str, int] = {s_id: 0 for s_id in step_ids}  # 0=unvisited, 1=visiting, 2=visited
        cycle_found = False

        def dfs(node: str) -> bool:
            nonlocal cycle_found
            visited[node] = 1  # visiting
            for neighbor in adj.get(node, []):
                if neighbor in visited:
                    if visited[neighbor] == 1:
                        cycle_found = True
                        return True
                    elif visited[neighbor] == 0:
                        if dfs(neighbor):
                            return True
            visited[node] = 2  # visited
            return False

        for s_id in step_ids:
            if visited[s_id] == 0:
                if dfs(s_id):
                    diagnostics.append("Cyclic dependency detected in workflow graph")
                    break

        return diagnostics
