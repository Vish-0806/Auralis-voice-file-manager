"""Dynamic task planner implementation for Auralis."""

from __future__ import annotations

import logging
from typing import Optional
from memory import AssistantContext

from brain.reasoning.models import ReasoningResult
from core.models import ExecutionPlan as CoreExecutionPlan
from core.intents import Intent

from .models import ExecutionSequence
from .plan_builder import PlanBuilder
from .dependency_resolver import DependencyResolver
from .plan_optimizer import PlanOptimizer
from .objective_analyzer import ObjectiveAnalyzer
from .subtask_generator import SubtaskGenerator
from .dependency_builder import DependencyBuilder
from .workflow_compiler import WorkflowCompiler


class TaskPlanner:
    """Converts a ReasoningResult into an optimized, executable ExecutionPlan.

    Orchestrates the modular planning sequence:
    ObjectiveAnalyzer -> SubtaskGenerator -> DependencyBuilder -> DependencyResolver -> PlanOptimizer -> WorkflowCompiler.
    """

    def __init__(
        self,
        plan_builder: PlanBuilder | None = None,
        dependency_resolver: DependencyResolver | None = None,
        plan_optimizer: PlanOptimizer | None = None,
        objective_analyzer: ObjectiveAnalyzer | None = None,
        subtask_generator: SubtaskGenerator | None = None,
        dependency_builder: DependencyBuilder | None = None,
        workflow_compiler: WorkflowCompiler | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initializes the TaskPlanner.

        Maintains backward compatibility if plan_builder is passed.

        Args:
            plan_builder: Legacy/custom step builder (for backward compatibility).
            dependency_resolver: Topological sorting resolver.
            plan_optimizer: Deduplication and parallelizer optimizer.
            objective_analyzer: Objective analyzer component.
            subtask_generator: Subtask generator component.
            dependency_builder: Dependency builder component.
            workflow_compiler: Workflow compiler component.
            logger: Optional custom logger for planner diagnostics.
        """
        self._logger = logger or logging.getLogger(__name__)

        # Backward compatibility fallback
        self._plan_builder = plan_builder

        self._objective_analyzer = objective_analyzer or ObjectiveAnalyzer(logger=self._logger)
        self._subtask_generator = subtask_generator or SubtaskGenerator(logger=self._logger)
        self._dependency_builder = dependency_builder or DependencyBuilder(logger=self._logger)
        self._dependency_resolver = dependency_resolver or DependencyResolver(logger=self._logger)
        self._plan_optimizer = plan_optimizer or PlanOptimizer(logger=self._logger)
        self._workflow_compiler = workflow_compiler or WorkflowCompiler(logger=self._logger)

    def plan(
        self, reasoning: ReasoningResult, confidence: float = 1.0, context: Optional[AssistantContext] = None
    ) -> CoreExecutionPlan:
        """Converts a ReasoningResult into a runnable core ExecutionPlan.

        Args:
            reasoning: The structured reasoning from the Reasoning Engine.
            confidence: Injected confidence rating from Goal Interpretation.
            context: Optional AssistantContext for retrieval planning.

        Returns:
            A core ExecutionPlan ready for the ActionDispatcher.
        """
        self._logger.info("Planning execution steps", extra={"goal_name": reasoning.goal_name})

        # 1. Objective Analyzer
        _ = self._objective_analyzer.analyze(reasoning)

        # 2 & 3. Generate raw sequence
        if self._plan_builder:
            self._logger.debug("Delegating sequence generation to custom plan_builder fallback")
            raw_sequence = self._plan_builder.build_steps(reasoning)
        else:
            steps = self._subtask_generator.generate_steps(reasoning)
            dependencies = self._dependency_builder.build_dependencies(reasoning, steps)
            raw_sequence = ExecutionSequence(steps=steps, dependencies=dependencies)

        # 4. Dependency Resolver (Topological sort)
        ordered_steps = self._dependency_resolver.resolve_order(raw_sequence)

        # 5. Plan Optimizer
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

        # 6. Workflow Compiler
        self._logger.info(
            "Dynamic plan has multiple steps, compiling to workflow",
            extra={"steps_count": len(optimized_steps)},
        )
        return self._workflow_compiler.compile(optimized_steps, reasoning.goal_name, confidence)
