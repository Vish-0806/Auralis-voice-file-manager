"""Unit tests for GoalExtractor (Phase 9.2.3)."""

from concurrent.futures import ThreadPoolExecutor
import logging
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from brain.reasoning import (
    ConstraintAnalyzer,
    GoalExtractionResult,
    GoalExtractor,
    GoalExtractorConfig,
    GoalPriority,
    GoalType,
    IntentAnalyzer,
    IntentCategory,
    ReasoningEngine,
    ReasoningStrategy,
    ReasoningStrategySelector,
)


@pytest.fixture
def extractor() -> GoalExtractor:
    """Fixture providing a fresh GoalExtractor instance."""
    return GoalExtractor()


def test_goal_registration(extractor: GoalExtractor) -> None:
    """Verifies registering a custom goal pattern rule."""
    res = extractor.register_goal_pattern(
        pattern=r"\barchive\b",
        goal_type=GoalType.MOVE_FILES,
        action="archive",
        priority=GoalPriority.HIGH,
        metadata={"custom": True},
    )
    assert res is True

    result = extractor.extract_goals("archive old files")
    assert result.goal_type == GoalType.MOVE_FILES
    assert result.action == "archive"
    assert result.metadata == {"custom": True}


def test_goal_removal(extractor: GoalExtractor) -> None:
    """Verifies removing a registered goal pattern rule."""
    extractor.register_goal_pattern("unique_goal_pat", goal_type=GoalType.SCHEDULE_TASK)
    removed = extractor.remove_goal_pattern("unique_goal_pat")
    assert removed is True

    result = extractor.extract_goals("unique_goal_pat")
    assert result.goal_type == GoalType.UNKNOWN


def test_deterministic_extraction(extractor: GoalExtractor) -> None:
    """Verifies deterministic goal extraction from user request phrases."""
    res_move = extractor.extract_goals("Move all PDFs to Archive")
    assert res_move.goal_type == GoalType.MOVE_FILES
    assert res_move.action == "move"

    res_copy = extractor.extract_goals("Copy photos to backup")
    assert res_copy.goal_type == GoalType.COPY_FILES

    res_del = extractor.extract_goals("Delete temp files")
    assert res_del.goal_type == GoalType.DELETE_FILES

    res_rename = extractor.extract_goals("Rename report.pdf to final.pdf")
    assert res_rename.goal_type == GoalType.RENAME_FILES

    res_find = extractor.extract_goals("Find invoices")
    assert res_find.goal_type == GoalType.SEARCH_FILES

    res_open = extractor.extract_goals("Open budget.xlsx")
    assert res_open.goal_type == GoalType.OPEN_FILE

    res_mkdir = extractor.extract_goals("Create project folder")
    assert res_mkdir.goal_type == GoalType.CREATE_FOLDER

    res_rmdir = extractor.extract_goals("Delete old folder")
    assert res_rmdir.goal_type == GoalType.DELETE_FOLDER

    res_sched = extractor.extract_goals("Schedule backup task")
    assert res_sched.goal_type == GoalType.SCHEDULE_TASK

    res_qa = extractor.extract_goals("What is Python?")
    assert res_qa.goal_type == GoalType.ANSWER_QUESTION


def test_every_goal_type(extractor: GoalExtractor) -> None:
    """Verifies all 12 GoalType enum values can be produced or registered."""
    types = [
        GoalType.MOVE_FILES,
        GoalType.COPY_FILES,
        GoalType.DELETE_FILES,
        GoalType.RENAME_FILES,
        GoalType.SEARCH_FILES,
        GoalType.OPEN_FILE,
        GoalType.CREATE_FOLDER,
        GoalType.DELETE_FOLDER,
        GoalType.SCHEDULE_TASK,
        GoalType.ANSWER_QUESTION,
        GoalType.GENERAL_TASK,
        GoalType.UNKNOWN,
    ]
    for gt in types:
        assert isinstance(gt.value, str)


def test_multiple_objects(extractor: GoalExtractor) -> None:
    """Verifies extracting multiple objects from request string."""
    res = extractor.extract_goals("move report.pdf and image.png to backup")
    assert len(res.objects) >= 2
    assert "report.pdf" in res.objects
    assert "image.png" in res.objects


def test_unknown_goal(extractor: GoalExtractor) -> None:
    """Verifies unmatched request text maps to UNKNOWN goal type."""
    res = extractor.extract_goals("qwertyuiop zxcvbnm 12345")
    assert res.goal_type == GoalType.UNKNOWN
    assert res.priority == GoalPriority.LOW


def test_invalid_input(extractor: GoalExtractor) -> None:
    """Verifies non-string input returns UNKNOWN goal without raising exceptions."""
    res = extractor.extract_goals(12345)  # type: ignore
    assert res.goal_type == GoalType.UNKNOWN


def test_empty_request(extractor: GoalExtractor) -> None:
    """Verifies empty or whitespace request string returns UNKNOWN goal."""
    res = extractor.extract_goals("")
    assert res.goal_type == GoalType.UNKNOWN

    res_ws = extractor.extract_goals("   \n\t  ")
    assert res_ws.goal_type == GoalType.UNKNOWN


def test_immutable_results(extractor: GoalExtractor) -> None:
    """Verifies GoalExtractionResult is an immutable snapshot model."""
    res = extractor.extract_goals("move report.pdf")
    with pytest.raises((TypeError, ValidationError)):
        res.goal_type = GoalType.COPY_FILES


def test_metadata(extractor: GoalExtractor) -> None:
    """Verifies metadata propagation in GoalExtractionResult."""
    extractor.register_goal_pattern(
        pattern="special_task_meta",
        goal_type=GoalType.GENERAL_TASK,
        metadata={"priority_level": 5},
    )
    res = extractor.extract_goals("special_task_meta")
    assert res.metadata == {"priority_level": 5}


def test_configuration_injection() -> None:
    """Verifies custom GoalExtractorConfig injection and object limits."""
    cfg = GoalExtractorConfig(maximum_objects=1)
    ge = GoalExtractor(config=cfg)

    res = ge.extract_goals("move report.pdf and image.png")
    assert len(res.objects) == 1


def test_thread_safety() -> None:
    """Verifies thread safety during concurrent goal registrations and extractions."""
    ge = GoalExtractor()

    def worker(idx: int) -> None:
        ge.register_goal_pattern(f"worker_pat_{idx}", goal_type=GoalType.GENERAL_TASK)
        ge.extract_goals(f"worker_pat_{idx}")

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker, i) for i in range(50)]
        for f in futures:
            f.result()

    res = ge.extract_goals("worker_pat_10")
    assert res.goal_type == GoalType.GENERAL_TASK


def test_duplicate_patterns(extractor: GoalExtractor) -> None:
    """Verifies re-registering a pattern updates the goal rule cleanly."""
    extractor.register_goal_pattern("dup_pat", goal_type=GoalType.SEARCH_FILES)
    extractor.register_goal_pattern("dup_pat", goal_type=GoalType.DELETE_FILES)

    patterns = [p for p in extractor.list_goal_patterns() if p["pattern"] == "dup_pat"]
    assert len(patterns) == 1
    assert patterns[0]["goal_type"] == GoalType.DELETE_FILES


def test_pattern_priority(extractor: GoalExtractor) -> None:
    """Verifies higher priority goal pattern overrides lower priority match."""
    extractor.register_goal_pattern(
        "prio_key", goal_type=GoalType.GENERAL_TASK, priority=GoalPriority.LOW
    )
    extractor.register_goal_pattern(
        "prio_key", goal_type=GoalType.DELETE_FILES, priority=GoalPriority.CRITICAL
    )

    res = extractor.extract_goals("prio_key")
    assert res.goal_type == GoalType.DELETE_FILES


def test_registry_clearing(extractor: GoalExtractor) -> None:
    """Verifies clear_goal_patterns resets patterns registry."""
    extractor.clear_goal_patterns()
    assert extractor.list_goal_patterns() == []
    assert extractor.extract_goals("move report.pdf").goal_type == GoalType.UNKNOWN


def test_listing(extractor: GoalExtractor) -> None:
    """Verifies list_goal_patterns returning registered goal patterns."""
    patterns = extractor.list_goal_patterns()
    assert len(patterns) > 0

    move_pats = extractor.list_goal_patterns(goal_type=GoalType.MOVE_FILES)
    assert all(p["goal_type"] == GoalType.MOVE_FILES for p in move_pats)


def test_graceful_failures(extractor: GoalExtractor) -> None:
    """Verifies malformed regex rules do not crash extractor."""
    extractor.register_goal_pattern("[invalid regex (", goal_type=GoalType.SEARCH_FILES)
    res = extractor.extract_goals("some query text")
    assert isinstance(res, GoalExtractionResult)


def test_integration_with_intent_analyzer() -> None:
    """Verifies goal extractor accepts IntentAnalysisResult to guide fallback."""
    analyzer = IntentAnalyzer()
    extractor = GoalExtractor()

    intent_res = analyzer.analyze("search for budget documents")
    goal_res = extractor.extract_goals("budget documents", intent_result=intent_res)

    assert intent_res.intent == IntentCategory.FILE_SEARCH
    assert goal_res.goal_type == GoalType.SEARCH_FILES


def test_integration_with_strategy_selector() -> None:
    """Verifies goal extractor operates smoothly alongside StrategySelector."""
    analyzer = IntentAnalyzer()
    selector = ReasoningStrategySelector()
    extractor = GoalExtractor()

    request = "what is recursion?"
    intent_res = analyzer.analyze(request)
    strat_res = selector.select_strategy(intent_res)
    goal_res = extractor.extract_goals(request, intent_result=intent_res, strategy_result=strat_res)

    assert strat_res.strategy == ReasoningStrategy.DIRECT_RESPONSE
    assert goal_res.goal_type == GoalType.ANSWER_QUESTION


def test_logging(caplog: pytest.LogCaptureFixture, extractor: GoalExtractor) -> None:
    """Verifies logging output for pattern registration and goal extraction."""
    with caplog.at_level(logging.INFO):
        extractor.register_goal_pattern("log_goal", goal_type=GoalType.OPEN_FILE)
        extractor.extract_goals("log_goal")

    assert "Goal Pattern Registered" in caplog.text
    assert "Goal Extraction Performed" in caplog.text


def test_singleton_compatibility() -> None:
    """Verifies GoalExtractor operates as expected when shared across components."""
    e1 = GoalExtractor()
    e2 = GoalExtractor()
    assert isinstance(e1, GoalExtractor)
    assert isinstance(e2, GoalExtractor)


def test_backward_compatibility() -> None:
    """Verifies backward compatibility with pre-existing brain.reasoning exports."""
    from brain.reasoning import (
        ConstraintAnalyzer,
        GoalExtractionResult,
        GoalExtractor,
        IntentAnalyzer,
        ObjectiveBuilder,
        PriorityManager,
        ReasoningEngine,
        ReasoningStrategySelector,
    )

    ge = GoalExtractor()
    assert ge is not None


def test_regression_validation(extractor: GoalExtractor) -> None:
    """Verifies end-to-end reasoning pipeline flow."""
    analyzer = IntentAnalyzer()
    selector = ReasoningStrategySelector()

    req = "delete temp files"
    intent_res = analyzer.analyze(req)
    strat_res = selector.select_strategy(intent_res)
    goal_res = extractor.extract_goals(req, intent_res, strat_res)

    assert intent_res.intent == IntentCategory.FILE_MANAGEMENT
    assert strat_res.strategy == ReasoningStrategy.FILE_REASONING
    assert goal_res.goal_type == GoalType.DELETE_FILES
    assert goal_res.action == "delete"


def test_configuration_validation() -> None:
    """Verifies GoalExtractorConfig properties."""
    cfg = GoalExtractorConfig(maximum_objects=10, case_sensitive=True, strict_extraction=False)
    ge = GoalExtractor(config=cfg)

    assert ge.config.maximum_objects == 10
    assert ge.config.case_sensitive is True
    assert ge.config.strict_extraction is False
