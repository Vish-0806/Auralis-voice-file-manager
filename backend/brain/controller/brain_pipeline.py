"""Modular execution pipeline orchestrating the stages of the Auralis AI Brain."""

from __future__ import annotations

import logging
from typing import Any, Optional
# pyrefly: ignore [missing-import]
from memory import AssistantContext
from brain.goal.goal_interpreter import GoalInterpreter
from brain.reasoning.reasoning_engine import ReasoningEngine
from brain.planning.task_planner import TaskPlanner
from brain.capability.capability_selector import CapabilitySelector
from brain.execution.execution_engine import ExecutionEngine
from core.intents import Intent

from .models import BrainResponse
from .brain_config import BrainConfig


class BrainPipeline:
    """Coordinates each modular stage of the AI Brain pipeline sequentially."""

    def __init__(
        self,
        config: BrainConfig,
        interpreter: GoalInterpreter,
        reasoning_engine: ReasoningEngine,
        planner: TaskPlanner,
        capability_selector: CapabilitySelector,
        execution_engine: ExecutionEngine,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initializes the BrainPipeline.

        Args:
            config: Centralized brain configurations.
            interpreter: Goal Interpreter subsystem.
            reasoning_engine: Reasoning Engine subsystem.
            planner: Dynamic Task Planner subsystem.
            capability_selector: Capability Selector subsystem.
            execution_engine: Multi-Step Execution Engine subsystem.
            logger: Optional custom logger.
        """
        self._logger = logger or logging.getLogger(__name__)
        self._config = config
        self._interpreter = interpreter
        self._reasoning_engine = reasoning_engine
        self._planner = planner
        self._capability_selector = capability_selector
        self._execution_engine = execution_engine

    def execute(self, message: str, dispatcher: Any, context: Optional[AssistantContext] = None) -> BrainResponse:
        """Runs the complete modular execution pipeline.

        Args:
            message: User command message.
            dispatcher: ActionDispatcher instance.
            context: Optional AssistantContext.

        Returns:
            A structured BrainResponse.
        """
        self._logger.info("Executing AI Brain pipeline", extra={"brain_message": message})

        goal_result = self._interpreter.interpret(message, context=context)
        goal_name = goal_result.goal.name

        if (
            goal_result.confidence.score < self._config.confidence_threshold
            or goal_name == "UNKNOWN"
        ):
            self._logger.info(
                "Goal confidence below threshold or UNKNOWN; bypassing dynamic planning pipeline",
                extra={"goal": goal_name, "score": goal_result.confidence.score},
            )
            return BrainResponse(
                success=False,
                message="Goal bypassed: Low confidence or unknown command format.",
                goal_name=goal_name,
            )

        self._logger.info(
            "Goal identified successfully",
            extra={"goal": goal_name, "score": goal_result.confidence.score},
        )

        try:
            reasoning_result = self._reasoning_engine.reason(goal_result.goal, context=context)

            plan = self._planner.plan(reasoning_result, confidence=goal_result.confidence.score, context=context)

            routed_plan = self._capability_selector.select_capabilities(plan)

            summary = self._execution_engine.execute_plan(routed_plan, dispatcher)

            metrics = self._execution_engine._progress_monitor._metrics_collector.get_metrics()

            message_out = (
                "Pipeline completed successfully."
                if summary.success
                else f"Pipeline execution failed: {summary.error}"
            )

            return BrainResponse(
                success=summary.success,
                message=message_out,
                goal_name=goal_name,
                plan=routed_plan,
                summary=summary,
                metrics=metrics,
            )

        except Exception as exc:
            self._logger.exception("AI Brain pipeline encountered execution error")
            return BrainResponse(
                success=False,
                message=f"Pipeline exception: {str(exc)}",
                goal_name=goal_name,
            )
