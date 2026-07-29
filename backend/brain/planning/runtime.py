"""Planning Runtime Coordinator for orchestrating the complete planning subsystem.

This module provides thread-safe runtime orchestration of ActionPlanner, PlanValidator,
DependencyResolver, RiskAnalyzer, and ExecutionPlanBuilder without executing actions,
calling LLMs, accessing memory providers, or interacting with the operating system.
"""

from datetime import datetime, timezone
from enum import Enum
import logging
import threading
import time
from typing import Any, Dict, List, Optional

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field

from brain.planning.action_planner import ActionPlan, ActionPlanner
from brain.planning.dependency_resolver import DependencyResolutionResult, DependencyResolver
from brain.planning.execution_plan_builder import ExecutionPlan, ExecutionPlanBuilder
from brain.planning.plan_validator import PlanValidationResult, PlanValidator
from brain.planning.risk_analyzer import RiskAnalysisResult, RiskAnalyzer
from brain.reasoning.context_builder import ReasoningContext

logger = logging.getLogger(__name__)


class PlanningRuntimeStatus(str, Enum):
    """Enumeration of planning runtime lifecycle status states."""

    INITIALIZING = "INITIALIZING"
    READY = "READY"
    DEGRADED = "DEGRADED"
    SHUTDOWN = "SHUTDOWN"
    ERROR = "ERROR"


class PlanningRuntimeStats(BaseModel):
    """Immutable model representing planning runtime diagnostic statistics."""

    model_config = ConfigDict(frozen=True)

    plans_processed: int = 0
    plans_built: int = 0
    average_runtime_ms: float = 0.0
    last_request_timestamp: Optional[datetime] = None
    startup_timestamp: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PlanningRuntimeHealth(BaseModel):
    """Immutable model representing planning runtime health status."""

    model_config = ConfigDict(frozen=True)

    status: PlanningRuntimeStatus = PlanningRuntimeStatus.READY
    healthy: bool = True
    components: Dict[str, bool] = Field(default_factory=dict)
    statistics: Dict[str, Any] = Field(default_factory=dict)
    issues: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PlanningRuntimeCoordinator:
    """Singleton runtime coordinator orchestrating the 5-stage planning pipeline."""

    def __init__(
        self,
        action_planner: Optional[ActionPlanner] = None,
        plan_validator: Optional[PlanValidator] = None,
        dependency_resolver: Optional[DependencyResolver] = None,
        risk_analyzer: Optional[RiskAnalyzer] = None,
        execution_plan_builder: Optional[ExecutionPlanBuilder] = None,
    ) -> None:
        """Initializes the coordinator with optional component instances."""
        self._lock = threading.RLock()
        self._status = PlanningRuntimeStatus.INITIALIZING
        self._startup_timestamp: Optional[datetime] = None

        self._action_planner = action_planner or ActionPlanner()
        self._plan_validator = plan_validator or PlanValidator()
        self._dependency_resolver = dependency_resolver or DependencyResolver()
        self._risk_analyzer = risk_analyzer or RiskAnalyzer()
        self._execution_plan_builder = execution_plan_builder or ExecutionPlanBuilder()

        self._plans_processed = 0
        self._plans_built = 0
        self._total_runtime_ms = 0.0
        self._last_request_timestamp: Optional[datetime] = None

    @property
    def action_planner(self) -> ActionPlanner:
        return self._action_planner

    @property
    def plan_validator(self) -> PlanValidator:
        return self._plan_validator

    @property
    def dependency_resolver(self) -> DependencyResolver:
        return self._dependency_resolver

    @property
    def risk_analyzer(self) -> RiskAnalyzer:
        return self._risk_analyzer

    @property
    def execution_plan_builder(self) -> ExecutionPlanBuilder:
        return self._execution_plan_builder

    @property
    def status(self) -> PlanningRuntimeStatus:
        with self._lock:
            return self._status

    def initialize(self) -> bool:
        """Initializes all planning components and transitions status to READY."""
        with self._lock:
            if self._status == PlanningRuntimeStatus.READY:
                return True

            self._startup_timestamp = datetime.now(timezone.utc)
            self._status = PlanningRuntimeStatus.READY
            logger.info("Runtime Initialized")
            return True

    def shutdown(self) -> bool:
        """Shuts down the planning runtime safely."""
        with self._lock:
            if self._status == PlanningRuntimeStatus.SHUTDOWN:
                return True

            self._status = PlanningRuntimeStatus.SHUTDOWN
            logger.info("Runtime Shutdown")
            return True

    def clear(self) -> None:
        """Resets runtime statistics and clears component caches while preserving configuration."""
        with self._lock:
            self._plans_processed = 0
            self._plans_built = 0
            self._total_runtime_ms = 0.0
            self._last_request_timestamp = None
            logger.info("Runtime Cleared")

    def process_reasoning_context(
        self, reasoning_context: Optional[ReasoningContext] = None
    ) -> ExecutionPlan:
        """Executes the 5-stage deterministic planning pipeline for a reasoning context."""
        start_time = time.perf_counter()
        with self._lock:
            if self._status == PlanningRuntimeStatus.SHUTDOWN:
                self.initialize()

            # 1. Action Planning
            action_plan = self._action_planner.create_plan(reasoning_context)

            # 2. Plan Validation
            validation_result = self._plan_validator.validate_plan(action_plan)

            # 3. Dependency Resolution
            dependency_result = self._dependency_resolver.resolve_dependencies(action_plan)

            # 4. Risk Analysis
            risk_result = self._risk_analyzer.analyze_risks(action_plan, validation_result, dependency_result)

            # 5. Execution Plan Building
            execution_plan = self._execution_plan_builder.build_execution_plan(
                action_plan, validation_result, dependency_result, risk_result
            )

            # Update stats
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            self._plans_processed += 1
            self._plans_built += 1
            self._total_runtime_ms += elapsed_ms
            self._last_request_timestamp = datetime.now(timezone.utc)

            logger.info("Planning Request Processed")
            return execution_plan

    def health_check(self) -> PlanningRuntimeHealth:
        """Generates real-time health diagnostic status report."""
        with self._lock:
            components_status = {
                "ActionPlanner": self._action_planner is not None,
                "PlanValidator": self._plan_validator is not None,
                "DependencyResolver": self._dependency_resolver is not None,
                "RiskAnalyzer": self._risk_analyzer is not None,
                "ExecutionPlanBuilder": self._execution_plan_builder is not None,
            }
            all_available = all(components_status.values())
            is_healthy = (self._status == PlanningRuntimeStatus.READY) and all_available

            issues = []
            if not all_available:
                issues.append("One or more planning components are unavailable")
            if self._status != PlanningRuntimeStatus.READY:
                issues.append(f"Runtime status is {self._status.value}")

            health = PlanningRuntimeHealth(
                status=self._status,
                healthy=is_healthy,
                components=components_status,
                statistics=self.get_statistics().model_dump(),
                issues=issues,
                metadata={"thread_safety": "PROTECTED"},
            )
            logger.info("Health Check")
            return health

    def get_statistics(self) -> PlanningRuntimeStats:
        """Retrieves runtime statistics snapshot."""
        with self._lock:
            avg_ms = (self._total_runtime_ms / self._plans_processed) if self._plans_processed > 0 else 0.0
            return PlanningRuntimeStats(
                plans_processed=self._plans_processed,
                plans_built=self._plans_built,
                average_runtime_ms=avg_ms,
                last_request_timestamp=self._last_request_timestamp,
                startup_timestamp=self._startup_timestamp,
                metadata={},
            )

    def list_components(self) -> List[str]:
        """Lists registered planning components."""
        return [
            "ActionPlanner",
            "PlanValidator",
            "DependencyResolver",
            "RiskAnalyzer",
            "ExecutionPlanBuilder",
        ]


_global_lock = threading.RLock()
_global_planning_runtime: Optional[PlanningRuntimeCoordinator] = None


def get_planning_runtime(
    action_planner: Optional[ActionPlanner] = None,
    plan_validator: Optional[PlanValidator] = None,
    dependency_resolver: Optional[DependencyResolver] = None,
    risk_analyzer: Optional[RiskAnalyzer] = None,
    execution_plan_builder: Optional[ExecutionPlanBuilder] = None,
    reset: bool = False,
) -> PlanningRuntimeCoordinator:
    """Singleton accessor for the global PlanningRuntimeCoordinator instance."""
    global _global_planning_runtime
    with _global_lock:
        if reset or _global_planning_runtime is None:
            _global_planning_runtime = PlanningRuntimeCoordinator(
                action_planner=action_planner,
                plan_validator=plan_validator,
                dependency_resolver=dependency_resolver,
                risk_analyzer=risk_analyzer,
                execution_plan_builder=execution_plan_builder,
            )
            _global_planning_runtime.initialize()
        return _global_planning_runtime


def reset_planning_runtime() -> None:
    """Resets the global PlanningRuntimeCoordinator instance."""
    global _global_planning_runtime
    with _global_lock:
        if _global_planning_runtime is not None:
            _global_planning_runtime.shutdown()
            _global_planning_runtime.clear()
            _global_planning_runtime = None
