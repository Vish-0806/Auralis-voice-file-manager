"""Workflow Builder for the Auralis Workflow Execution Engine (Phase 12.4).

Responsible for constructing structured WorkflowRequest graphs, establishing step dependencies,
assigning priorities, and setting execution modes without performing execution logic.
"""

from typing import Any, Dict, List, Optional

from brain.execution.workflow.exceptions import WorkflowValidationError
from brain.execution.workflow.interfaces import IWorkflowBuilder
from brain.execution.workflow.workflow_models import (
    WorkflowExecutionMode,
    WorkflowPriority,
    WorkflowRequest,
    WorkflowStep,
)


class WorkflowBuilder(IWorkflowBuilder):
    """Builder assembling workflow steps and dependencies into immutable WorkflowRequest models."""

    def build_workflow(
        self,
        name: str,
        steps: List[WorkflowStep],
        context: Optional[Dict[str, Any]] = None,
    ) -> WorkflowRequest:
        """Construct a structured WorkflowRequest without execution logic.

        Args:
            name: Workflow name.
            steps: List of WorkflowStep objects.
            context: Optional contextual metadata dict.

        Returns:
            Populated WorkflowRequest object.

        Raises:
            WorkflowValidationError: If steps is None or empty.
        """
        if steps is None:
            raise WorkflowValidationError("Workflow steps list cannot be None")

        eff_context = dict(context or {})
        mode = WorkflowExecutionMode.SEQUENTIAL
        priority = WorkflowPriority.NORMAL

        # Automatically assign priority if any step is CRITICAL or HIGH
        if any(s.priority == WorkflowPriority.CRITICAL for s in steps):
            priority = WorkflowPriority.CRITICAL
        elif any(s.priority == WorkflowPriority.HIGH for s in steps):
            priority = WorkflowPriority.HIGH

        return WorkflowRequest(
            name=name or "Untitled Workflow",
            description=f"Workflow graph containing {len(steps)} steps",
            steps=list(steps),
            mode=mode,
            priority=priority,
            context=eff_context,
            metadata={"step_count": len(steps)},
        )
