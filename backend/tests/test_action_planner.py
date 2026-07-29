"""Unit tests for ActionPlanner (Phase 9.3.1)."""

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
    ActionPlannerConfig,
    ActionPriority,
    ActionStep,
    ActionType,
)
from brain.reasoning import (
    GoalExtractionResult,
    GoalType,
    ReasoningContext,
    ReasoningContextBuilder,
)


@pytest.fixture
def planner() -> ActionPlanner:
    """Fixture providing a fresh ActionPlanner instance."""
    return ActionPlanner()


def test_rule_registration(planner: ActionPlanner) -> None:
    """Verifies registering custom plan rules for a GoalType."""
    custom_steps = [
        {"action_type": ActionType.SEARCH, "description": "Custom Search", "priority": ActionPriority.HIGH}
    ]
    res = planner.register_plan_rule(GoalType.SEARCH_FILES, custom_steps)
    assert res is True

    rules = planner.list_plan_rules()
    assert GoalType.SEARCH_FILES.value in rules
    assert len(rules[GoalType.SEARCH_FILES.value]) == 1


def test_rule_removal(planner: ActionPlanner) -> None:
    """Verifies removing a plan rule for a GoalType."""
    removed = planner.remove_plan_rule(GoalType.MOVE_FILES)
    assert removed is True

    rules = planner.list_plan_rules()
    assert GoalType.MOVE_FILES.value not in rules


def test_deterministic_planning(planner: ActionPlanner) -> None:
    """Verifies deterministic plan creation matching ReasoningContext goals."""
    builder = ReasoningContextBuilder()
    ctx = builder.build_context("move pdfs", goal_result=GoalExtractionResult(goal_type=GoalType.MOVE_FILES))

    plan = planner.create_plan(ctx)
    assert isinstance(plan, ActionPlan)
    assert plan.request == "move pdfs"
    assert plan.goal == GoalType.MOVE_FILES.value
    assert plan.step_count == 3
    assert plan.steps[0].action_type == ActionType.LOCATE_FILES
    assert plan.steps[1].action_type == ActionType.CREATE_FOLDER
    assert plan.steps[2].action_type == ActionType.MOVE_FILES


def test_every_action_type() -> None:
    """Verifies all 12 ActionType enum values are accessible."""
    action_types = set(ActionType)
    assert len(action_types) == 12
    assert ActionType.LOCATE_FILES in action_types
    assert ActionType.MOVE_FILES in action_types
    assert ActionType.COPY_FILES in action_types
    assert ActionType.DELETE_FILES in action_types
    assert ActionType.RENAME_FILES in action_types
    assert ActionType.OPEN_FILE in action_types
    assert ActionType.CREATE_FOLDER in action_types
    assert ActionType.DELETE_FOLDER in action_types
    assert ActionType.SEARCH in action_types
    assert ActionType.RESPOND in action_types
    assert ActionType.SCHEDULE in action_types
    assert ActionType.NO_ACTION in action_types


def test_step_ordering(planner: ActionPlanner) -> None:
    """Verifies step_number values in ActionPlan are sequential starting from 1."""
    builder = ReasoningContextBuilder()
    ctx = builder.build_context("copy data", goal_result=GoalExtractionResult(goal_type=GoalType.COPY_FILES))

    plan = planner.create_plan(ctx)
    for idx, step in enumerate(plan.steps, start=1):
        assert step.step_number == idx


def test_immutable_models(planner: ActionPlanner) -> None:
    """Verifies ActionPlan and ActionStep models are immutable snapshots."""
    builder = ReasoningContextBuilder()
    ctx = builder.build_context("test")
    plan = planner.create_plan(ctx)

    with pytest.raises((TypeError, ValidationError)):
        plan.request = "MUTATED"

    if plan.steps:
        with pytest.raises((TypeError, ValidationError)):
            plan.steps[0].description = "MUTATED"


def test_metadata(planner: ActionPlanner) -> None:
    """Verifies metadata propagation from ReasoningContext to ActionPlan."""
    builder = ReasoningContextBuilder()
    ctx = builder.build_context("test", metadata={"session": "s123"})
    plan = planner.create_plan(ctx)

    assert plan.metadata == {"session": "s123"}


def test_configuration_injection() -> None:
    """Verifies ActionPlannerConfig maximum_steps enforcement."""
    cfg = ActionPlannerConfig(maximum_steps=1)
    ap = ActionPlanner(config=cfg)

    builder = ReasoningContextBuilder()
    ctx = builder.build_context("move files", goal_result=GoalExtractionResult(goal_type=GoalType.MOVE_FILES))

    plan = ap.create_plan(ctx)
    assert plan.step_count == 1


def test_invalid_input(planner: ActionPlanner) -> None:
    """Verifies passing invalid/non-ReasoningContext input produces fallback NO_ACTION plan cleanly."""
    plan = planner.create_plan("invalid_type")  # type: ignore
    assert isinstance(plan, ActionPlan)
    assert plan.step_count == 1
    assert plan.steps[0].action_type == ActionType.NO_ACTION


def test_empty_context(planner: ActionPlanner) -> None:
    """Verifies passing None context produces fallback NO_ACTION plan cleanly."""
    plan = planner.create_plan(None)
    assert isinstance(plan, ActionPlan)
    assert plan.step_count == 1
    assert plan.steps[0].action_type == ActionType.NO_ACTION


def test_duplicate_rules(planner: ActionPlanner) -> None:
    """Verifies registering a plan rule for an existing GoalType updates the template."""
    new_steps = [{"action_type": ActionType.SEARCH, "description": "New Search Rule"}]
    planner.register_plan_rule(GoalType.SEARCH_FILES, new_steps)

    rules = planner.list_plan_rules()
    assert len(rules[GoalType.SEARCH_FILES.value]) == 1
    assert rules[GoalType.SEARCH_FILES.value][0]["description"] == "New Search Rule"


def test_thread_safety() -> None:
    """Verifies thread safety under concurrent plan rule registrations and plan creations."""
    ap = ActionPlanner()
    builder = ReasoningContextBuilder()
    ctx = builder.build_context("req")

    def worker(idx: int) -> None:
        ap.register_plan_rule(GoalType.SEARCH_FILES, [{"action_type": ActionType.SEARCH, "description": f"Rule {idx}"}])
        ap.create_plan(ctx)

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker, i) for i in range(50)]
        for f in futures:
            f.result()

    plan = ap.create_plan(ctx)
    assert isinstance(plan, ActionPlan)


def test_registry_clearing(planner: ActionPlanner) -> None:
    """Verifies clear_plan_rules removes all rule templates."""
    planner.clear_plan_rules()
    assert planner.list_plan_rules() == {}


def test_listing(planner: ActionPlanner) -> None:
    """Verifies list_plan_rules returns dictionary of goal type string keys and step lists."""
    rules = planner.list_plan_rules()
    assert isinstance(rules, dict)
    assert GoalType.MOVE_FILES.value in rules


def test_graceful_failures(planner: ActionPlanner) -> None:
    """Verifies graceful handling when an unregistered GoalType is passed."""
    planner.remove_plan_rule(GoalType.SCHEDULE_TASK)
    builder = ReasoningContextBuilder()
    ctx = builder.build_context("schedule", goal_result=GoalExtractionResult(goal_type=GoalType.SCHEDULE_TASK))

    plan = planner.create_plan(ctx)
    assert plan.step_count == 1
    assert plan.steps[0].action_type == ActionType.NO_ACTION


def test_singleton_compatibility() -> None:
    """Verifies ActionPlanner instance operational behavior."""
    p1 = ActionPlanner()
    p2 = ActionPlanner()
    assert isinstance(p1, ActionPlanner)
    assert isinstance(p2, ActionPlanner)


def test_backward_compatibility() -> None:
    """Verifies backward compatibility with existing brain.planning exports."""
    from brain.planning import (
        ActionPlan,
        ActionPlanner,
        ActionPlannerConfig,
        ActionPriority,
        ActionStep,
        ActionType,
        PlanBuilder,
        TaskPlanner,
    )

    ap = ActionPlanner()
    assert ap is not None


def test_integration_with_reasoning_context(planner: ActionPlanner) -> None:
    """Verifies creating plan directly from ReasoningContext."""
    builder = ReasoningContextBuilder()
    ctx = builder.build_context("delete folder temp", goal_result=GoalExtractionResult(goal_type=GoalType.DELETE_FOLDER))

    plan = planner.create_plan(ctx)
    assert plan.goal == GoalType.DELETE_FOLDER.value
    assert plan.steps[0].action_type == ActionType.DELETE_FOLDER


def test_logging(caplog: pytest.LogCaptureFixture, planner: ActionPlanner) -> None:
    """Verifies required event log outputs."""
    with caplog.at_level(logging.INFO):
        planner.register_plan_rule(GoalType.SEARCH_FILES, [])
        planner.create_plan(None)
        planner.remove_plan_rule(GoalType.SEARCH_FILES)
        planner.clear_plan_rules()

    assert "Plan Rule Registered" in caplog.text
    assert "Action Plan Created" in caplog.text
    assert "Plan Rule Removed" in caplog.text
    assert "Plan Registry Cleared" in caplog.text


def test_plan_timestamps(planner: ActionPlanner) -> None:
    """Verifies created_at timestamp is generated automatically on ActionPlan."""
    plan = planner.create_plan(None)
    assert isinstance(plan.created_at, datetime)


def test_plan_priorities(planner: ActionPlanner) -> None:
    """Verifies priority levels assigned to action steps."""
    builder = ReasoningContextBuilder()
    ctx = builder.build_context("delete files", goal_result=GoalExtractionResult(goal_type=GoalType.DELETE_FILES))

    plan = planner.create_plan(ctx)
    assert plan.steps[1].priority == ActionPriority.HIGH


def test_regression_validation(planner: ActionPlanner) -> None:
    """Verifies end-to-end reasoning context to action plan pipeline conversion."""
    builder = ReasoningContextBuilder()
    ctx = builder.build_context("rename document.docx", goal_result=GoalExtractionResult(goal_type=GoalType.RENAME_FILES))

    plan = planner.create_plan(ctx)
    assert plan.request == "rename document.docx"
    assert plan.steps[0].action_type == ActionType.LOCATE_FILES
    assert plan.steps[1].action_type == ActionType.RENAME_FILES


def test_configuration_validation() -> None:
    """Verifies ActionPlannerConfig properties."""
    cfg = ActionPlannerConfig(maximum_steps=50, include_metadata=False, strict_planning=False)
    ap = ActionPlanner(config=cfg)

    assert ap.config.maximum_steps == 50
    assert ap.config.include_metadata is False
    assert ap.config.strict_planning is False


def test_no_action_handling(planner: ActionPlanner) -> None:
    """Verifies UNKNOWN goal type produces ActionType.NO_ACTION step."""
    builder = ReasoningContextBuilder()
    ctx = builder.build_context("unknown request", goal_result=GoalExtractionResult(goal_type=GoalType.UNKNOWN))

    plan = planner.create_plan(ctx)
    assert plan.step_count == 1
    assert plan.steps[0].action_type == ActionType.NO_ACTION
