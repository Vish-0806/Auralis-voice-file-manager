"""Workflow compiler compiling optimized steps into workflow definitions in Auralis."""

from __future__ import annotations

import logging
import uuid
from typing import Final
from automation.workflow.models import WorkflowDefinition, WorkflowStep
from automation.workflow.workflow_registry import WorkflowRegistry
from core.models import ExecutionPlan as CoreExecutionPlan
from core.intents import Intent
from .models import ExecutionStep


class WorkflowCompiler:
    """Compiles optimized step sequences into runnable workflow actions."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes WorkflowCompiler.

        Args:
            logger: Optional custom logger.
        """
        self._logger = logger or logging.getLogger(__name__)

    def compile(
        self, optimized_steps: list[ExecutionStep], goal_name: str, confidence: float = 1.0
    ) -> CoreExecutionPlan:
        """Compiles step sequences and registers dynamic workflow definitions.

        Args:
            optimized_steps: Deduplicated list of execution steps.
            goal_name: User Goal identifier.
            confidence: Goal classification confidence score.

        Returns:
            A CoreExecutionPlan representing the workflow invocation.
        """
        wf_steps = [
            WorkflowStep(
                intent=step.intent,
                target=step.target,
                parameters=step.parameters,
            )
            for step in optimized_steps
        ]

        # Use canonical workflow name if it maps to a default built-in workflow
        goal_to_workflow_name: Final[dict[str, str]] = {
            "START_CODING": "Start Coding",
            "STUDY": "Study Mode",
            "MEETING": "Meeting Mode",
            "CLEAN_WORKSPACE": "Clean Workspace",
        }
        workflow_name = goal_to_workflow_name.get(
            goal_name.upper(),
            f"DynamicWorkflow_{uuid.uuid4().hex[:8]}"
        )

        workflow_def = WorkflowDefinition(
            name=workflow_name,
            description=f"Dynamically generated execution workflow for goal: {goal_name}",
            steps=wf_steps,
        )

        WorkflowRegistry._dynamic_registry[workflow_name] = workflow_def
        self._logger.debug(
            "Registered dynamic workflow definition during compilation",
            extra={"workflow_name": workflow_name},
        )

        return CoreExecutionPlan(
            intent=Intent.RUN_WORKFLOW,
            target=workflow_name,
            parameters={
                "dynamic_workflow": True,
                "goal_name": goal_name,
                "original_steps": [
                    {
                        "step_id": s.step_id,
                        "intent": s.intent.value,
                        "target": s.target,
                        "parameters": s.parameters,
                    }
                    for s in optimized_steps
                ],
            },
            confidence=confidence,
        )
