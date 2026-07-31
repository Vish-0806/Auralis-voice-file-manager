"""Multi-Step Planning Engine Exception Hierarchy for Auralis (Phase 10.6).

Defines exception types for goal analysis, plan generation, validation, execution planning,
and execution monitoring.
"""

from brain.ai.exceptions import AIException


class PlanningException(AIException):
    """Base exception for all multi-step planning subsystem errors in Auralis."""

    pass


class GoalAnalysisError(PlanningException):
    """Raised when rule-based goal analysis fails."""

    pass


class PlanGenerationError(PlanningException):
    """Raised when plan generation fails to build a structured Plan."""

    pass


class PlanValidationError(PlanningException):
    """Raised when plan validation identifies invalid structures, cycles, or missing dependencies."""

    def __init__(self, plan_id: str, errors: list):
        self.plan_id = plan_id
        self.errors = errors
        super().__init__(f"Validation failed for Plan '{plan_id}': {'; '.join(errors)}")


class ExecutionPlanningError(PlanningException):
    """Raised when determining sequential step execution order fails."""

    pass


class ExecutionMonitoringError(PlanningException):
    """Raised when tracking execution lifecycle states encounters an error."""

    pass
