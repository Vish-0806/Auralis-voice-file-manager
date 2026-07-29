"""Risk Analyzer for evaluating execution risks for ActionPlans.

This module provides thread-safe risk assessment without executing actions, modifying ActionPlans,
modifying PlanValidationResult, modifying DependencyResolutionResult, calling LLMs,
accessing memory providers, or interacting with the operating system.
"""

from datetime import datetime, timezone
from enum import Enum
import logging
import threading
from typing import Any, Callable, Dict, List, Optional

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field

from brain.planning.action_planner import ActionPlan, ActionStep, ActionType
from brain.planning.dependency_resolver import DependencyResolutionResult, DependencyStatus
from brain.planning.plan_validator import PlanValidationResult, ValidationSeverity

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """Enumeration of risk severity levels."""

    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskCategory(str, Enum):
    """Enumeration of execution risk categories."""

    DATA_LOSS = "DATA_LOSS"
    PERMISSION = "PERMISSION"
    OVERWRITE = "OVERWRITE"
    SYSTEM_RESOURCE = "SYSTEM_RESOURCE"
    DEPENDENCY = "DEPENDENCY"
    VALIDATION = "VALIDATION"
    CONFIGURATION = "CONFIGURATION"
    UNKNOWN = "UNKNOWN"


class RiskItem(BaseModel):
    """Immutable model representing a single detected execution risk."""

    model_config = ConfigDict(frozen=True)

    code: str
    title: str
    description: str
    category: RiskCategory
    risk_level: RiskLevel
    affected_step: Optional[int] = None
    recommendation: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RiskAnalysisResult(BaseModel):
    """Immutable model representing the outcome of execution risk analysis."""

    model_config = ConfigDict(frozen=True)

    overall_risk: RiskLevel
    acceptable: bool
    risks: List[RiskItem] = Field(default_factory=list)
    risk_count: int = 0
    analyzed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RiskAnalyzerConfig(BaseModel):
    """Configuration options for RiskAnalyzer behavior."""

    strict_mode: bool = True
    maximum_risks: int = 500
    include_recommendations: bool = True


RISK_LEVEL_ORDER = {
    RiskLevel.NONE: 0,
    RiskLevel.LOW: 1,
    RiskLevel.MEDIUM: 2,
    RiskLevel.HIGH: 3,
    RiskLevel.CRITICAL: 4,
}


class RiskAnalyzer:
    """Thread-safe engine for evaluating execution risks of ActionPlans."""

    def __init__(self, config: Optional[RiskAnalyzerConfig] = None) -> None:
        """Initializes the RiskAnalyzer with optional configuration and thread lock."""
        self.config = config or RiskAnalyzerConfig()
        self._risk_rules: List[Dict[str, Any]] = []
        self._lock = threading.RLock()

    def register_risk_rule(
        self,
        rule_id: str,
        rule_func: Callable[[Optional[ActionPlan], Optional[PlanValidationResult], Optional[DependencyResolutionResult]], List[RiskItem]],
        priority: int = 10,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Registers a custom risk evaluation rule."""
        with self._lock:
            self._risk_rules = [r for r in self._risk_rules if r["rule_id"] != rule_id]
            entry = {
                "rule_id": rule_id,
                "rule_func": rule_func,
                "priority": priority,
                "metadata": metadata or {},
            }
            self._risk_rules.append(entry)
            logger.info("Risk Rule Registered: rule_id=%s", rule_id)
            return True

    def remove_risk_rule(self, rule_id: str) -> bool:
        """Removes a registered custom risk rule by rule_id."""
        with self._lock:
            initial_count = len(self._risk_rules)
            self._risk_rules = [r for r in self._risk_rules if r["rule_id"] != rule_id]
            removed = len(self._risk_rules) < initial_count

            if removed:
                logger.info("Risk Rule Removed: rule_id=%s", rule_id)
                return True
            return False

    def clear_risk_rules(self) -> None:
        """Clears all custom risk rules from the registry."""
        with self._lock:
            self._risk_rules.clear()
            logger.info("Risk Registry Cleared")

    def analyze_risks(
        self,
        plan: Optional[ActionPlan] = None,
        validation_result: Optional[PlanValidationResult] = None,
        dependency_result: Optional[DependencyResolutionResult] = None,
    ) -> RiskAnalysisResult:
        """Evaluates execution risks across ActionPlan, PlanValidationResult, and DependencyResolutionResult."""
        with self._lock:
            now = datetime.now(timezone.utc)
            detected_risks: List[RiskItem] = []

            # 1. ActionPlan Checks
            if isinstance(plan, ActionPlan) and plan.steps:
                for step in plan.steps:
                    # Check DATA_LOSS risk for deletions
                    if step.action_type in (ActionType.DELETE_FILES, ActionType.DELETE_FOLDER):
                        risk_lvl = RiskLevel.CRITICAL if step.action_type == ActionType.DELETE_FOLDER else RiskLevel.HIGH
                        detected_risks.append(
                            RiskItem(
                                code="DELETION_DATA_LOSS_RISK",
                                title="File/Folder Deletion Risk",
                                description=f"Step {step.step_number} performs destructive deletion ({step.action_type.value})",
                                category=RiskCategory.DATA_LOSS,
                                risk_level=risk_lvl,
                                affected_step=step.step_number,
                                recommendation="Require user confirmation before proceeding with deletion." if self.config.include_recommendations else "",
                            )
                        )

                    # Check PERMISSION risk for system folders
                    target_path = str(step.parameters.get("target") or step.parameters.get("destination") or "").lower()
                    if any(sys_dir in target_path for sys_dir in ["system32", "windows", "program files", "/usr", "/etc"]):
                        detected_risks.append(
                            RiskItem(
                                code="SYSTEM_PERMISSION_RISK",
                                title="Protected System Location Access",
                                description=f"Step {step.step_number} targets protected system path '{target_path}'",
                                category=RiskCategory.PERMISSION,
                                risk_level=RiskLevel.HIGH,
                                affected_step=step.step_number,
                                recommendation="Verify elevated write permissions on target directory." if self.config.include_recommendations else "",
                            )
                        )

                    # Check OVERWRITE risk for copy/move actions
                    if step.action_type in (ActionType.COPY_FILES, ActionType.MOVE_FILES) and step.parameters.get("overwrite"):
                        detected_risks.append(
                            RiskItem(
                                code="FILE_OVERWRITE_RISK",
                                title="Existing File Overwrite Risk",
                                description=f"Step {step.step_number} has overwrite flag enabled for {step.action_type.value}",
                                category=RiskCategory.OVERWRITE,
                                risk_level=RiskLevel.MEDIUM,
                                affected_step=step.step_number,
                                recommendation="Create backup before overwriting target files." if self.config.include_recommendations else "",
                            )
                        )

                    # Check UNKNOWN/NO_ACTION steps
                    if step.action_type == ActionType.NO_ACTION:
                        detected_risks.append(
                            RiskItem(
                                code="NO_ACTION_STEP_RISK",
                                title="Unresolved Step Action",
                                description=f"Step {step.step_number} is NO_ACTION",
                                category=RiskCategory.UNKNOWN,
                                risk_level=RiskLevel.LOW,
                                affected_step=step.step_number,
                                recommendation="Review request intent for unsupported operations." if self.config.include_recommendations else "",
                            )
                        )

            # 2. PlanValidationResult Checks
            if isinstance(validation_result, PlanValidationResult) and not validation_result.valid:
                for issue in validation_result.issues:
                    if issue.severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL):
                        detected_risks.append(
                            RiskItem(
                                code="PLAN_VALIDATION_ERROR_RISK",
                                title="Plan Validation Error",
                                description=f"Validation failed: {issue.message}",
                                category=RiskCategory.VALIDATION,
                                risk_level=RiskLevel.HIGH,
                                affected_step=issue.step_number,
                                recommendation="Resolve plan validation errors prior to execution." if self.config.include_recommendations else "",
                            )
                        )

            # 3. DependencyResolutionResult Checks
            if isinstance(dependency_result, DependencyResolutionResult) and not dependency_result.resolved:
                risk_lvl = RiskLevel.CRITICAL if dependency_result.status == DependencyStatus.CYCLIC else RiskLevel.HIGH
                detected_risks.append(
                    RiskItem(
                        code="DEPENDENCY_RESOLUTION_RISK",
                        title="Dependency Resolution Failure",
                        description=f"Dependency status is {dependency_result.status.value}",
                        category=RiskCategory.DEPENDENCY,
                        risk_level=risk_lvl,
                        affected_step=None,
                        recommendation="Resolve cyclic or conflicting dependencies." if self.config.include_recommendations else "",
                    )
                )

            # 4. Custom Registered Rules
            if self._risk_rules:
                sorted_rules = sorted(self._risk_rules, key=lambda r: r.get("priority", 10), reverse=True)
                for r in sorted_rules:
                    try:
                        custom_risks = r["rule_func"](plan, validation_result, dependency_result)
                        if custom_risks and isinstance(custom_risks, list):
                            for cr in custom_risks:
                                if isinstance(cr, RiskItem) and len(detected_risks) < self.config.maximum_risks:
                                    detected_risks.append(cr)
                    except Exception as e:
                        logger.warning("Risk rule '%s' raised exception: %s", r.get("rule_id"), e)

            # Calculate overall_risk
            if not detected_risks:
                overall_risk = RiskLevel.NONE
            else:
                max_rank = max(RISK_LEVEL_ORDER[r.risk_level] for r in detected_risks)
                overall_risk = next(k for k, v in RISK_LEVEL_ORDER.items() if v == max_rank)

            # Calculate acceptable flag
            if self.config.strict_mode:
                acceptable = overall_risk in (RiskLevel.NONE, RiskLevel.LOW, RiskLevel.MEDIUM)
            else:
                acceptable = overall_risk != RiskLevel.CRITICAL

            metadata_out = dict(plan.metadata) if isinstance(plan, ActionPlan) else {}

            result = RiskAnalysisResult(
                overall_risk=overall_risk,
                acceptable=acceptable,
                risks=detected_risks,
                risk_count=len(detected_risks),
                analyzed_at=now,
                metadata=metadata_out,
            )

            logger.info("Risk Analysis Performed")
            return result

    def list_risk_rules(self) -> List[Dict[str, Any]]:
        """Lists registered custom risk rules."""
        with self._lock:
            return [
                {
                    "rule_id": r["rule_id"],
                    "priority": r["priority"],
                    "metadata": dict(r.get("metadata", {})),
                }
                for r in self._risk_rules
            ]
