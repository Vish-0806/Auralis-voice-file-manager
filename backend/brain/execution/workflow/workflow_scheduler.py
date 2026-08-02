"""Workflow Scheduler for the Auralis Workflow Execution Engine (Phase 12.4).

Responsible for topological sorting and scheduling step execution order according to dependencies and priority.
"""

from collections import deque
from typing import Dict, List, Set

from brain.execution.workflow.exceptions import WorkflowDependencyError
from brain.execution.workflow.interfaces import IWorkflowScheduler
from brain.execution.workflow.workflow_models import (
    WorkflowExecution,
    WorkflowPriority,
    WorkflowRequest,
    WorkflowStatus,
)

PRIORITY_WEIGHT = {
    WorkflowPriority.CRITICAL: 4,
    WorkflowPriority.HIGH: 3,
    WorkflowPriority.NORMAL: 2,
    WorkflowPriority.LOW: 1,
}


class WorkflowScheduler(IWorkflowScheduler):
    """Scheduler producing executable topological step schedules respecting dependencies and step priority."""

    def schedule(self, request: WorkflowRequest) -> WorkflowExecution:
        """Produce an executable WorkflowExecution schedule ordered by dependencies and priority.

        Args:
            request: WorkflowRequest object.

        Returns:
            WorkflowExecution object.

        Raises:
            WorkflowDependencyError: If scheduling fails due to invalid step dependencies.
        """
        if not request.steps:
            return WorkflowExecution(
                workflow_id=request.request_id,
                status=WorkflowStatus.READY,
                execution_order=[],
            )

        step_map = {step.step_id: step for step in request.steps}
        in_degree: Dict[str, int] = {step.step_id: len(step.dependencies) for step in request.steps}
        graph: Dict[str, List[str]] = {step.step_id: [] for step in request.steps}

        for step in request.steps:
            for dep_id in step.dependencies:
                if dep_id in graph:
                    graph[dep_id].append(step.step_id)

        # Ready queue initialized with in_degree == 0 steps
        ready_steps = [s_id for s_id, deg in in_degree.items() if deg == 0]
        # Sort ready steps by priority descending
        ready_steps.sort(key=lambda s_id: PRIORITY_WEIGHT.get(step_map[s_id].priority, 2), reverse=True)

        queue = deque(ready_steps)
        execution_order: List[str] = []

        while queue:
            curr_id = queue.popleft()
            execution_order.append(curr_id)

            next_ready: List[str] = []
            for neighbor in graph[curr_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    next_ready.append(neighbor)

            # Sort next ready steps by priority descending
            next_ready.sort(key=lambda s_id: PRIORITY_WEIGHT.get(step_map[s_id].priority, 2), reverse=True)
            queue.extend(next_ready)

        if len(execution_order) < len(request.steps):
            raise WorkflowDependencyError("Unresolvable cyclic dependency detected during scheduling")

        return WorkflowExecution(
            workflow_id=request.request_id,
            status=WorkflowStatus.READY,
            execution_order=execution_order,
            metadata={"scheduled_step_count": len(execution_order)},
        )
