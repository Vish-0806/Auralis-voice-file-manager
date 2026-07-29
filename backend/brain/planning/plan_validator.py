"""Plan Validator for deterministic validation of ActionPlan objects.

This module provides thread-safe plan validation without executing commands, modifying ActionPlans,
resolving dependencies, analyzing execution risks, calling LLMs, or accessing memory providers.
"""

from datetime import datetime, timezone
from enum import Enum
import logging
import threading
from typing import Any, Callable, Dict, List, Optional

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field

from brain.planning.action_planner import ActionPlan, ActionStep, ActionType

logger = logging.getLogger(__name__)


class ValidationSeverity(str, Enum):
    """Enumeration of plan validation severity levels."""

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ValidationIssue(BaseModel):
    """Immutable model representing a single validation issue or warning."""

    model_config = ConfigDict(frozen=True)

    code: str
    message: str
    severity: ValidationSeverity
    step_number: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PlanValidationResult(BaseModel):
    """Immutable model representing the outcome of ActionPlan validation."""

    model_config = ConfigDict(frozen=True)

    valid: bool
    issues: List[ValidationIssue] = Field(default_factory=list)
    warnings: List[ValidationIssue] = Field(default_factory=list)
    error_count: int = 0
    warning_count: int = 0
    validated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PlanValidatorConfig(BaseModel):
    """Configuration options for PlanValidator behavior."""

    strict_validation: bool = True
    allow_empty_plans: bool = False
    validate_step_order: bool = True
    validate_duplicates: bool = True


class PlanValidator:
    """Thread-safe engine for validating ActionPlan objects."""

    def __init__(self, config: Optional[PlanValidatorConfig] = None) -> None:
        """Initializes the PlanValidator with optional configuration and thread lock."""
        self.config = config or PlanValidatorConfig()
        self._validation_rules: List[Dict[str, Any]] = []
        self._lock = threading.RLock()

    def register_validation_rule(
        self,
        rule_id: str,
        validator_func: Callable[[ActionPlan], List[ValidationIssue]],
        priority: int = 10,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Registers a custom plan validation rule."""
        with self._lock:
            self._validation_rules = [r for r in self._validation_rules if r["rule_id"] != rule_id]
            entry = {
                "rule_id": rule_id,
                "validator_func": validator_func,
                "priority": priority,
                "metadata": metadata or {},
            }
            self._validation_rules.append(entry)
            logger.info("Validation Rule Registered: rule_id=%s", rule_id)
            return True

    def remove_validation_rule(self, rule_id: str) -> bool:
        """Removes a registered custom validation rule by rule_id."""
        with self._lock:
            initial_count = len(self._validation_rules)
            self._validation_rules = [r for r in self._validation_rules if r["rule_id"] != rule_id]
            removed = len(self._validation_rules) < initial_count

            if removed:
                logger.info("Validation Rule Removed: rule_id=%s", rule_id)
                return True
            return False

    def clear_validation_rules(self) -> None:
        """Clears all custom validation rules from the registry."""
        with self._lock:
            self._validation_rules.clear()
            logger.info("Validation Registry Cleared")

    def validate_plan(self, plan: Optional[ActionPlan] = None) -> PlanValidationResult:
        """Validates an ActionPlan against built-in and registered validation rules."""
        with self._lock:
            now = datetime.now(timezone.utc)
            all_issues: List[ValidationIssue] = []

            if not isinstance(plan, ActionPlan):
                issue = ValidationIssue(
                    code="INVALID_PLAN_INPUT",
                    message="Input is not a valid ActionPlan instance",
                    severity=ValidationSeverity.ERROR,
                )
                all_issues.append(issue)
                result = PlanValidationResult(
                    valid=False,
                    issues=all_issues,
                    warnings=[],
                    error_count=1,
                    warning_count=0,
                    validated_at=now,
                    metadata={},
                )
                logger.info("Plan Validated")
                return result

            # Rule 1: Empty Plan Check
            if not plan.steps:
                if not self.config.allow_empty_plans:
                    all_issues.append(
                        ValidationIssue(
                            code="EMPTY_PLAN",
                            message="ActionPlan contains zero steps",
                            severity=ValidationSeverity.ERROR,
                        )
                    )
            else:
                # Rule 2: NO_ACTION Check
                if len(plan.steps) == 1 and plan.steps[0].action_type == ActionType.NO_ACTION:
                    all_issues.append(
                        ValidationIssue(
                            code="NO_ACTION_PLAN",
                            message="ActionPlan contains NO_ACTION step",
                            severity=ValidationSeverity.WARNING,
                            step_number=1,
                        )
                    )

                # Rule 3: Step Order & Duplicates
                seen_steps = set()
                previous_action: Optional[ActionType] = None

                for expected_idx, step in enumerate(plan.steps, start=1):
                    # Check step number sequence
                    if self.config.validate_step_order and step.step_number != expected_idx:
                        all_issues.append(
                            ValidationIssue(
                                code="STEP_ORDER_NON_SEQUENTIAL",
                                message=f"Step number {step.step_number} is non-sequential; expected {expected_idx}",
                                severity=ValidationSeverity.ERROR,
                                step_number=step.step_number,
                            )
                        )

                    # Check duplicate step numbers
                    if self.config.validate_duplicates and step.step_number in seen_steps:
                        all_issues.append(
                            ValidationIssue(
                                code="DUPLICATE_STEP_NUMBER",
                                message=f"Duplicate step number {step.step_number} detected",
                                severity=ValidationSeverity.ERROR,
                                step_number=step.step_number,
                            )
                        )
                    seen_steps.add(step.step_number)

                    # Check duplicate consecutive actions
                    if self.config.validate_duplicates and previous_action == step.action_type:
                        all_issues.append(
                            ValidationIssue(
                                code="DUPLICATE_CONSECUTIVE_ACTION",
                                message=f"Consecutive duplicate action {step.action_type} detected at step {step.step_number}",
                                severity=ValidationSeverity.WARNING,
                                step_number=step.step_number,
                            )
                        )
                    previous_action = step.action_type

                    # Check missing description
                    if not step.description or not step.description.strip():
                        all_issues.append(
                            ValidationIssue(
                                code="MISSING_STEP_DESCRIPTION",
                                message=f"Missing description at step {step.step_number}",
                                severity=ValidationSeverity.WARNING,
                                step_number=step.step_number,
                            )
                        )

            # Custom registered validation rules sorted by priority descending
            if self._validation_rules:
                sorted_rules = sorted(self._validation_rules, key=lambda r: r.get("priority", 10), reverse=True)
                for r in sorted_rules:
                    try:
                        custom_issues = r["validator_func"](plan)
                        if custom_issues and isinstance(custom_issues, list):
                            for ci in custom_issues:
                                if isinstance(ci, ValidationIssue):
                                    all_issues.append(ci)
                    except Exception as e:
                        logger.warning("Validation rule '%s' raised exception: %s", r.get("rule_id"), e)

            warnings = [i for i in all_issues if i.severity in (ValidationSeverity.WARNING, ValidationSeverity.INFO)]
            errors = [i for i in all_issues if i.severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL)]

            is_valid = len(errors) == 0 if self.config.strict_validation else True

            result = PlanValidationResult(
                valid=is_valid,
                issues=all_issues,
                warnings=warnings,
                error_count=len(errors),
                warning_count=len(warnings),
                validated_at=now,
                metadata=dict(plan.metadata),
            )

            logger.info("Plan Validated")
            return result

    def list_validation_rules(self) -> List[Dict[str, Any]]:
        """Lists registered custom validation rules."""
        with self._lock:
            return [
                {
                    "rule_id": r["rule_id"],
                    "priority": r["priority"],
                    "metadata": dict(r.get("metadata", {})),
                }
                for r in self._validation_rules
            ]
