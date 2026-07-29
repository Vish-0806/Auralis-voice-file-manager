"""Execution Plan Builder for combining all planning outputs into a single immutable ExecutionPlan.

This module provides thread-safe execution plan creation without executing actions, modifying input objects,
calling LLMs, accessing memory providers, or interacting with the operating system.
"""

from datetime import datetime, timezone
from enum import Enum
import logging
import threading
from typing import Any, Callable, Dict, List, Optional

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field

from brain.planning.action_planner import ActionPlan
from brain.planning.dependency_resolver import DependencyResolutionResult, DependencyStatus
from brain.planning.plan_validator import PlanValidationResult
from brain.planning.risk_analyzer import RiskAnalysisResult, RiskLevel

logger = logging.getLogger(__name__)


class ExecutionReadiness(str, Enum):
    """Enumeration of execution readiness states."""

    READY = "READY"
    READY_WITH_WARNINGS = "READY_WITH_WARNINGS"
    NOT_READY = "NOT_READY"
    BLOCKED = "BLOCKED"


class ExecutionStage(str, Enum):
    """Enumeration of execution pipeline stages."""

    PLANNING = "PLANNING"
    VALIDATION = "VALIDATION"
    DEPENDENCY_RESOLUTION = "DEPENDENCY_RESOLUTION"
    RISK_ANALYSIS = "RISK_ANALYSIS"
    READY_FOR_EXECUTION = "READY_FOR_EXECUTION"


class ExecutionPlan(BaseModel):
    """Immutable model representing the combined outcome of multi-stage task planning."""

    model_config = ConfigDict(frozen=True)

    request: str = ""
    action_plan: ActionPlan = Field(default_factory=ActionPlan)
    validation_result: PlanValidationResult = Field(default_factory=PlanValidationResult)
    dependency_result: DependencyResolutionResult = Field(default_factory=DependencyResolutionResult)
    risk_result: RiskAnalysisResult = Field(default_factory=RiskAnalysisResult)
    execution_order: List[int] = Field(default_factory=list)
    readiness: ExecutionReadiness = ExecutionReadiness.READY
    current_stage: ExecutionStage = ExecutionStage.READY_FOR_EXECUTION
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExecutionPlanBuilderConfig(BaseModel):
    """Configuration options for ExecutionPlanBuilder behavior."""

    strict_build: bool = True
    include_metadata: bool = True
    include_diagnostics: bool = True


class ExecutionPlanBuilder:
    """Thread-safe engine for building immutable ExecutionPlan objects."""

    def __init__(self, config: Optional[ExecutionPlanBuilderConfig] = None) -> None:
        """Initializes the ExecutionPlanBuilder with optional configuration and thread lock."""
        self.config = config or ExecutionPlanBuilderConfig()
        self._builder_hooks: List[Dict[str, Any]] = []
        self._lock = threading.RLock()

    def register_builder_hook(
        self,
        hook_id: str,
        hook_func: Callable[[Dict[str, Any]], Dict[str, Any]],
        priority: int = 10,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Registers a builder metadata transformation hook."""
        with self._lock:
            self._builder_hooks = [h for h in self._builder_hooks if h["hook_id"] != hook_id]
            entry = {
                "hook_id": hook_id,
                "hook_func": hook_func,
                "priority": priority,
                "metadata": metadata or {},
            }
            self._builder_hooks.append(entry)
            logger.info("Builder Hook Registered: hook_id=%s", hook_id)
            return True

    def remove_builder_hook(self, hook_id: str) -> bool:
        """Removes a registered builder hook by hook_id."""
        with self._lock:
            initial_count = len(self._builder_hooks)
            self._builder_hooks = [h for h in self._builder_hooks if h["hook_id"] != hook_id]
            removed = len(self._builder_hooks) < initial_count

            if removed:
                logger.info("Builder Hook Removed: hook_id=%s", hook_id)
                return True
            return False

    def clear_builder_hooks(self) -> None:
        """Clears all builder hooks from the registry."""
        with self._lock:
            self._builder_hooks.clear()
            logger.info("Builder Hooks Cleared")

    def build_execution_plan(
        self,
        action_plan: Optional[ActionPlan] = None,
        validation_result: Optional[PlanValidationResult] = None,
        dependency_result: Optional[DependencyResolutionResult] = None,
        risk_result: Optional[RiskAnalysisResult] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExecutionPlan:
        """Constructs an immutable ExecutionPlan combining all planning stage outputs."""
        with self._lock:
            plan_val = action_plan if isinstance(action_plan, ActionPlan) else ActionPlan()
            val_val = validation_result if isinstance(validation_result, PlanValidationResult) else PlanValidationResult(valid=True)
            dep_val = dependency_result if isinstance(dependency_result, DependencyResolutionResult) else DependencyResolutionResult(resolved=True, status=DependencyStatus.RESOLVED)
            risk_val = risk_result if isinstance(risk_result, RiskAnalysisResult) else RiskAnalysisResult(overall_risk=RiskLevel.NONE, acceptable=True)

            req_str = plan_val.request

            # Determine ExecutionReadiness
            if not dep_val.resolved or dep_val.status in (DependencyStatus.CYCLIC, DependencyStatus.CONFLICT) or risk_val.overall_risk in (RiskLevel.HIGH, RiskLevel.CRITICAL) or not risk_val.acceptable:
                readiness = ExecutionReadiness.BLOCKED
            elif not val_val.valid:
                readiness = ExecutionReadiness.NOT_READY
            elif risk_val.overall_risk == RiskLevel.MEDIUM or val_val.warning_count > 0:
                readiness = ExecutionReadiness.READY_WITH_WARNINGS
            else:
                readiness = ExecutionReadiness.READY

            # Populate execution_order
            if dep_val.execution_order:
                exec_order = list(dep_val.execution_order)
            elif plan_val.steps:
                exec_order = [s.step_number for s in plan_val.steps]
            else:
                exec_order = []

            ctx_metadata = dict(metadata or {})
            if self.config.include_metadata and plan_val.metadata:
                for k, v in plan_val.metadata.items():
                    if k not in ctx_metadata:
                        ctx_metadata[k] = v

            # Execute builder hooks
            if self.config.include_metadata and self._builder_hooks:
                sorted_hooks = sorted(self._builder_hooks, key=lambda h: h.get("priority", 10), reverse=True)
                for hook in sorted_hooks:
                    try:
                        func = hook["hook_func"]
                        updated = func(dict(ctx_metadata))
                        if isinstance(updated, dict):
                            ctx_metadata = updated
                    except Exception as e:
                        logger.warning("Builder hook '%s' raised exception: %s", hook.get("hook_id"), e)

            now = datetime.now(timezone.utc)
            execution_plan = ExecutionPlan(
                request=req_str,
                action_plan=plan_val,
                validation_result=val_val,
                dependency_result=dep_val,
                risk_result=risk_val,
                execution_order=exec_order,
                readiness=readiness,
                current_stage=ExecutionStage.READY_FOR_EXECUTION,
                created_at=now,
                metadata=ctx_metadata,
            )

            logger.info("Execution Plan Built")
            return execution_plan

    def list_builder_hooks(self) -> List[Dict[str, Any]]:
        """Lists registered builder hooks."""
        with self._lock:
            return [
                {
                    "hook_id": h["hook_id"],
                    "priority": h["priority"],
                    "metadata": dict(h.get("metadata", {})),
                }
                for h in self._builder_hooks
            ]
