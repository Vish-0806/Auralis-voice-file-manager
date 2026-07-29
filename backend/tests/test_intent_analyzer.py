"""Unit tests for IntentAnalyzer (Phase 9.2.1)."""

from concurrent.futures import ThreadPoolExecutor
import logging
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from brain.reasoning import (
    ConstraintAnalyzer,
    IntentAnalysisResult,
    IntentAnalyzer,
    IntentAnalyzerConfig,
    IntentCategory,
    IntentConfidence,
    ReasoningEngine,
)


@pytest.fixture
def analyzer() -> IntentAnalyzer:
    """Fixture providing a fresh IntentAnalyzer instance."""
    return IntentAnalyzer()


def test_pattern_registration(analyzer: IntentAnalyzer) -> None:
    """Verifies pattern registration."""
    res = analyzer.register_pattern(
        pattern="custom_command_xyz",
        intent=IntentCategory.SYSTEM_CONTROL,
        confidence=IntentConfidence.VERY_HIGH,
        priority=100,
        metadata={"category": "custom"},
    )
    assert res is True

    analysis = analyzer.analyze("custom_command_xyz")
    assert analysis.intent == IntentCategory.SYSTEM_CONTROL
    assert analysis.confidence == IntentConfidence.VERY_HIGH
    assert analysis.metadata == {"category": "custom"}


def test_pattern_removal(analyzer: IntentAnalyzer) -> None:
    """Verifies removing a registered pattern rule."""
    analyzer.register_pattern("unique_remove_pat", intent=IntentCategory.HELP)
    removed = analyzer.remove_pattern("unique_remove_pat")
    assert removed is True

    analysis = analyzer.analyze("unique_remove_pat")
    assert analysis.intent != IntentCategory.HELP or "unique_remove_pat" not in analysis.matched_patterns


def test_duplicate_patterns(analyzer: IntentAnalyzer) -> None:
    """Verifies re-registering a pattern updates the rule without duplicating it."""
    analyzer.register_pattern("dup_pat", intent=IntentCategory.FILE_SEARCH, priority=5)
    analyzer.register_pattern("dup_pat", intent=IntentCategory.FILE_MANAGEMENT, priority=20)

    patterns = [p for p in analyzer.list_patterns() if p["pattern"] == "dup_pat"]
    assert len(patterns) == 1
    assert patterns[0]["intent"] == IntentCategory.FILE_MANAGEMENT


def test_deterministic_matching(analyzer: IntentAnalyzer) -> None:
    """Verifies deterministic pattern matching across categories."""
    res_move = analyzer.analyze("please move report.pdf to Downloads")
    assert res_move.intent == IntentCategory.FILE_MANAGEMENT

    res_search = analyzer.analyze("find all pdfs in my folder")
    assert res_search.intent == IntentCategory.FILE_SEARCH

    res_qa = analyzer.analyze("what is the size of report.pdf")
    assert res_qa.intent == IntentCategory.QUESTION_ANSWERING

    res_convo = analyzer.analyze("hello good morning")
    assert res_convo.intent == IntentCategory.CONVERSATION


def test_confidence_levels(analyzer: IntentAnalyzer) -> None:
    """Verifies confidence level mapping in results."""
    res = analyzer.analyze("hello")
    assert res.confidence == IntentConfidence.VERY_HIGH

    res_search = analyzer.analyze("search for report.pdf")
    assert res_search.confidence == IntentConfidence.HIGH


def test_unknown_intent(analyzer: IntentAnalyzer) -> None:
    """Verifies unmatched input returns UNKNOWN intent with VERY_LOW confidence."""
    res = analyzer.analyze("qwertyuiop zxcvbnm 123456789")
    assert res.intent == IntentCategory.UNKNOWN
    assert res.confidence == IntentConfidence.VERY_LOW
    assert res.matched_patterns == []


def test_empty_input(analyzer: IntentAnalyzer) -> None:
    """Verifies empty input string returns UNKNOWN intent."""
    res = analyzer.analyze("")
    assert res.intent == IntentCategory.UNKNOWN
    assert res.confidence == IntentConfidence.VERY_LOW


def test_invalid_input(analyzer: IntentAnalyzer) -> None:
    """Verifies whitespace input string returns UNKNOWN intent."""
    res = analyzer.analyze("   \t \n ")
    assert res.intent == IntentCategory.UNKNOWN
    assert res.confidence == IntentConfidence.VERY_LOW


def test_thread_safety() -> None:
    """Verifies thread safety during concurrent pattern registration and analysis."""
    an = IntentAnalyzer()

    def worker(idx: int) -> None:
        an.register_pattern(f"worker_pat_{idx}", intent=IntentCategory.SYSTEM_CONTROL)
        an.analyze(f"worker_pat_{idx}")

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker, i) for i in range(50)]
        for f in futures:
            f.result()

    res = an.analyze("worker_pat_25")
    assert res.intent == IntentCategory.SYSTEM_CONTROL


def test_configuration_injection() -> None:
    """Verifies custom IntentAnalyzerConfig configuration options."""
    cfg = IntentAnalyzerConfig(maximum_patterns=2, case_sensitive=True)
    an = IntentAnalyzer(config=cfg)

    # Clearing defaults to test capacity bound
    an.clear_patterns()
    assert an.register_pattern("p1", IntentCategory.HELP) is True
    assert an.register_pattern("p2", IntentCategory.HELP) is True
    assert an.register_pattern("p3", IntentCategory.HELP) is False


def test_immutable_results(analyzer: IntentAnalyzer) -> None:
    """Verifies IntentAnalysisResult is an immutable snapshot model."""
    result = analyzer.analyze("hello")
    with pytest.raises((TypeError, ValidationError)):
        result.intent = IntentCategory.HELP


def test_graceful_failures(analyzer: IntentAnalyzer) -> None:
    """Verifies invalid regex inputs do not crash analyzer."""
    analyzer.register_pattern("[invalid regex (", intent=IntentCategory.FILE_SEARCH, is_regex=True)
    res = analyzer.analyze("test string")
    assert isinstance(res, IntentAnalysisResult)


def test_pattern_listing(analyzer: IntentAnalyzer) -> None:
    """Verifies list_patterns returning registered pattern rules."""
    patterns = analyzer.list_patterns()
    assert len(patterns) > 0

    fm_patterns = analyzer.list_patterns(intent=IntentCategory.FILE_MANAGEMENT)
    assert all(p["intent"] == IntentCategory.FILE_MANAGEMENT for p in fm_patterns)


def test_registry_clearing(analyzer: IntentAnalyzer) -> None:
    """Verifies clear_patterns resets registry."""
    analyzer.clear_patterns()
    assert analyzer.list_patterns() == []
    assert analyzer.analyze("hello").intent == IntentCategory.UNKNOWN


def test_case_sensitivity() -> None:
    """Verifies case_sensitive configuration flag behavior."""
    cfg = IntentAnalyzerConfig(case_sensitive=True)
    an = IntentAnalyzer(config=cfg)
    an.clear_patterns()

    an.register_pattern("UPPERCASE", intent=IntentCategory.HELP, is_regex=False)

    assert an.analyze("UPPERCASE").intent == IntentCategory.HELP
    assert an.analyze("uppercase").intent == IntentCategory.UNKNOWN


def test_multiple_matches(analyzer: IntentAnalyzer) -> None:
    """Verifies multiple matched patterns are captured in result."""
    analyzer.register_pattern("file", intent=IntentCategory.FILE_MANAGEMENT, priority=1)
    analyzer.register_pattern("move", intent=IntentCategory.FILE_MANAGEMENT, priority=10)

    res = analyzer.analyze("move file")
    assert len(res.matched_patterns) >= 2


def test_priority_resolution(analyzer: IntentAnalyzer) -> None:
    """Verifies higher priority pattern rule overrides lower priority rule."""
    analyzer.register_pattern("special_key", intent=IntentCategory.HELP, priority=1)
    analyzer.register_pattern("special_key", intent=IntentCategory.SYSTEM_CONTROL, priority=100)

    res = analyzer.analyze("special_key")
    assert res.intent == IntentCategory.SYSTEM_CONTROL


def test_metadata(analyzer: IntentAnalyzer) -> None:
    """Verifies pattern metadata propagation to analysis result."""
    analyzer.register_pattern(
        "meta_key", intent=IntentCategory.SCHEDULING, metadata={"cron": True}
    )
    res = analyzer.analyze("meta_key")
    assert res.metadata == {"cron": True}


def test_logging(caplog: pytest.LogCaptureFixture, analyzer: IntentAnalyzer) -> None:
    """Verifies logging output on pattern registration and analysis."""
    with caplog.at_level(logging.INFO):
        analyzer.register_pattern("log_test", intent=IntentCategory.HELP)
        analyzer.analyze("log_test")

    assert "Pattern Registered" in caplog.text
    assert "Intent Analysis Performed" in caplog.text


def test_backward_compatibility() -> None:
    """Verifies backward compatibility with pre-existing brain.reasoning exports."""
    from brain.reasoning import (
        Constraint,
        ConstraintAnalyzer,
        Objective,
        ObjectiveBuilder,
        Priority,
        PriorityManager,
        ReasoningEngine,
        ReasoningResult,
    )

    re_engine = ReasoningEngine()
    assert re_engine is not None
