"""Unit tests for PlanValidator (Phase 9.3.2)."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import logging
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from brain.planning import (
    ActionPlan,
    ActionPlanner,
    ActionPriority,
    ActionStep,
    ActionType,
    PlanValidationResult,
    PlanValidator,
    PlanValidatorConfig,
    ValidationIssue,
    ValidationSeverity,
)
from brain.reasoning import (
    GoalExtractionResult,
    GoalType,
    ReasoningContextBuilder,
)


@pytest.fixture
def validator() -> PlanValidator:
    """Fixture providing a fresh PlanValidator instance."""
    return PlanValidator()


def test_validation_rule_registration(validator: PlanValidator) -> None:
    """Verifies registering a custom plan validation rule."""
    def rule_func(plan: ActionPlan) -> list[ValidationIssue]:
        return [ValidationIssue(code="CUSTOM_RULE", message="Custom Issue", severity=ValidationSeverity.WARNING)]

    res = validator.register_validation_rule("r1", rule_func)
    assert res is True

    rules = validator.list_validation_rules()
    assert len(rules) == 1
    assert rules[0]["rule_id"] == "r1"


def test_validation_rule_removal(validator: PlanValidator) -> None:
    """Verifies removing a registered custom validation rule."""
    validator.register_validation_rule("r_rem", lambda p: [])
    removed = validator.remove_validation_rule("r_rem")
    assert removed is True
    assert validator.list_validation_rules() == []


def test_valid_plans(validator: PlanValidator) -> None:
    """Verifies a valid ActionPlan produces valid=True validation result."""
    planner = ActionPlanner()
    builder = ReasoningContextBuilder()
    ctx = builder.build_context("move pdfs", goal_result=GoalExtractionResult(goal_type=GoalType.MOVE_FILES))
    plan = planner.create_plan(ctx)

    res = validator.validate_plan(plan)
    assert isinstance(res, PlanValidationResult)
    assert res.valid is True
    assert res.error_count == 0


def test_invalid_plans(validator: PlanValidator) -> None:
    """Verifies an invalid non-ActionPlan input produces valid=False result."""
    res = validator.validate_plan("invalid_input")  # type: ignore
    assert res.valid is False
    assert res.error_count == 1
    assert res.issues[0].code == "INVALID_PLAN_INPUT"


def test_duplicate_steps(validator: PlanValidator) -> None:
    """Verifies detection of duplicate step numbers."""
    step1 = ActionStep(step_number=1, action_type=ActionType.LOCATE_FILES, description="Locate")
    step2 = ActionStep(step_number=1, action_type=ActionType.COPY_FILES, description="Copy")
    plan = ActionPlan(request="test", steps=[step1, step2], step_count=2)

    res = validator.validate_plan(plan)
    assert res.valid is False
    assert any(i.code == "DUPLICATE_STEP_NUMBER" for i in res.issues)


def test_duplicate_actions(validator: PlanValidator) -> None:
    """Verifies detection of duplicate consecutive action types."""
    step1 = ActionStep(step_number=1, action_type=ActionType.COPY_FILES, description="Copy 1")
    step2 = ActionStep(step_number=2, action_type=ActionType.COPY_FILES, description="Copy 2")
    plan = ActionPlan(request="test", steps=[step1, step2], step_count=2)

    res = validator.validate_plan(plan)
    assert res.warning_count >= 1
    assert any(i.code == "DUPLICATE_CONSECUTIVE_ACTION" for i in res.issues)


def test_empty_plans(validator: PlanValidator) -> None:
    """Verifies validation behavior for empty ActionPlan."""
    plan = ActionPlan(request="test", steps=[], step_count=0)
    res = validator.validate_plan(plan)
    assert res.valid is False
    assert any(i.code == "EMPTY_PLAN" for i in res.issues)


def test_no_action_plans(validator: PlanValidator) -> None:
    """Verifies warning generation for single step NO_ACTION plans."""
    planner = ActionPlanner()
    builder = ReasoningContextBuilder()
    ctx = builder.build_context("unknown", goal_result=GoalExtractionResult(goal_type=GoalType.UNKNOWN))
    plan = planner.create_plan(ctx)

    res = validator.validate_plan(plan)
    assert res.valid is True
    assert res.warning_count >= 1
    assert any(i.code == "NO_ACTION_PLAN" for i in res.issues)


def test_malformed_plans(validator: PlanValidator) -> None:
    """Verifies non-ActionPlan input parameter handling."""
    res = validator.validate_plan(None)
    assert res.valid is False
    assert res.error_count == 1


def test_immutable_results(validator: PlanValidator) -> None:
    """Verifies PlanValidationResult and ValidationIssue models are immutable snapshots."""
    res = validator.validate_plan(None)
    with pytest.raises((TypeError, ValidationError)):
        res.valid = True

    if res.issues:
        with pytest.raises((TypeError, ValidationError)):
            res.issues[0].code = "MUTATED"


def test_metadata(validator: PlanValidator) -> None:
    """Verifies metadata propagation from ActionPlan to PlanValidationResult."""
    plan = ActionPlan(request="req", metadata={"user": "u1"})
    res = validator.validate_plan(plan)

    assert res.metadata == {"user": "u1"}


def test_configuration_injection() -> None:
    """Verifies PlanValidatorConfig custom settings."""
    cfg = PlanValidatorConfig(allow_empty_plans=True)
    pv = PlanValidator(config=cfg)

    plan = ActionPlan(request="empty", steps=[])
    res = pv.validate_plan(plan)

    assert res.valid is True
    assert not any(i.code == "EMPTY_PLAN" for i in res.issues)


def test_thread_safety() -> None:
    """Verifies thread safety under concurrent rule registrations and plan validations."""
    pv = PlanValidator()
    plan = ActionPlan(request="req")

    def worker(idx: int) -> None:
        pv.register_validation_rule(f"r_{idx}", lambda p: [])
        pv.validate_plan(plan)

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker, i) for i in range(50)]
        for f in futures:
            f.result()

    res = pv.validate_plan(plan)
    assert isinstance(res, PlanValidationResult)


def test_registry_clearing(validator: PlanValidator) -> None:
    """Verifies clear_validation_rules removes all custom rules."""
    validator.register_validation_rule("r1", lambda p: [])
    validator.clear_validation_rules()
    assert validator.list_validation_rules() == []


def test_listing(validator: PlanValidator) -> None:
    """Verifies list_validation_rules returns metadata list."""
    validator.register_validation_rule("r1", lambda p: [], priority=5, metadata={"tag": "t"})
    rules = validator.list_validation_rules()

    assert len(rules) == 1
    assert rules[0]["rule_id"] == "r1"
    assert rules[0]["priority"] == 5


def test_graceful_failures(validator: PlanValidator) -> None:
    """Verifies custom rules raising exceptions do not crash plan validation."""
    def faulty_rule(p: ActionPlan) -> list[ValidationIssue]:
        raise RuntimeError("Rule exception!")

    validator.register_validation_rule("faulty", faulty_rule)
    plan = ActionPlan(request="req")
    res = validator.validate_plan(plan)

    assert isinstance(res, PlanValidationResult)


def test_singleton_compatibility() -> None:
    """Verifies PlanValidator instance operational behavior."""
    v1 = PlanValidator()
    v2 = PlanValidator()
    assert isinstance(v1, PlanValidator)
    assert isinstance(v2, PlanValidator)


def test_backward_compatibility() -> None:
    """Verifies backward compatibility with pre-existing planning exports."""
    from brain.planning import (
        ActionPlanner,
        PlanValidationResult,
        PlanValidator,
        PlanValidatorConfig,
        ValidationIssue,
        ValidationSeverity,
    )

    pv = PlanValidator()
    assert pv is not None


def test_integration_with_action_planner(validator: PlanValidator) -> None:
    """Verifies validating ActionPlan created by ActionPlanner."""
    planner = ActionPlanner()
    builder = ReasoningContextBuilder()
    ctx = builder.build_context("delete files", goal_result=GoalExtractionResult(goal_type=GoalType.DELETE_FILES))
    plan = planner.create_plan(ctx)

    res = validator.validate_plan(plan)
    assert res.valid is True


def test_logging(caplog: pytest.LogCaptureFixture, validator: PlanValidator) -> None:
    """Verifies required event log outputs."""
    with caplog.at_level(logging.INFO):
        validator.register_validation_rule("r1", lambda p: [])
        validator.validate_plan(None)
        validator.remove_validation_rule("r1")
        validator.clear_validation_rules()

    assert "Validation Rule Registered" in caplog.text
    assert "Plan Validated" in caplog.text
    assert "Validation Rule Removed" in caplog.text
    assert "Validation Registry Cleared" in caplog.text


def test_regression_validation(validator: PlanValidator) -> None:
    """Verifies plan validation with non-sequential steps."""
    step1 = ActionStep(step_number=1, action_type=ActionType.LOCATE_FILES, description="Locate")
    step3 = ActionStep(step_number=3, action_type=ActionType.OPEN_FILE, description="Open")
    plan = ActionPlan(request="test", steps=[step1, step3], step_count=2)

    res = validator.validate_plan(plan)
    assert res.valid is False
    assert any(i.code == "STEP_ORDER_NON_SEQUENTIAL" for i in res.issues)


def test_configuration_validation() -> None:
    """Verifies PlanValidatorConfig properties."""
    cfg = PlanValidatorConfig(strict_validation=False, allow_empty_plans=True, validate_step_order=False, validate_duplicates=False)
    pv = PlanValidator(config=cfg)

    assert pv.config.strict_validation is False
    assert pv.config.allow_empty_plans is True
    assert pv.config.validate_step_order is False
    assert pv.config.validate_duplicates is False


def test_validation_timestamps(validator: PlanValidator) -> None:
    """Verifies validated_at timestamp is generated automatically."""
    res = validator.validate_plan(None)
    assert isinstance(res.validated_at, datetime)


def test_warning_generation(validator: PlanValidator) -> None:
    """Verifies warning issues count vs error issues count calculation."""
    step1 = ActionStep(step_number=1, action_type=ActionType.LOCATE_FILES, description="")
    plan = ActionPlan(request="test", steps=[step1], step_count=1)

    res = validator.validate_plan(plan)
    assert res.valid is True
    assert res.warning_count >= 1
    assert res.error_count == 0
