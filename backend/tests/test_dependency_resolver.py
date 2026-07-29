"""Unit tests for DependencyResolver (Phase 9.3.3)."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import logging
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from core.intents import Intent
from brain.planning import (
    ActionDependency,
    ActionPlan,
    ActionPlanner,
    ActionStep,
    ActionType,
    DependencyResolutionResult,
    DependencyResolver,
    DependencyResolverConfig,
    DependencyStatus,
    DependencyType,
    ExecutionDependency,
    ExecutionSequence,
    ExecutionStep,
    PlanValidator,
)
from brain.reasoning import (
    GoalExtractionResult,
    GoalType,
    ReasoningContextBuilder,
)


@pytest.fixture
def resolver() -> DependencyResolver:
    """Fixture providing a fresh DependencyResolver instance."""
    return DependencyResolver()


def test_dependency_rule_registration(resolver: DependencyResolver) -> None:
    """Verifies registering a custom dependency rule."""
    def rule_func(plan: ActionPlan) -> list[ActionDependency]:
        return [ActionDependency(source_step=1, target_step=2, dependency_type=DependencyType.SOFT)]

    res = resolver.register_dependency_rule("r1", rule_func)
    assert res is True

    rules = resolver.list_dependency_rules()
    assert len(rules) == 1
    assert rules[0]["rule_id"] == "r1"


def test_dependency_rule_removal(resolver: DependencyResolver) -> None:
    """Verifies removing a registered custom dependency rule."""
    resolver.register_dependency_rule("r_rem", lambda p: [])
    removed = resolver.remove_dependency_rule("r_rem")
    assert removed is True
    assert resolver.list_dependency_rules() == []


def test_dependency_detection(resolver: DependencyResolver) -> None:
    """Verifies automatic dependency detection between LOCATE_FILES and MOVE_FILES steps."""
    step1 = ActionStep(step_number=1, action_type=ActionType.LOCATE_FILES, description="Locate")
    step2 = ActionStep(step_number=2, action_type=ActionType.MOVE_FILES, description="Move")
    plan = ActionPlan(request="test", steps=[step1, step2], step_count=2)

    res = resolver.resolve_dependencies(plan)
    assert isinstance(res, DependencyResolutionResult)
    assert res.resolved is True
    assert res.status == DependencyStatus.RESOLVED
    assert len(res.dependencies) == 1
    assert res.dependencies[0].source_step == 1
    assert res.dependencies[0].target_step == 2


def test_execution_ordering(resolver: DependencyResolver) -> None:
    """Verifies topological sorting produces correct execution ordering."""
    step1 = ActionStep(step_number=1, action_type=ActionType.LOCATE_FILES, description="Locate")
    step2 = ActionStep(step_number=2, action_type=ActionType.CREATE_FOLDER, description="Create")
    step3 = ActionStep(step_number=3, action_type=ActionType.MOVE_FILES, description="Move")
    plan = ActionPlan(request="test", steps=[step1, step2, step3], step_count=3)

    res = resolver.resolve_dependencies(plan)
    assert res.execution_order == [1, 2, 3]


def test_dependency_chains(resolver: DependencyResolver) -> None:
    """Verifies handling a multi-step dependency chain."""
    step1 = ActionStep(step_number=1, action_type=ActionType.LOCATE_FILES, description="Locate")
    step2 = ActionStep(step_number=2, action_type=ActionType.MOVE_FILES, description="Move")
    step3 = ActionStep(step_number=3, action_type=ActionType.DELETE_FILES, description="Delete")
    plan = ActionPlan(request="test", steps=[step1, step2, step3], step_count=3)

    res = resolver.resolve_dependencies(plan)
    assert len(res.dependencies) >= 2


def test_cyclic_dependencies(resolver: DependencyResolver) -> None:
    """Verifies detection of cyclic dependencies produces CYCLIC status."""
    def cyclic_rule(plan: ActionPlan) -> list[ActionDependency]:
        return [
            ActionDependency(source_step=1, target_step=2),
            ActionDependency(source_step=2, target_step=1),
        ]

    resolver.register_dependency_rule("cycle", cyclic_rule)
    step1 = ActionStep(step_number=1, action_type=ActionType.RESPOND, description="R1")
    step2 = ActionStep(step_number=2, action_type=ActionType.RESPOND, description="R2")
    plan = ActionPlan(request="test", steps=[step1, step2], step_count=2)

    res = resolver.resolve_dependencies(plan)
    assert res.resolved is False
    assert res.status == DependencyStatus.CYCLIC
    assert len(res.conflicts) >= 1


def test_unresolved_dependencies(resolver: DependencyResolver) -> None:
    """Verifies non-ActionPlan input produces UNRESOLVED status."""
    res = resolver.resolve_dependencies("invalid_input")  # type: ignore
    assert res.resolved is False
    assert res.status == DependencyStatus.UNRESOLVED


def test_duplicate_dependencies(resolver: DependencyResolver) -> None:
    """Verifies duplicate dependency relationships are deduplicated."""
    def dup_rule(plan: ActionPlan) -> list[ActionDependency]:
        return [
            ActionDependency(source_step=1, target_step=2),
            ActionDependency(source_step=1, target_step=2),
        ]

    resolver.register_dependency_rule("dup", dup_rule)
    step1 = ActionStep(step_number=1, action_type=ActionType.RESPOND, description="R1")
    step2 = ActionStep(step_number=2, action_type=ActionType.RESPOND, description="R2")
    plan = ActionPlan(request="test", steps=[step1, step2], step_count=2)

    res = resolver.resolve_dependencies(plan)
    assert len(res.dependencies) == 1


def test_malformed_plans(resolver: DependencyResolver) -> None:
    """Verifies None plan input handling without raising exceptions."""
    res = resolver.resolve_dependencies(None)
    assert res.resolved is False
    assert res.status == DependencyStatus.UNRESOLVED


def test_immutable_models(resolver: DependencyResolver) -> None:
    """Verifies ActionDependency and DependencyResolutionResult models are immutable snapshots."""
    res = resolver.resolve_dependencies(None)
    with pytest.raises((TypeError, ValidationError)):
        res.resolved = True

    dep = ActionDependency(source_step=1, target_step=2)
    with pytest.raises((TypeError, ValidationError)):
        dep.source_step = 99


def test_metadata(resolver: DependencyResolver) -> None:
    """Verifies metadata propagation into resolution result."""
    plan = ActionPlan(request="test", metadata={"context_id": "c1"})
    res = resolver.resolve_dependencies(plan)

    assert res.metadata == {"context_id": "c1"}


def test_configuration_injection() -> None:
    """Verifies DependencyResolverConfig custom settings."""
    cfg = DependencyResolverConfig(maximum_dependencies=1)
    dr = DependencyResolver(config=cfg)

    step1 = ActionStep(step_number=1, action_type=ActionType.LOCATE_FILES, description="Locate")
    step2 = ActionStep(step_number=2, action_type=ActionType.MOVE_FILES, description="Move")
    step3 = ActionStep(step_number=3, action_type=ActionType.DELETE_FILES, description="Delete")
    plan = ActionPlan(request="test", steps=[step1, step2, step3], step_count=3)

    res = dr.resolve_dependencies(plan)
    assert len(res.dependencies) == 1


def test_registry_clearing(resolver: DependencyResolver) -> None:
    """Verifies clear_dependency_rules removes all custom rules."""
    resolver.register_dependency_rule("r1", lambda p: [])
    resolver.clear_dependency_rules()
    assert resolver.list_dependency_rules() == []


def test_listing(resolver: DependencyResolver) -> None:
    """Verifies list_dependency_rules returns metadata list."""
    resolver.register_dependency_rule("r1", lambda p: [], priority=5, metadata={"info": "test"})
    rules = resolver.list_dependency_rules()

    assert len(rules) == 1
    assert rules[0]["rule_id"] == "r1"
    assert rules[0]["priority"] == 5


def test_thread_safety() -> None:
    """Verifies thread safety under concurrent rule registrations and resolutions."""
    dr = DependencyResolver()
    plan = ActionPlan(request="req")

    def worker(idx: int) -> None:
        dr.register_dependency_rule(f"r_{idx}", lambda p: [])
        dr.resolve_dependencies(plan)

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker, i) for i in range(50)]
        for f in futures:
            f.result()

    res = dr.resolve_dependencies(plan)
    assert isinstance(res, DependencyResolutionResult)


def test_graceful_failures(resolver: DependencyResolver) -> None:
    """Verifies custom rules raising exceptions do not crash resolution."""
    def faulty_rule(p: ActionPlan) -> list[ActionDependency]:
        raise RuntimeError("Rule error!")

    resolver.register_dependency_rule("faulty", faulty_rule)
    plan = ActionPlan(request="req")
    res = resolver.resolve_dependencies(plan)

    assert isinstance(res, DependencyResolutionResult)


def test_singleton_compatibility() -> None:
    """Verifies DependencyResolver operational behavior."""
    r1 = DependencyResolver()
    r2 = DependencyResolver()
    assert isinstance(r1, DependencyResolver)
    assert isinstance(r2, DependencyResolver)


def test_backward_compatibility() -> None:
    """Verifies 100% backward compatibility with legacy resolve_order method."""
    resolver = DependencyResolver()
    step_a = ExecutionStep(step_id="step_a", intent=Intent.SEARCH_FILE, parameters={})
    step_b = ExecutionStep(step_id="step_b", intent=Intent.OPEN_FILE, parameters={})

    dep = ExecutionDependency(step_id="step_b", depends_on=["step_a"])
    sequence = ExecutionSequence(steps=[step_a, step_b], dependencies=[dep])

    ordered = resolver.resolve_order(sequence)
    assert [s.step_id for s in ordered] == ["step_a", "step_b"]


def test_integration_with_action_planner(resolver: DependencyResolver) -> None:
    """Verifies resolving dependencies for ActionPlan generated by ActionPlanner."""
    planner = ActionPlanner()
    builder = ReasoningContextBuilder()
    ctx = builder.build_context("move report.pdf", goal_result=GoalExtractionResult(goal_type=GoalType.MOVE_FILES))
    plan = planner.create_plan(ctx)

    res = resolver.resolve_dependencies(plan)
    assert res.resolved is True
    assert len(res.dependencies) >= 1


def test_integration_with_plan_validator(resolver: DependencyResolver) -> None:
    """Verifies pipeline: ActionPlanner -> PlanValidator -> DependencyResolver."""
    planner = ActionPlanner()
    validator = PlanValidator()
    builder = ReasoningContextBuilder()

    ctx = builder.build_context("copy data", goal_result=GoalExtractionResult(goal_type=GoalType.COPY_FILES))
    plan = planner.create_plan(ctx)
    val_res = validator.validate_plan(plan)
    assert val_res.valid is True

    dep_res = resolver.resolve_dependencies(plan)
    assert dep_res.resolved is True


def test_logging(caplog: pytest.LogCaptureFixture, resolver: DependencyResolver) -> None:
    """Verifies required event log outputs."""
    with caplog.at_level(logging.INFO):
        resolver.register_dependency_rule("r1", lambda p: [])
        resolver.resolve_dependencies(None)
        resolver.remove_dependency_rule("r1")
        resolver.clear_dependency_rules()

    assert "Dependency Rule Registered" in caplog.text
    assert "Dependencies Resolved" in caplog.text
    assert "Dependency Rule Removed" in caplog.text
    assert "Dependency Registry Cleared" in caplog.text


def test_timestamps(resolver: DependencyResolver) -> None:
    """Verifies resolved_at timestamp is generated automatically."""
    res = resolver.resolve_dependencies(None)
    assert isinstance(res.resolved_at, datetime)


def test_regression_validation(resolver: DependencyResolver) -> None:
    """Verifies complex multi-step plan dependency resolution."""
    step1 = ActionStep(step_number=1, action_type=ActionType.CREATE_FOLDER, description="Create")
    step2 = ActionStep(step_number=2, action_type=ActionType.LOCATE_FILES, description="Locate")
    step3 = ActionStep(step_number=3, action_type=ActionType.MOVE_FILES, description="Move")
    plan = ActionPlan(request="test", steps=[step1, step2, step3], step_count=3)

    res = resolver.resolve_dependencies(plan)
    assert res.resolved is True
    assert len(res.dependencies) == 2


def test_configuration_validation() -> None:
    """Verifies DependencyResolverConfig properties."""
    cfg = DependencyResolverConfig(detect_cycles=False, strict_resolution=False, maximum_dependencies=10)
    dr = DependencyResolver(config=cfg)

    assert dr.config.detect_cycles is False
    assert dr.config.strict_resolution is False
    assert dr.config.maximum_dependencies == 10
