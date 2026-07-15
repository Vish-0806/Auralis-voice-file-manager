"""Dynamic task planner implementation for Auralis."""

from __future__ import annotations

import logging
import uuid
from typing import Final

# pyrefly: ignore [missing-import]
from brain.reasoning.models import ReasoningResult
from core.models import ExecutionPlan as CoreExecutionPlan
from core.intents import Intent
from automation.workflow.models import WorkflowDefinition, WorkflowStep
from automation.workflow.workflow_registry import WorkflowRegistry

from .plan_builder import PlanBuilder
from .dependency_resolver import DependencyResolver
from .plan_optimizer import PlanOptimizer


class TaskPlanner:
    """Converts a ReasoningResult into an optimized, executable ExecutionPlan."""

    def __init__(
        self,
        plan_builder: PlanBuilder | None = None,
        dependency_resolver: DependencyResolver | None = None,
        plan_optimizer: PlanOptimizer | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initializes the TaskPlanner.

        Args:
            plan_builder: Dynamic step builder.
            dependency_resolver: Topological sorting resolver.
            plan_optimizer: Deduplication and parallelizer optimizer.
            logger: Optional custom logger for planner diagnostics.
        """
        self._logger = logger or logging.getLogger(__name__)
        self._plan_builder = plan_builder or PlanBuilder(logger=self._logger)
        self._dependency_resolver = dependency_resolver or DependencyResolver(logger=self._logger)
        self._plan_optimizer = plan_optimizer or PlanOptimizer(logger=self._logger)

    def plan(self, reasoning: ReasoningResult, confidence: float = 1.0) -> CoreExecutionPlan:
        """Converts a ReasoningResult into a runnable core ExecutionPlan.

        Args:
            reasoning: The structured reasoning from the Reasoning Engine.
            confidence: Injected confidence rating from Goal Interpretation.

        Returns:
            A core ExecutionPlan ready for the ActionDispatcher.
        """
        self._logger.info("Planning execution steps", extra={"goal_name": reasoning.goal_name})

        raw_sequence = self._plan_builder.build_steps(reasoning)
        ordered_steps = self._dependency_resolver.resolve_order(raw_sequence)
        optimized_steps = self._plan_optimizer.optimize_plan(ordered_steps)

        if not optimized_steps:
            self._logger.warning("Generated execution plan is empty", extra={"goal_name": reasoning.goal_name})
            return CoreExecutionPlan(
                intent=Intent.UNKNOWN,
                confidence=0.0,
            )

        if len(optimized_steps) == 1:
            single_step = optimized_steps[0]
            self._logger.info(
                "Dynamic plan has single step, mapping directly to intent",
                extra={"intent": single_step.intent.value, "target": single_step.target},
            )
            return CoreExecutionPlan(
                intent=single_step.intent,
                target=single_step.target,
                parameters=single_step.parameters,
                confidence=confidence,
            )

        self._logger.info(
            "Dynamic plan has multiple steps, compiling to workflow",
            extra={"steps_count": len(optimized_steps)},
        )

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
            reasoning.goal_name.upper(),
            f"DynamicWorkflow_{uuid.uuid4().hex[:8]}"
        )

        workflow_def = WorkflowDefinition(
            name=workflow_name,
            description=f"Dynamically generated execution workflow for goal: {reasoning.goal_name}",
            steps=wf_steps,
        )

        WorkflowRegistry._dynamic_registry[workflow_name] = workflow_def
        self._logger.debug("Registered dynamic workflow definition", extra={"workflow_name": workflow_name})

        return CoreExecutionPlan(
            intent=Intent.RUN_WORKFLOW,
            target=workflow_name,
            parameters={
                "dynamic_workflow": True,
                "goal_name": reasoning.goal_name,
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
