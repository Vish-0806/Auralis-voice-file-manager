"""AIPlanner high-level service coordinating multi-step planning (Phase 10.6).

Coordinates:
GoalAnalyzer → PlanGenerator → PlanValidator → ExecutionPlanner → ExecutionMonitor
Uses dependency injection throughout.
"""

import logging
from typing import Any, Dict, List, Optional

from brain.ai.planning.exceptions import PlanningException
from brain.ai.planning.interfaces import (
    ExecutionMonitorInterface,
    ExecutionPlannerInterface,
    GoalAnalyzerInterface,
    PlanGeneratorInterface,
    PlannerInterface,
    PlanValidatorInterface,
)
from brain.ai.planning.goal_analyzer import DefaultGoalAnalyzer
from brain.ai.planning.plan_generator import DefaultPlanGenerator
from brain.ai.planning.plan_validator import DefaultPlanValidator
from brain.ai.planning.execution_planner import DefaultExecutionPlanner
from brain.ai.planning.execution_monitor import DefaultExecutionMonitor
from brain.ai.planning.planning_models import Plan, PlanningGoal, PlanStatus, PlanStep

logger = logging.getLogger(__name__)


class AIPlanner(PlannerInterface):
    """High-level Multi-Step Planning Engine service."""

    def __init__(
        self,
        goal_analyzer: Optional[GoalAnalyzerInterface] = None,
        plan_generator: Optional[PlanGeneratorInterface] = None,
        plan_validator: Optional[PlanValidatorInterface] = None,
        execution_planner: Optional[ExecutionPlannerInterface] = None,
        execution_monitor: Optional[ExecutionMonitorInterface] = None,
    ) -> None:
        self.goal_analyzer = goal_analyzer or DefaultGoalAnalyzer()
        self.plan_generator = plan_generator or DefaultPlanGenerator()
        self.plan_validator = plan_validator or DefaultPlanValidator()
        self.execution_planner = execution_planner or DefaultExecutionPlanner()
        self.execution_monitor = execution_monitor or DefaultExecutionMonitor()

    def create_and_validate_plan(
        self,
        user_request: str,
        constraints: Optional[Dict[str, Any]] = None,
        tool_registry: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Execute full planning pipeline: Analyze Goal -> Generate Plan -> Validate -> Determine Order.

        Args:
            user_request: Raw user prompt string.
            constraints: Optional dictionary of constraint parameters.
            tool_registry: Optional ToolRegistry instance to validate tool existence.

        Returns:
            Dictionary containing 'goal', 'plan', 'validation', 'ordered_steps', and 'is_valid'.

        Raises:
            PlanningException: If any pipeline stage encounters an unrecoverable failure.
        """
        try:
            # 1. Goal Analysis
            goal: PlanningGoal = self.goal_analyzer.analyze_goal(user_request, constraints=constraints)

            # 2. Plan Generation
            raw_plan: Plan = self.plan_generator.generate_plan(goal)

            # 3. Plan Validation
            validation_res: Dict[str, Any] = self.plan_validator.validate_plan(raw_plan, tool_registry=tool_registry)

            if not validation_res["is_valid"]:
                logger.warning(f"Plan validation failed: {validation_res['errors']}")

            # 4. Resolve Execution Order if valid
            ordered_steps: List[PlanStep] = []
            if validation_res["is_valid"]:
                ordered_steps = self.execution_planner.determine_execution_order(raw_plan)
                # Create validated plan instance with VALIDATED status
                plan = Plan(
                    plan_id=raw_plan.plan_id,
                    goal_id=raw_plan.goal_id,
                    steps=raw_plan.steps,
                    status=PlanStatus.VALIDATED,
                    created_at=raw_plan.created_at,
                    metadata={**raw_plan.metadata, "validated": True},
                )
            else:
                plan = raw_plan

            return {
                "goal": goal,
                "plan": plan,
                "validation": validation_res,
                "ordered_steps": ordered_steps,
                "is_valid": validation_res["is_valid"],
            }

        except Exception as exc:
            if isinstance(exc, PlanningException):
                raise
            raise PlanningException(f"AIPlanner pipeline failed: {exc}") from exc
