"""Unit tests for ReasoningContextBuilder (Phase 9.2.5)."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import logging
import pytest
from pydantic import ValidationError

from brain.reasoning import (
    ConstraintAnalysisResult,
    ConstraintAnalyzer,
    ConstraintType,
    GoalExtractionResult,
    GoalExtractor,
    GoalType,
    IntentAnalysisResult,
    IntentAnalyzer,
    IntentCategory,
    ReasoningContext,
    ReasoningContextBuilder,
    ReasoningContextBuilderConfig,
    ReasoningEngine,
    ReasoningStrategy,
    ReasoningStrategySelector,
    StrategySelectionResult,
)


@pytest.fixture
def builder() -> ReasoningContextBuilder:
    """Fixture providing a fresh ReasoningContextBuilder instance."""
    return ReasoningContextBuilder()


def test_context_construction(builder: ReasoningContextBuilder) -> None:
    """Verifies context construction combining all stage reasoning outputs."""
    intent_res = IntentAnalysisResult(intent=IntentCategory.FILE_MANAGEMENT)
    strat_res = StrategySelectionResult(strategy=ReasoningStrategy.FILE_REASONING)
    goal_res = GoalExtractionResult(goal_type=GoalType.MOVE_FILES)
    const_res = ConstraintAnalysisResult(constraint_count=1)

    ctx = builder.build_context(
        request="move report.pdf to Archive",
        intent_result=intent_res,
        strategy_result=strat_res,
        goal_result=goal_res,
        constraint_result=const_res,
        metadata={"session_id": "s1"},
    )

    assert isinstance(ctx, ReasoningContext)
    assert ctx.request == "move report.pdf to Archive"
    assert ctx.intent.intent == IntentCategory.FILE_MANAGEMENT
    assert ctx.strategy.strategy == ReasoningStrategy.FILE_REASONING
    assert ctx.goal.goal_type == GoalType.MOVE_FILES
    assert ctx.constraints.constraint_count == 1
    assert ctx.metadata == {"session_id": "s1"}


def test_immutable_context(builder: ReasoningContextBuilder) -> None:
    """Verifies ReasoningContext model is an immutable snapshot."""
    ctx = builder.build_context("test request")
    with pytest.raises((TypeError, ValidationError)):
        ctx.request = "MUTATED"


def test_metadata_propagation(builder: ReasoningContextBuilder) -> None:
    """Verifies metadata dictionary propagation into context model."""
    ctx = builder.build_context("req", metadata={"user": "u123", "client": "v1"})
    assert ctx.metadata == {"user": "u123", "client": "v1"}


def test_timestamp_creation(builder: ReasoningContextBuilder) -> None:
    """Verifies timestamp created_at field is generated automatically."""
    ctx = builder.build_context("req")
    assert isinstance(ctx.created_at, datetime)


def test_empty_context(builder: ReasoningContextBuilder) -> None:
    """Verifies building a context with no arguments returns a default valid context."""
    ctx = builder.build_context()
    assert isinstance(ctx, ReasoningContext)
    assert ctx.request == ""
    assert ctx.intent.intent == IntentCategory.UNKNOWN


def test_invalid_input(builder: ReasoningContextBuilder) -> None:
    """Verifies non-string request and non-model parameters produce a clean default context without raising exceptions."""
    ctx = builder.build_context(request=12345, intent_result="invalid", strategy_result=99)
    assert isinstance(ctx, ReasoningContext)
    assert ctx.request == ""
    assert ctx.intent.intent == IntentCategory.UNKNOWN


def test_hook_registration(builder: ReasoningContextBuilder) -> None:
    """Verifies context hook registration."""
    def sample_hook(meta: dict) -> dict:
        meta["hooked"] = True
        return meta

    res = builder.register_context_hook("h1", sample_hook, priority=10)
    assert res is True

    hooks = builder.list_context_hooks()
    assert len(hooks) == 1
    assert hooks[0]["hook_id"] == "h1"


def test_hook_removal(builder: ReasoningContextBuilder) -> None:
    """Verifies removing a registered context hook."""
    builder.register_context_hook("h_rem", lambda m: m)
    removed = builder.remove_context_hook("h_rem")
    assert removed is True
    assert builder.list_context_hooks() == []


def test_hook_execution(builder: ReasoningContextBuilder) -> None:
    """Verifies registered hooks execute and enrich context metadata during build_context."""
    def enrich_hook(meta: dict) -> dict:
        meta["processed_by_hook"] = True
        return meta

    builder.register_context_hook("enrich", enrich_hook)
    ctx = builder.build_context("test req", metadata={"initial": True})

    assert ctx.metadata["initial"] is True
    assert ctx.metadata["processed_by_hook"] is True


def test_duplicate_hooks(builder: ReasoningContextBuilder) -> None:
    """Verifies re-registering a hook with same hook_id replaces existing entry."""
    builder.register_context_hook("h_dup", lambda m: m, priority=1)
    builder.register_context_hook("h_dup", lambda m: m, priority=100)

    hooks = builder.list_context_hooks()
    assert len(hooks) == 1
    assert hooks[0]["priority"] == 100


def test_hook_ordering(builder: ReasoningContextBuilder) -> None:
    """Verifies context hooks execute in order of priority descending."""
    execution_order = []

    def h_low(meta: dict) -> dict:
        execution_order.append("low")
        return meta

    def h_high(meta: dict) -> dict:
        execution_order.append("high")
        return meta

    builder.register_context_hook("low", h_low, priority=1)
    builder.register_context_hook("high", h_high, priority=100)
    builder.build_context("req")

    assert execution_order == ["high", "low"]


def test_configuration_injection() -> None:
    """Verifies custom ReasoningContextBuilderConfig configuration."""
    cfg = ReasoningContextBuilderConfig(include_metadata=False)
    rcb = ReasoningContextBuilder(config=cfg)

    def hook(meta: dict) -> dict:
        meta["should_not_run"] = True
        return meta

    rcb.register_context_hook("h_ignore", hook)
    ctx = rcb.build_context("req", metadata={"initial": 1})

    assert "should_not_run" not in ctx.metadata


def test_thread_safety() -> None:
    """Verifies thread safety during concurrent hook registrations and context building."""
    rcb = ReasoningContextBuilder()

    def worker(idx: int) -> None:
        rcb.register_context_hook(f"h_worker_{idx}", lambda m: m)
        rcb.build_context(f"req_{idx}")

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker, i) for i in range(50)]
        for f in futures:
            f.result()

    ctx = rcb.build_context("final req")
    assert isinstance(ctx, ReasoningContext)


def test_registry_clearing(builder: ReasoningContextBuilder) -> None:
    """Verifies clear_context_hooks clears all registered hooks."""
    builder.register_context_hook("h1", lambda m: m)
    builder.clear_context_hooks()
    assert builder.list_context_hooks() == []


def test_listing(builder: ReasoningContextBuilder) -> None:
    """Verifies list_context_hooks returns metadata for all registered hooks."""
    builder.register_context_hook("h1", lambda m: m, priority=5, metadata={"info": "test"})
    hooks = builder.list_context_hooks()
    assert len(hooks) == 1
    assert hooks[0]["hook_id"] == "h1"
    assert hooks[0]["priority"] == 5


def test_graceful_failures(builder: ReasoningContextBuilder) -> None:
    """Verifies context hooks throwing exceptions do not crash context construction."""
    def faulty_hook(meta: dict) -> dict:
        raise ValueError("Hook failed!")

    builder.register_context_hook("faulty", faulty_hook)
    ctx = builder.build_context("test req")
    assert isinstance(ctx, ReasoningContext)


def test_integration_with_intent_analyzer() -> None:
    """Verifies building context with IntentAnalyzer output."""
    intent_an = IntentAnalyzer()
    rcb = ReasoningContextBuilder()

    intent_res = intent_an.analyze("move report.pdf")
    ctx = rcb.build_context("move report.pdf", intent_result=intent_res)

    assert ctx.intent.intent == IntentCategory.FILE_MANAGEMENT


def test_integration_with_strategy_selector() -> None:
    """Verifies building context with StrategySelector output."""
    intent_an = IntentAnalyzer()
    strat_sel = ReasoningStrategySelector()
    rcb = ReasoningContextBuilder()

    i_res = intent_an.analyze("search for pdfs")
    s_res = strat_sel.select_strategy(i_res)
    ctx = rcb.build_context("search for pdfs", intent_result=i_res, strategy_result=s_res)

    assert ctx.strategy.strategy == ReasoningStrategy.SEARCH_REASONING


def test_integration_with_goal_extractor() -> None:
    """Verifies building context with GoalExtractor output."""
    intent_an = IntentAnalyzer()
    strat_sel = ReasoningStrategySelector()
    goal_ext = GoalExtractor()
    rcb = ReasoningContextBuilder()

    req = "create folder ProjectX"
    i_res = intent_an.analyze(req)
    s_res = strat_sel.select_strategy(i_res)
    g_res = goal_ext.extract_goals(req, i_res, s_res)
    ctx = rcb.build_context(req, i_res, s_res, g_res)

    assert ctx.goal.goal_type == GoalType.CREATE_FOLDER


def test_integration_with_constraint_analyzer() -> None:
    """Verifies building context with ConstraintAnalyzer output."""
    intent_an = IntentAnalyzer()
    strat_sel = ReasoningStrategySelector()
    goal_ext = GoalExtractor()
    ca = ConstraintAnalyzer()
    rcb = ReasoningContextBuilder()

    req = "copy photo.png to Desktop larger than 5MB"
    i_res = intent_an.analyze(req)
    s_res = strat_sel.select_strategy(i_res)
    g_res = goal_ext.extract_goals(req, i_res, s_res)
    c_res = ca.analyze_constraints(req, i_res, s_res, g_res)
    ctx = rcb.build_context(req, i_res, s_res, g_res, c_res)

    assert ctx.constraints.constraint_count >= 1


def test_singleton_compatibility() -> None:
    """Verifies ReasoningContextBuilder operates cleanly as a shared instance."""
    b1 = ReasoningContextBuilder()
    b2 = ReasoningContextBuilder()
    assert isinstance(b1, ReasoningContextBuilder)
    assert isinstance(b2, ReasoningContextBuilder)


def test_backward_compatibility() -> None:
    """Verifies backward compatibility with pre-existing brain.reasoning exports."""
    from brain.reasoning import (
        ConstraintAnalyzer,
        GoalExtractor,
        IntentAnalyzer,
        ObjectiveBuilder,
        PriorityManager,
        ReasoningContext,
        ReasoningContextBuilder,
        ReasoningEngine,
        ReasoningStrategySelector,
    )

    rcb = ReasoningContextBuilder()
    assert rcb is not None


def test_regression_validation() -> None:
    """Verifies end-to-end multi-stage reasoning pipeline context build."""
    intent_an = IntentAnalyzer()
    strat_sel = ReasoningStrategySelector()
    goal_ext = GoalExtractor()
    ca = ConstraintAnalyzer()
    rcb = ReasoningContextBuilder()

    req = "delete temp files before January"
    i_res = intent_an.analyze(req)
    s_res = strat_sel.select_strategy(i_res)
    g_res = goal_ext.extract_goals(req, i_res, s_res)
    c_res = ca.analyze_constraints(req, i_res, s_res, g_res)
    ctx = rcb.build_context(req, i_res, s_res, g_res, c_res, metadata={"pipeline": "v1"})

    assert ctx.request == req
    assert ctx.intent.intent == IntentCategory.FILE_MANAGEMENT
    assert ctx.strategy.strategy == ReasoningStrategy.FILE_REASONING
    assert ctx.goal.goal_type == GoalType.DELETE_FILES
    assert ctx.constraints.constraint_count >= 1
    assert ctx.metadata == {"pipeline": "v1"}


def test_configuration_validation() -> None:
    """Verifies ReasoningContextBuilderConfig properties."""
    cfg = ReasoningContextBuilderConfig(include_metadata=True, validate_components=False, strict_building=False)
    rcb = ReasoningContextBuilder(config=cfg)

    assert rcb.config.include_metadata is True
    assert rcb.config.validate_components is False
    assert rcb.config.strict_building is False
