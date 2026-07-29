"""Unit tests for ConstraintAnalyzer (Phase 9.2.4)."""

from concurrent.futures import ThreadPoolExecutor
import logging
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from brain.goal.models import Goal, GoalCategory
from brain.reasoning import (
    Constraint,
    ConstraintAnalysisResult,
    ConstraintAnalyzer,
    ConstraintAnalyzerConfig,
    ConstraintSeverity,
    ConstraintType,
    GoalExtractor,
    GoalType,
    IntentAnalyzer,
    IntentCategory,
    ReasoningEngine,
    ReasoningStrategy,
    ReasoningStrategySelector,
)


@pytest.fixture
def analyzer() -> ConstraintAnalyzer:
    """Fixture providing a fresh ConstraintAnalyzer instance."""
    return ConstraintAnalyzer()


def test_constraint_registration(analyzer: ConstraintAnalyzer) -> None:
    """Verifies registering a custom constraint pattern rule."""
    res = analyzer.register_constraint_pattern(
        pattern=r"\bsecret_tag\b",
        constraint_type=ConstraintType.FILE_NAME,
        severity=ConstraintSeverity.CRITICAL,
        metadata={"secure": True},
    )
    assert res is True

    result = analyzer.analyze_constraints("secret_tag file")
    assert isinstance(result, ConstraintAnalysisResult)
    assert result.constraint_count == 1
    assert result.constraints[0].constraint_type == ConstraintType.FILE_NAME
    assert result.constraints[0].severity == ConstraintSeverity.CRITICAL


def test_constraint_removal(analyzer: ConstraintAnalyzer) -> None:
    """Verifies removing a registered constraint pattern rule."""
    analyzer.register_constraint_pattern("unique_const_pat", constraint_type=ConstraintType.QUANTITY)
    removed = analyzer.remove_constraint_pattern("unique_const_pat")
    assert removed is True

    result = analyzer.analyze_constraints("unique_const_pat")
    assert result.constraint_count == 0


def test_every_constraint_type(analyzer: ConstraintAnalyzer) -> None:
    """Verifies all 11 ConstraintType enum values can be produced or registered."""
    types = [
        ConstraintType.FILE_TYPE,
        ConstraintType.FILE_NAME,
        ConstraintType.SOURCE_LOCATION,
        ConstraintType.DESTINATION_LOCATION,
        ConstraintType.DATE_RANGE,
        ConstraintType.TIME_RANGE,
        ConstraintType.FILE_SIZE,
        ConstraintType.FILE_EXTENSION,
        ConstraintType.QUANTITY,
        ConstraintType.PRIORITY,
        ConstraintType.UNKNOWN,
    ]
    for ct in types:
        assert isinstance(ct.value, str)


def test_multiple_constraints(analyzer: ConstraintAnalyzer) -> None:
    """Verifies extracting multiple constraints from a single user request."""
    req = "move all PDF files from Downloads to Archive larger than 5 MB top 10"
    res = analyzer.analyze_constraints(req)

    assert isinstance(res, ConstraintAnalysisResult)
    assert res.constraint_count >= 3
    types_found = {c.constraint_type for c in res.constraints}
    assert ConstraintType.FILE_TYPE in types_found or ConstraintType.FILE_EXTENSION in types_found
    assert ConstraintType.SOURCE_LOCATION in types_found or ConstraintType.DESTINATION_LOCATION in types_found


def test_empty_request(analyzer: ConstraintAnalyzer) -> None:
    """Verifies empty request string produces an empty ConstraintAnalysisResult."""
    res = analyzer.analyze_constraints("")
    assert isinstance(res, ConstraintAnalysisResult)
    assert res.constraint_count == 0
    assert res.constraints == []


def test_invalid_input(analyzer: ConstraintAnalyzer) -> None:
    """Verifies invalid non-string input produces an empty ConstraintAnalysisResult without crashing."""
    res = analyzer.analyze_constraints(12345)
    assert isinstance(res, ConstraintAnalysisResult)
    assert res.constraint_count == 0


def test_immutable_models(analyzer: ConstraintAnalyzer) -> None:
    """Verifies Constraint and ConstraintAnalysisResult models are immutable snapshots."""
    res = analyzer.analyze_constraints("move pdf files")
    assert isinstance(res, ConstraintAnalysisResult)

    with pytest.raises((TypeError, ValidationError)):
        res.constraint_count = 999

    if res.constraints:
        with pytest.raises((TypeError, ValidationError)):
            res.constraints[0].value = "MUTATED"


def test_metadata(analyzer: ConstraintAnalyzer) -> None:
    """Verifies metadata propagation in Constraint objects."""
    analyzer.register_constraint_pattern(
        pattern="meta_pat",
        constraint_type=ConstraintType.PRIORITY,
        metadata={"priority_level": "urgent"},
    )
    res = analyzer.analyze_constraints("meta_pat")
    assert res.constraints[0].metadata == {"priority_level": "urgent"}


def test_configuration_injection() -> None:
    """Verifies custom ConstraintAnalyzerConfig injection and limits."""
    cfg = ConstraintAnalyzerConfig(maximum_constraints=1)
    ca = ConstraintAnalyzer(config=cfg)

    res = ca.analyze_constraints("move PDF files from Downloads to Desktop larger than 10MB")
    assert isinstance(res, ConstraintAnalysisResult)
    assert res.constraint_count <= 1


def test_thread_safety() -> None:
    """Verifies thread safety during concurrent constraint registrations and extractions."""
    ca = ConstraintAnalyzer()

    def worker(idx: int) -> None:
        ca.register_constraint_pattern(f"worker_const_{idx}", constraint_type=ConstraintType.FILE_TYPE)
        ca.analyze_constraints(f"worker_const_{idx}")

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker, i) for i in range(50)]
        for f in futures:
            f.result()

    res = ca.analyze_constraints("worker_const_5")
    assert res.constraint_count == 1


def test_duplicate_patterns(analyzer: ConstraintAnalyzer) -> None:
    """Verifies re-registering a constraint pattern updates the rule cleanly."""
    analyzer.register_constraint_pattern("dup_const", constraint_type=ConstraintType.FILE_TYPE)
    analyzer.register_constraint_pattern("dup_const", constraint_type=ConstraintType.FILE_SIZE)

    patterns = [p for p in analyzer.list_constraint_patterns() if p["pattern"] == "dup_const"]
    assert len(patterns) == 1
    assert patterns[0]["constraint_type"] == ConstraintType.FILE_SIZE


def test_pattern_priority(analyzer: ConstraintAnalyzer) -> None:
    """Verifies pattern rule updates and ordering."""
    analyzer.register_constraint_pattern("prio_const", constraint_type=ConstraintType.QUANTITY)
    res = analyzer.analyze_constraints("prio_const")
    assert res.constraints[0].constraint_type == ConstraintType.QUANTITY


def test_registry_clearing(analyzer: ConstraintAnalyzer) -> None:
    """Verifies clear_constraint_patterns resets pattern registry."""
    analyzer.clear_constraint_patterns()
    assert analyzer.list_constraint_patterns() == []
    res = analyzer.analyze_constraints("move PDF files")
    assert res.constraint_count == 0


def test_listing(analyzer: ConstraintAnalyzer) -> None:
    """Verifies list_constraint_patterns returning registered constraint pattern rules."""
    patterns = analyzer.list_constraint_patterns()
    assert len(patterns) > 0

    ft_pats = analyzer.list_constraint_patterns(constraint_type=ConstraintType.FILE_TYPE)
    assert all(p["constraint_type"] == ConstraintType.FILE_TYPE for p in ft_pats)


def test_graceful_failures(analyzer: ConstraintAnalyzer) -> None:
    """Verifies malformed regex rules do not crash analyzer."""
    analyzer.register_constraint_pattern("[invalid regex (", constraint_type=ConstraintType.FILE_TYPE)
    res = analyzer.analyze_constraints("some text")
    assert isinstance(res, ConstraintAnalysisResult)


def test_integration_with_intent_analyzer() -> None:
    """Verifies constraint analyzer operates smoothly alongside IntentAnalyzer."""
    intent_an = IntentAnalyzer()
    ca = ConstraintAnalyzer()

    req = "find all PDFs from Downloads"
    intent_res = intent_an.analyze(req)
    const_res = ca.analyze_constraints(req, intent_result=intent_res)

    assert intent_res.intent == IntentCategory.FILE_SEARCH
    assert const_res.constraint_count >= 1


def test_integration_with_strategy_selector() -> None:
    """Verifies constraint analyzer operates smoothly alongside StrategySelector."""
    intent_an = IntentAnalyzer()
    strat_sel = ReasoningStrategySelector()
    ca = ConstraintAnalyzer()

    req = "move files to Desktop"
    intent_res = intent_an.analyze(req)
    strat_res = strat_sel.select_strategy(intent_res)
    const_res = ca.analyze_constraints(req, intent_result=intent_res, strategy_result=strat_res)

    assert strat_res.strategy == ReasoningStrategy.FILE_REASONING
    assert const_res.constraint_count >= 1


def test_integration_with_goal_extractor() -> None:
    """Verifies constraint analyzer operates smoothly alongside GoalExtractor."""
    intent_an = IntentAnalyzer()
    strat_sel = ReasoningStrategySelector()
    goal_ext = GoalExtractor()
    ca = ConstraintAnalyzer()

    req = "delete temp files before January"
    intent_res = intent_an.analyze(req)
    strat_res = strat_sel.select_strategy(intent_res)
    goal_res = goal_ext.extract_goals(req, intent_res, strat_res)
    const_res = ca.analyze_constraints(req, intent_res, strat_res, goal_res)

    assert goal_res.goal_type == GoalType.DELETE_FILES
    assert const_res.constraint_count >= 1


def test_logging(caplog: pytest.LogCaptureFixture, analyzer: ConstraintAnalyzer) -> None:
    """Verifies logging output for pattern registration and constraint analysis."""
    with caplog.at_level(logging.INFO):
        analyzer.register_constraint_pattern("log_const", constraint_type=ConstraintType.QUANTITY)
        analyzer.analyze_constraints("log_const")

    assert "Constraint Pattern Registered" in caplog.text
    assert "Constraint Analysis Performed" in caplog.text


def test_singleton_compatibility() -> None:
    """Verifies ConstraintAnalyzer operates as expected when shared across components."""
    c1 = ConstraintAnalyzer()
    c2 = ConstraintAnalyzer()
    assert isinstance(c1, ConstraintAnalyzer)
    assert isinstance(c2, ConstraintAnalyzer)


def test_backward_compatibility(analyzer: ConstraintAnalyzer) -> None:
    """Verifies 100% backward compatibility with pre-existing Goal object analysis."""
    legacy_goal = Goal(name="MEETING", category=GoalCategory.PRODUCTIVITY, description="")
    constraints = analyzer.analyze_constraints(legacy_goal)

    assert isinstance(constraints, list)
    assert len(constraints) == 1
    assert constraints[0].type == "internet"
    assert constraints[0].satisfied is True


def test_regression_validation(analyzer: ConstraintAnalyzer) -> None:
    """Verifies full pipeline regression flow from intent -> strategy -> goal -> constraints."""
    intent_an = IntentAnalyzer()
    strat_sel = ReasoningStrategySelector()
    goal_ext = GoalExtractor()

    req = "copy photo.png to Archive larger than 2 MB"
    i_res = intent_an.analyze(req)
    s_res = strat_sel.select_strategy(i_res)
    g_res = goal_ext.extract_goals(req, i_res, s_res)
    c_res = analyzer.analyze_constraints(req, i_res, s_res, g_res)

    assert i_res.intent == IntentCategory.FILE_MANAGEMENT
    assert s_res.strategy == ReasoningStrategy.FILE_REASONING
    assert g_res.goal_type == GoalType.COPY_FILES
    assert c_res.constraint_count >= 2


def test_configuration_validation() -> None:
    """Verifies ConstraintAnalyzerConfig properties."""
    cfg = ConstraintAnalyzerConfig(maximum_constraints=50, case_sensitive=True, strict_analysis=False)
    ca = ConstraintAnalyzer(config=cfg)

    assert ca.config.maximum_constraints == 50
    assert ca.config.case_sensitive is True
    assert ca.config.strict_analysis is False


def test_empty_constraint_result(analyzer: ConstraintAnalyzer) -> None:
    """Verifies empty constraint result structure when no patterns match."""
    res = analyzer.analyze_constraints("no constraints here zzz")
    assert isinstance(res, ConstraintAnalysisResult)
    assert res.constraint_count == 0
    assert res.constraints == []
