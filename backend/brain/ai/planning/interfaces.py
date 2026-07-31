"""Abstract interfaces for Multi-Step Planning Engine (Phase 10.6).

Defines ABCs for:
- GoalAnalyzerInterface
- PlanGeneratorInterface
- PlanValidatorInterface
- ExecutionPlannerInterface
- ExecutionMonitorInterface
- PlannerInterface
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from brain.ai.planning.planning_models import (
    ExecutionResult,
    Plan,
    PlanningGoal,
    PlanStep,
    StepStatus,
)


class GoalAnalyzerInterface(ABC):
    """Abstract interface for rule-based user request goal analysis."""

    @abstractmethod
    def analyze_goal(
        self,
        user_request: str,
        constraints: Optional[Dict[str, Any]] = None,
    ) -> PlanningGoal:
        """Normalize user request and extract goal, constraints, and required capabilities."""
        pass


class PlanGeneratorInterface(ABC):
    """Abstract interface for generating structured execution plans."""

    @abstractmethod
    def generate_plan(self, goal: PlanningGoal) -> Plan:
        """Convert a PlanningGoal into an ordered, step-numbered Plan."""
        pass


class PlanValidatorInterface(ABC):
    """Abstract interface for validating plan structure, step dependencies, and tool references."""

    @abstractmethod
    def validate_plan(
        self,
        plan: Plan,
        tool_registry: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Validate plan structure for cycles, duplicate IDs, missing tools, and empty steps."""
        pass


class ExecutionPlannerInterface(ABC):
    """Abstract interface for determining sequential step execution order."""

    @abstractmethod
    def determine_execution_order(self, plan: Plan) -> List[PlanStep]:
        """Resolve step dependencies and return topologically sorted sequential step order."""
        pass


class ExecutionMonitorInterface(ABC):
    """Abstract interface for tracking step execution lifecycle and recording metrics."""

    @abstractmethod
    def track_step_start(self, step_id: str) -> None:
        """Record start of step execution."""
        pass

    @abstractmethod
    def track_step_complete(
        self,
        step_id: str,
        output: Any = None,
        duration_ms: float = 0.0,
    ) -> ExecutionResult:
        """Record successful step completion."""
        pass

    @abstractmethod
    def track_step_fail(
        self,
        step_id: str,
        error_message: str,
        duration_ms: float = 0.0,
    ) -> ExecutionResult:
        """Record step execution failure."""
        pass

    @abstractmethod
    def get_execution_summary(self) -> Dict[str, Any]:
        """Retrieve overall execution summary metrics dictionary."""
        pass


class PlannerInterface(ABC):
    """Abstract high-level Planner interface coordinating the full planning workflow."""

    @abstractmethod
    def create_and_validate_plan(
        self,
        user_request: str,
        constraints: Optional[Dict[str, Any]] = None,
        tool_registry: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Coordinate analysis, generation, validation, and execution order resolution."""
        pass
