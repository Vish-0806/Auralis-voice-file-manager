"""Unit tests for RiskAnalyzer (Phase 9.3.4)."""

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
    ActionStep,
    ActionType,
    DependencyResolutionResult,
    DependencyResolver,
    DependencyStatus,
    PlanValidationResult,
    PlanValidator,
    RiskAnalysisResult,
    RiskAnalyzer,
    RiskAnalyzerConfig,
    RiskCategory,
    RiskItem,
    RiskLevel,
    ValidationIssue,
    ValidationSeverity,
)
from brain.reasoning import (
    GoalExtractionResult,
    GoalType,
    ReasoningContextBuilder,
)


@pytest.fixture
def analyzer() -> RiskAnalyzer:
    """Fixture providing a fresh RiskAnalyzer instance."""
    return RiskAnalyzer()


def test_risk_rule_registration(analyzer: RiskAnalyzer) -> None:
    """Verifies registering a custom risk evaluation rule."""
    def custom_rule(p: ActionPlan | None, v: PlanValidationResult | None, d: DependencyResolutionResult | None) -> list[RiskItem]:
        return [RiskItem(code="CUSTOM_RISK", title="Custom Title", description="Custom Desc", category=RiskCategory.CONFIGURATION, risk_level=RiskLevel.LOW)]

    res = analyzer.register_risk_rule("r1", custom_rule)
    assert res is True

    rules = analyzer.list_risk_rules()
    assert len(rules) == 1
    assert rules[0]["rule_id"] == "r1"


def test_risk_rule_removal(analyzer: RiskAnalyzer) -> None:
    """Verifies removing a registered custom risk rule."""
    analyzer.register_risk_rule("r_rem", lambda p, v, d: [])
    removed = analyzer.remove_risk_rule("r_rem")
    assert removed is True
    assert analyzer.list_risk_rules() == []


def test_data_loss_detection(analyzer: RiskAnalyzer) -> None:
    """Verifies DATA_LOSS risk detection on DELETE_FILES and DELETE_FOLDER steps."""
    step1 = ActionStep(step_number=1, action_type=ActionType.DELETE_FILES, description="Delete files")
    plan = ActionPlan(request="test", steps=[step1], step_count=1)

    res = analyzer.analyze_risks(plan)
    assert isinstance(res, RiskAnalysisResult)
    assert res.overall_risk == RiskLevel.HIGH
    assert any(r.category == RiskCategory.DATA_LOSS for r in res.risks)


def test_permission_risk_detection(analyzer: RiskAnalyzer) -> None:
    """Verifies PERMISSION risk detection on protected system path targets."""
    step1 = ActionStep(step_number=1, action_type=ActionType.MOVE_FILES, description="Move", parameters={"destination": "C:\\Windows\\System32\\file.dll"})
    plan = ActionPlan(request="test", steps=[step1], step_count=1)

    res = analyzer.analyze_risks(plan)
    assert res.overall_risk == RiskLevel.HIGH
    assert any(r.category == RiskCategory.PERMISSION for r in res.risks)


def test_overwrite_risk_detection(analyzer: RiskAnalyzer) -> None:
    """Verifies OVERWRITE risk detection on move/copy actions with overwrite flag."""
    step1 = ActionStep(step_number=1, action_type=ActionType.COPY_FILES, description="Copy", parameters={"overwrite": True})
    plan = ActionPlan(request="test", steps=[step1], step_count=1)

    res = analyzer.analyze_risks(plan)
    assert any(r.category == RiskCategory.OVERWRITE for r in res.risks)


def test_dependency_risk_detection(analyzer: RiskAnalyzer) -> None:
    """Verifies DEPENDENCY risk detection on CYCLIC dependency resolution results."""
    dep_res = DependencyResolutionResult(
        resolved=False,
        status=DependencyStatus.CYCLIC,
        conflicts=["Cycle detected"],
    )

    res = analyzer.analyze_risks(dependency_result=dep_res)
    assert res.overall_risk == RiskLevel.CRITICAL
    assert any(r.category == RiskCategory.DEPENDENCY for r in res.risks)


def test_validation_risk_detection(analyzer: RiskAnalyzer) -> None:
    """Verifies VALIDATION risk detection on invalid plan validation results."""
    val_res = PlanValidationResult(
        valid=False,
        issues=[ValidationIssue(code="ERR", message="Failed", severity=ValidationSeverity.ERROR)],
        error_count=1,
    )

    res = analyzer.analyze_risks(validation_result=val_res)
    assert res.overall_risk == RiskLevel.HIGH
    assert any(r.category == RiskCategory.VALIDATION for r in res.risks)


def test_configuration_risk_detection(analyzer: RiskAnalyzer) -> None:
    """Verifies CONFIGURATION risk detection."""
    def cfg_rule(p: ActionPlan | None, v: PlanValidationResult | None, d: DependencyResolutionResult | None) -> list[RiskItem]:
        return [RiskItem(code="CFG_RISK", title="Config Error", description="Inconsistent cfg", category=RiskCategory.CONFIGURATION, risk_level=RiskLevel.MEDIUM)]

    analyzer.register_risk_rule("cfg", cfg_rule)
    res = analyzer.analyze_risks()
    assert any(r.category == RiskCategory.CONFIGURATION for r in res.risks)


def test_unknown_risk_handling(analyzer: RiskAnalyzer) -> None:
    """Verifies UNKNOWN category risk detection on NO_ACTION steps."""
    step1 = ActionStep(step_number=1, action_type=ActionType.NO_ACTION, description="No action")
    plan = ActionPlan(request="test", steps=[step1], step_count=1)

    res = analyzer.analyze_risks(plan)
    assert any(r.category == RiskCategory.UNKNOWN for r in res.risks)


def test_overall_risk_calculation(analyzer: RiskAnalyzer) -> None:
    """Verifies overall_risk returns the highest severity among detected risk items."""
    step1 = ActionStep(step_number=1, action_type=ActionType.NO_ACTION, description="Low risk")
    step2 = ActionStep(step_number=2, action_type=ActionType.DELETE_FOLDER, description="Critical risk")
    plan = ActionPlan(request="test", steps=[step1, step2], step_count=2)

    res = analyzer.analyze_risks(plan)
    assert res.overall_risk == RiskLevel.CRITICAL


def test_acceptable_flag(analyzer: RiskAnalyzer) -> None:
    """Verifies acceptable flag calculation in strict vs non-strict mode."""
    step1 = ActionStep(step_number=1, action_type=ActionType.DELETE_FILES, description="High risk deletion")
    plan = ActionPlan(request="test", steps=[step1], step_count=1)

    # Strict mode: HIGH risk -> acceptable=False
    res_strict = analyzer.analyze_risks(plan)
    assert res_strict.acceptable is False

    # Non-strict mode: HIGH risk -> acceptable=True (only CRITICAL is unacceptable)
    lenient_analyzer = RiskAnalyzer(config=RiskAnalyzerConfig(strict_mode=False))
    res_lenient = lenient_analyzer.analyze_risks(plan)
    assert res_lenient.acceptable is True


def test_immutable_models(analyzer: RiskAnalyzer) -> None:
    """Verifies RiskItem and RiskAnalysisResult models are immutable snapshots."""
    res = analyzer.analyze_risks()
    with pytest.raises((TypeError, ValidationError)):
        res.overall_risk = RiskLevel.CRITICAL

    item = RiskItem(code="R1", title="T1", description="D1", category=RiskCategory.UNKNOWN, risk_level=RiskLevel.LOW)
    with pytest.raises((TypeError, ValidationError)):
        item.title = "MUTATED"


def test_metadata(analyzer: RiskAnalyzer) -> None:
    """Verifies metadata propagation from ActionPlan into RiskAnalysisResult."""
    plan = ActionPlan(request="req", metadata={"user_id": "u100"})
    res = analyzer.analyze_risks(plan)

    assert res.metadata == {"user_id": "u100"}


def test_configuration_injection() -> None:
    """Verifies RiskAnalyzerConfig options."""
    cfg = RiskAnalyzerConfig(strict_mode=False, maximum_risks=1, include_recommendations=False)
    ra = RiskAnalyzer(config=cfg)

    step1 = ActionStep(step_number=1, action_type=ActionType.DELETE_FILES, description="Delete")
    plan = ActionPlan(request="test", steps=[step1], step_count=1)

    res = ra.analyze_risks(plan)
    assert res.risks[0].recommendation == ""


def test_registry_clearing(analyzer: RiskAnalyzer) -> None:
    """Verifies clear_risk_rules removes all custom rules."""
    analyzer.register_risk_rule("r1", lambda p, v, d: [])
    analyzer.clear_risk_rules()
    assert analyzer.list_risk_rules() == []


def test_listing(analyzer: RiskAnalyzer) -> None:
    """Verifies list_risk_rules returns metadata list."""
    analyzer.register_risk_rule("r1", lambda p, v, d: [], priority=5, metadata={"tag": "test"})
    rules = analyzer.list_risk_rules()

    assert len(rules) == 1
    assert rules[0]["rule_id"] == "r1"
    assert rules[0]["priority"] == 5


def test_thread_safety() -> None:
    """Verifies thread safety under concurrent rule registrations and risk evaluations."""
    ra = RiskAnalyzer()
    plan = ActionPlan(request="req")

    def worker(idx: int) -> None:
        ra.register_risk_rule(f"r_{idx}", lambda p, v, d: [])
        ra.analyze_risks(plan)

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker, i) for i in range(50)]
        for f in futures:
            f.result()

    res = ra.analyze_risks(plan)
    assert isinstance(res, RiskAnalysisResult)


def test_graceful_failures(analyzer: RiskAnalyzer) -> None:
    """Verifies custom rules raising exceptions do not crash risk analysis."""
    def faulty_rule(p: ActionPlan | None, v: PlanValidationResult | None, d: DependencyResolutionResult | None) -> list[RiskItem]:
        raise RuntimeError("Rule error!")

    analyzer.register_risk_rule("faulty", faulty_rule)
    res = analyzer.analyze_risks()

    assert isinstance(res, RiskAnalysisResult)


def test_singleton_compatibility() -> None:
    """Verifies RiskAnalyzer operational behavior."""
    ra1 = RiskAnalyzer()
    ra2 = RiskAnalyzer()
    assert isinstance(ra1, RiskAnalyzer)
    assert isinstance(ra2, RiskAnalyzer)


def test_backward_compatibility() -> None:
    """Verifies backward compatibility with pre-existing brain.planning exports."""
    from brain.planning import (
        ActionPlanner,
        DependencyResolver,
        PlanValidator,
        RiskAnalysisResult,
        RiskAnalyzer,
        RiskCategory,
        RiskItem,
        RiskLevel,
    )

    ra = RiskAnalyzer()
    assert ra is not None


def test_integration_with_dependency_resolver(analyzer: RiskAnalyzer) -> None:
    """Verifies risk analysis integrating DependencyResolver and PlanValidator outputs."""
    planner = ActionPlanner()
    validator = PlanValidator()
    resolver = DependencyResolver()
    builder = ReasoningContextBuilder()

    ctx = builder.build_context("delete folder temp", goal_result=GoalExtractionResult(goal_type=GoalType.DELETE_FOLDER))
    plan = planner.create_plan(ctx)
    val_res = validator.validate_plan(plan)
    dep_res = resolver.resolve_dependencies(plan)

    res = analyzer.analyze_risks(plan, val_res, dep_res)
    assert res.overall_risk == RiskLevel.CRITICAL


def test_logging(caplog: pytest.LogCaptureFixture, analyzer: RiskAnalyzer) -> None:
    """Verifies required event log outputs."""
    with caplog.at_level(logging.INFO):
        analyzer.register_risk_rule("r1", lambda p, v, d: [])
        analyzer.analyze_risks()
        analyzer.remove_risk_rule("r1")
        analyzer.clear_risk_rules()

    assert "Risk Rule Registered" in caplog.text
    assert "Risk Analysis Performed" in caplog.text
    assert "Risk Rule Removed" in caplog.text
    assert "Risk Registry Cleared" in caplog.text


def test_timestamps(analyzer: RiskAnalyzer) -> None:
    """Verifies analyzed_at timestamp is generated automatically."""
    res = analyzer.analyze_risks()
    assert isinstance(res.analyzed_at, datetime)


def test_regression_validation(analyzer: RiskAnalyzer) -> None:
    """Verifies empty plan evaluation produces RiskLevel.NONE and acceptable=True."""
    plan = ActionPlan(request="safe plan", steps=[], step_count=0)
    res = analyzer.analyze_risks(plan)

    assert res.overall_risk == RiskLevel.NONE
    assert res.acceptable is True
