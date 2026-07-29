"""Unit tests for ExecutionPlanBuilder (Phase 9.3.5)."""

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
    ExecutionPlan,
    ExecutionPlanBuilder,
    ExecutionPlanBuilderConfig,
    ExecutionReadiness,
    ExecutionStage,
    PlanValidationResult,
    PlanValidator,
    RiskAnalysisResult,
    RiskAnalyzer,
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
def builder() -> ExecutionPlanBuilder:
    """Fixture providing a fresh ExecutionPlanBuilder instance."""
    return ExecutionPlanBuilder()


def test_builder_hook_registration(builder: ExecutionPlanBuilder) -> None:
    """Verifies registering a custom builder hook."""
    def sample_hook(meta: dict) -> dict:
        meta["hooked"] = True
        return meta

    res = builder.register_builder_hook("h1", sample_hook)
    assert res is True

    hooks = builder.list_builder_hooks()
    assert len(hooks) == 1
    assert hooks[0]["hook_id"] == "h1"


def test_builder_hook_removal(builder: ExecutionPlanBuilder) -> None:
    """Verifies removing a registered builder hook."""
    builder.register_builder_hook("h_rem", lambda m: m)
    removed = builder.remove_builder_hook("h_rem")
    assert removed is True
    assert builder.list_builder_hooks() == []


def test_ready_plan_creation(builder: ExecutionPlanBuilder) -> None:
    """Verifies READY readiness classification for valid, low-risk planning outputs."""
    plan = ActionPlan(request="test", steps=[ActionStep(step_number=1, action_type=ActionType.SEARCH, description="Search")])
    val_res = PlanValidationResult(valid=True)
    dep_res = DependencyResolutionResult(resolved=True, status=DependencyStatus.RESOLVED, execution_order=[1])
    risk_res = RiskAnalysisResult(overall_risk=RiskLevel.NONE, acceptable=True)

    exec_plan = builder.build_execution_plan(plan, val_res, dep_res, risk_res)

    assert isinstance(exec_plan, ExecutionPlan)
    assert exec_plan.readiness == ExecutionReadiness.READY
    assert exec_plan.current_stage == ExecutionStage.READY_FOR_EXECUTION
    assert exec_plan.execution_order == [1]


def test_ready_with_warnings(builder: ExecutionPlanBuilder) -> None:
    """Verifies READY_WITH_WARNINGS readiness classification when warnings or medium risk exist."""
    plan = ActionPlan(request="test", steps=[ActionStep(step_number=1, action_type=ActionType.COPY_FILES, description="Copy")])
    val_res = PlanValidationResult(valid=True, warning_count=1)
    dep_res = DependencyResolutionResult(resolved=True, status=DependencyStatus.RESOLVED, execution_order=[1])
    risk_res = RiskAnalysisResult(overall_risk=RiskLevel.MEDIUM, acceptable=True)

    exec_plan = builder.build_execution_plan(plan, val_res, dep_res, risk_res)

    assert exec_plan.readiness == ExecutionReadiness.READY_WITH_WARNINGS


def test_not_ready(builder: ExecutionPlanBuilder) -> None:
    """Verifies NOT_READY readiness classification when plan validation fails."""
    plan = ActionPlan(request="test")
    val_res = PlanValidationResult(valid=False, error_count=1)
    dep_res = DependencyResolutionResult(resolved=True, status=DependencyStatus.RESOLVED)
    risk_res = RiskAnalysisResult(overall_risk=RiskLevel.NONE, acceptable=True)

    exec_plan = builder.build_execution_plan(plan, val_res, dep_res, risk_res)

    assert exec_plan.readiness == ExecutionReadiness.NOT_READY


def test_blocked(builder: ExecutionPlanBuilder) -> None:
    """Verifies BLOCKED readiness classification on dependency failures or high/critical risks."""
    plan = ActionPlan(request="test")
    val_res = PlanValidationResult(valid=True)
    dep_res = DependencyResolutionResult(resolved=False, status=DependencyStatus.CYCLIC)
    risk_res = RiskAnalysisResult(overall_risk=RiskLevel.CRITICAL, acceptable=False)

    exec_plan = builder.build_execution_plan(plan, val_res, dep_res, risk_res)

    assert exec_plan.readiness == ExecutionReadiness.BLOCKED


def test_execution_order_propagation(builder: ExecutionPlanBuilder) -> None:
    """Verifies execution_order is populated from DependencyResolutionResult."""
    dep_res = DependencyResolutionResult(resolved=True, status=DependencyStatus.RESOLVED, execution_order=[2, 1, 3])
    exec_plan = builder.build_execution_plan(dependency_result=dep_res)

    assert exec_plan.execution_order == [2, 1, 3]


def test_immutable_models(builder: ExecutionPlanBuilder) -> None:
    """Verifies ExecutionPlan model is an immutable snapshot."""
    exec_plan = builder.build_execution_plan()
    with pytest.raises((TypeError, ValidationError)):
        exec_plan.readiness = ExecutionReadiness.BLOCKED


def test_metadata(builder: ExecutionPlanBuilder) -> None:
    """Verifies metadata propagation into ExecutionPlan."""
    plan = ActionPlan(request="test", metadata={"user": "u1"})
    exec_plan = builder.build_execution_plan(plan, metadata={"extra": "data"})

    assert exec_plan.metadata["user"] == "u1"
    assert exec_plan.metadata["extra"] == "data"


def test_configuration_injection() -> None:
    """Verifies ExecutionPlanBuilderConfig custom settings."""
    cfg = ExecutionPlanBuilderConfig(include_metadata=False)
    epb = ExecutionPlanBuilder(config=cfg)

    plan = ActionPlan(request="test", metadata={"secret": "hide"})
    exec_plan = epb.build_execution_plan(plan)

    assert "secret" not in exec_plan.metadata


def test_malformed_inputs(builder: ExecutionPlanBuilder) -> None:
    """Verifies None parameters create default valid ExecutionPlan cleanly."""
    exec_plan = builder.build_execution_plan(None, None, None, None)
    assert isinstance(exec_plan, ExecutionPlan)
    assert exec_plan.readiness == ExecutionReadiness.READY


def test_graceful_failures(builder: ExecutionPlanBuilder) -> None:
    """Verifies builder hooks throwing exceptions do not crash execution plan building."""
    def faulty_hook(meta: dict) -> dict:
        raise RuntimeError("Hook exception!")

    builder.register_builder_hook("faulty", faulty_hook)
    exec_plan = builder.build_execution_plan()

    assert isinstance(exec_plan, ExecutionPlan)


def test_registry_clearing(builder: ExecutionPlanBuilder) -> None:
    """Verifies clear_builder_hooks removes all custom hooks."""
    builder.register_builder_hook("h1", lambda m: m)
    builder.clear_builder_hooks()
    assert builder.list_builder_hooks() == []


def test_listing(builder: ExecutionPlanBuilder) -> None:
    """Verifies list_builder_hooks returns metadata list."""
    builder.register_builder_hook("h1", lambda m: m, priority=5, metadata={"info": "test"})
    hooks = builder.list_builder_hooks()

    assert len(hooks) == 1
    assert hooks[0]["hook_id"] == "h1"
    assert hooks[0]["priority"] == 5


def test_thread_safety() -> None:
    """Verifies thread safety under concurrent hook registrations and plan builds."""
    epb = ExecutionPlanBuilder()

    def worker(idx: int) -> None:
        epb.register_builder_hook(f"h_{idx}", lambda m: m)
        epb.build_execution_plan()

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker, i) for i in range(50)]
        for f in futures:
            f.result()

    exec_plan = epb.build_execution_plan()
    assert isinstance(exec_plan, ExecutionPlan)


def test_singleton_compatibility() -> None:
    """Verifies ExecutionPlanBuilder operational behavior."""
    b1 = ExecutionPlanBuilder()
    b2 = ExecutionPlanBuilder()
    assert isinstance(b1, ExecutionPlanBuilder)
    assert isinstance(b2, ExecutionPlanBuilder)


def test_backward_compatibility() -> None:
    """Verifies backward compatibility with pre-existing planning exports."""
    from brain.planning import (
        ExecutionPlan,
        ExecutionPlanBuilder,
        ExecutionPlanBuilderConfig,
        ExecutionReadiness,
        ExecutionStage,
    )

    epb = ExecutionPlanBuilder()
    assert epb is not None


def test_integration_with_risk_analyzer(builder: ExecutionPlanBuilder) -> None:
    """Verifies building ExecutionPlan from full planning pipeline outputs."""
    planner = ActionPlanner()
    validator = PlanValidator()
    resolver = DependencyResolver()
    analyzer = RiskAnalyzer()
    rcb = ReasoningContextBuilder()

    ctx = rcb.build_context("delete folder temp", goal_result=GoalExtractionResult(goal_type=GoalType.DELETE_FOLDER))
    plan = planner.create_plan(ctx)
    val_res = validator.validate_plan(plan)
    dep_res = resolver.resolve_dependencies(plan)
    risk_res = analyzer.analyze_risks(plan, val_res, dep_res)

    exec_plan = builder.build_execution_plan(plan, val_res, dep_res, risk_res)

    assert exec_plan.readiness == ExecutionReadiness.BLOCKED
    assert exec_plan.risk_result.overall_risk == RiskLevel.CRITICAL


def test_logging(caplog: pytest.LogCaptureFixture, builder: ExecutionPlanBuilder) -> None:
    """Verifies required event log outputs."""
    with caplog.at_level(logging.INFO):
        builder.register_builder_hook("h1", lambda m: m)
        builder.build_execution_plan()
        builder.remove_builder_hook("h1")
        builder.clear_builder_hooks()

    assert "Builder Hook Registered" in caplog.text
    assert "Execution Plan Built" in caplog.text
    assert "Builder Hook Removed" in caplog.text
    assert "Builder Hooks Cleared" in caplog.text


def test_timestamps(builder: ExecutionPlanBuilder) -> None:
    """Verifies created_at timestamp is generated automatically."""
    exec_plan = builder.build_execution_plan()
    assert isinstance(exec_plan.created_at, datetime)


def test_regression_validation(builder: ExecutionPlanBuilder) -> None:
    """Verifies end-to-end task planning pipeline execution plan creation."""
    planner = ActionPlanner()
    validator = PlanValidator()
    resolver = DependencyResolver()
    analyzer = RiskAnalyzer()
    rcb = ReasoningContextBuilder()

    ctx = rcb.build_context("move photos to Archive", goal_result=GoalExtractionResult(goal_type=GoalType.MOVE_FILES))
    plan = planner.create_plan(ctx)
    val_res = validator.validate_plan(plan)
    dep_res = resolver.resolve_dependencies(plan)
    risk_res = analyzer.analyze_risks(plan, val_res, dep_res)

    exec_plan = builder.build_execution_plan(plan, val_res, dep_res, risk_res)

    assert exec_plan.request == "move photos to Archive"
    assert exec_plan.execution_order == [1, 2, 3]


def test_configuration_validation() -> None:
    """Verifies ExecutionPlanBuilderConfig properties."""
    cfg = ExecutionPlanBuilderConfig(strict_build=False, include_metadata=False, include_diagnostics=False)
    epb = ExecutionPlanBuilder(config=cfg)

    assert epb.config.strict_build is False
    assert epb.config.include_metadata is False
    assert epb.config.include_diagnostics is False


def test_builder_hooks(builder: ExecutionPlanBuilder) -> None:
    """Verifies registered builder hooks execute and enrich metadata during build_execution_plan."""
    def enrich_hook(meta: dict) -> dict:
        meta["built_by"] = "test_hook"
        return meta

    builder.register_builder_hook("enrich", enrich_hook)
    exec_plan = builder.build_execution_plan(metadata={"orig": True})

    assert exec_plan.metadata["orig"] is True
    assert exec_plan.metadata["built_by"] == "test_hook"


def test_diagnostics(builder: ExecutionPlanBuilder) -> None:
    """Verifies execution stage and readiness properties."""
    exec_plan = builder.build_execution_plan()
    assert exec_plan.current_stage == ExecutionStage.READY_FOR_EXECUTION
    assert exec_plan.readiness == ExecutionReadiness.READY
