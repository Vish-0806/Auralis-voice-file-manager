"""Unit tests for ReasoningStrategySelector (Phase 9.2.2)."""

from concurrent.futures import ThreadPoolExecutor
import logging
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from brain.reasoning import (
    ConstraintAnalyzer,
    IntentAnalysisResult,
    IntentCategory,
    IntentConfidence,
    ReasoningEngine,
    ReasoningStrategy,
    ReasoningStrategySelector,
    StrategyPriority,
    StrategySelectionResult,
    StrategySelectorConfig,
)


@pytest.fixture
def selector() -> ReasoningStrategySelector:
    """Fixture providing a fresh ReasoningStrategySelector instance."""
    return ReasoningStrategySelector()


def test_strategy_registration(selector: ReasoningStrategySelector) -> None:
    """Verifies strategy rule registration."""
    res = selector.register_strategy(
        intent=IntentCategory.FILE_MANAGEMENT,
        strategy=ReasoningStrategy.FILE_REASONING,
        priority=StrategyPriority.CRITICAL,
        metadata={"custom": True},
    )
    assert res is True

    intent_res = IntentAnalysisResult(
        intent=IntentCategory.FILE_MANAGEMENT, confidence=IntentConfidence.HIGH
    )
    result = selector.select_strategy(intent_res)
    assert result.strategy == ReasoningStrategy.FILE_REASONING
    assert result.priority == StrategyPriority.CRITICAL
    assert result.metadata == {"custom": True}


def test_strategy_removal(selector: ReasoningStrategySelector) -> None:
    """Verifies strategy rule removal."""
    removed = selector.remove_strategy(IntentCategory.FILE_MANAGEMENT)
    assert removed is True

    intent_res = IntentAnalysisResult(
        intent=IntentCategory.FILE_MANAGEMENT, confidence=IntentConfidence.HIGH
    )
    result = selector.select_strategy(intent_res)
    # Should fallback to clarification required when unmapped
    assert result.strategy == ReasoningStrategy.CLARIFICATION_REQUIRED


def test_deterministic_mapping(selector: ReasoningStrategySelector) -> None:
    """Verifies deterministic intent-to-strategy mapping for all categories."""
    mappings = [
        (IntentCategory.FILE_MANAGEMENT, ReasoningStrategy.FILE_REASONING),
        (IntentCategory.FILE_SEARCH, ReasoningStrategy.SEARCH_REASONING),
        (IntentCategory.QUESTION_ANSWERING, ReasoningStrategy.DIRECT_RESPONSE),
        (IntentCategory.CONVERSATION, ReasoningStrategy.CONVERSATIONAL_REASONING),
        (IntentCategory.PLANNING, ReasoningStrategy.PLANNING_REASONING),
        (IntentCategory.SCHEDULING, ReasoningStrategy.SCHEDULING_REASONING),
        (IntentCategory.SYSTEM_CONTROL, ReasoningStrategy.SYSTEM_REASONING),
        (IntentCategory.HELP, ReasoningStrategy.HELP_REASONING),
    ]

    for intent, expected_strategy in mappings:
        intent_res = IntentAnalysisResult(intent=intent, confidence=IntentConfidence.HIGH)
        result = selector.select_strategy(intent_res)
        assert result.strategy == expected_strategy
        assert result.source_intent == intent
        assert result.requires_clarification is False


def test_unknown_intent(selector: ReasoningStrategySelector) -> None:
    """Verifies UNKNOWN intent maps to CLARIFICATION_REQUIRED."""
    intent_res = IntentAnalysisResult(intent=IntentCategory.UNKNOWN, confidence=IntentConfidence.VERY_LOW)
    result = selector.select_strategy(intent_res)

    assert result.strategy == ReasoningStrategy.CLARIFICATION_REQUIRED
    assert result.requires_clarification is True
    assert result.priority == StrategyPriority.LOW


def test_clarification_required(selector: ReasoningStrategySelector) -> None:
    """Verifies clarification flag is set when appropriate."""
    selector.register_strategy(
        intent=IntentCategory.HELP,
        strategy=ReasoningStrategy.CLARIFICATION_REQUIRED,
        requires_clarification=True,
    )
    intent_res = IntentAnalysisResult(intent=IntentCategory.HELP, confidence=IntentConfidence.MEDIUM)
    result = selector.select_strategy(intent_res)

    assert result.strategy == ReasoningStrategy.CLARIFICATION_REQUIRED
    assert result.requires_clarification is True


def test_confidence_threshold(selector: ReasoningStrategySelector) -> None:
    """Verifies VERY_LOW confidence intent triggers CLARIFICATION_REQUIRED."""
    intent_res = IntentAnalysisResult(
        intent=IntentCategory.FILE_MANAGEMENT, confidence=IntentConfidence.VERY_LOW
    )
    result = selector.select_strategy(intent_res)

    assert result.strategy == ReasoningStrategy.CLARIFICATION_REQUIRED
    assert result.requires_clarification is True


def test_priority_assignment(selector: ReasoningStrategySelector) -> None:
    """Verifies priority level assignment for strategies."""
    intent_res_sys = IntentAnalysisResult(
        intent=IntentCategory.SYSTEM_CONTROL, confidence=IntentConfidence.HIGH
    )
    result = selector.select_strategy(intent_res_sys)
    assert result.priority == StrategyPriority.CRITICAL

    intent_res_help = IntentAnalysisResult(
        intent=IntentCategory.HELP, confidence=IntentConfidence.HIGH
    )
    result_help = selector.select_strategy(intent_res_help)
    assert result_help.priority == StrategyPriority.LOW


def test_immutable_results(selector: ReasoningStrategySelector) -> None:
    """Verifies StrategySelectionResult is an immutable model."""
    intent_res = IntentAnalysisResult(intent=IntentCategory.CONVERSATION, confidence=IntentConfidence.HIGH)
    result = selector.select_strategy(intent_res)

    with pytest.raises((TypeError, ValidationError)):
        result.strategy = ReasoningStrategy.FILE_REASONING


def test_invalid_input(selector: ReasoningStrategySelector) -> None:
    """Verifies None input gracefully returns CLARIFICATION_REQUIRED."""
    result = selector.select_strategy(None)
    assert result.strategy == ReasoningStrategy.CLARIFICATION_REQUIRED
    assert result.requires_clarification is True


def test_thread_safety() -> None:
    """Verifies thread safety during concurrent strategy selection and registration."""
    sel = ReasoningStrategySelector()

    def worker(idx: int) -> None:
        sel.register_strategy(IntentCategory.CONVERSATION, ReasoningStrategy.CONVERSATIONAL_REASONING)
        intent_res = IntentAnalysisResult(intent=IntentCategory.CONVERSATION, confidence=IntentConfidence.HIGH)
        sel.select_strategy(intent_res)

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker, i) for i in range(50)]
        for f in futures:
            f.result()

    intent_res = IntentAnalysisResult(intent=IntentCategory.CONVERSATION, confidence=IntentConfidence.HIGH)
    res = sel.select_strategy(intent_res)
    assert res.strategy == ReasoningStrategy.CONVERSATIONAL_REASONING


def test_configuration_injection() -> None:
    """Verifies custom StrategySelectorConfig configuration."""
    cfg = StrategySelectorConfig(default_priority=StrategyPriority.HIGH, enable_fallback=False)
    sel = ReasoningStrategySelector(config=cfg)

    sel.clear_strategies()
    intent_res = IntentAnalysisResult(intent=IntentCategory.FILE_SEARCH, confidence=IntentConfidence.HIGH)
    result = sel.select_strategy(intent_res)

    assert result.strategy == ReasoningStrategy.UNKNOWN


def test_metadata(selector: ReasoningStrategySelector) -> None:
    """Verifies metadata propagation in StrategySelectionResult."""
    selector.register_strategy(
        intent=IntentCategory.SCHEDULING,
        strategy=ReasoningStrategy.SCHEDULING_REASONING,
        metadata={"async": True},
    )
    intent_res = IntentAnalysisResult(intent=IntentCategory.SCHEDULING, confidence=IntentConfidence.HIGH)
    result = selector.select_strategy(intent_res)

    assert result.metadata == {"async": True}


def test_registry_clearing(selector: ReasoningStrategySelector) -> None:
    """Verifies clear_strategies clears all registered strategy rules."""
    selector.clear_strategies()
    assert selector.list_strategies() == {}


def test_strategy_listing(selector: ReasoningStrategySelector) -> None:
    """Verifies list_strategies returning all registered rules."""
    rules = selector.list_strategies()
    assert IntentCategory.FILE_MANAGEMENT.value in rules
    assert rules[IntentCategory.FILE_MANAGEMENT.value]["strategy"] == ReasoningStrategy.FILE_REASONING


def test_duplicate_registrations(selector: ReasoningStrategySelector) -> None:
    """Verifies re-registering a strategy for an intent overwrites previous rule."""
    selector.register_strategy(
        intent=IntentCategory.FILE_MANAGEMENT,
        strategy=ReasoningStrategy.DIRECT_RESPONSE,
    )
    intent_res = IntentAnalysisResult(intent=IntentCategory.FILE_MANAGEMENT, confidence=IntentConfidence.HIGH)
    result = selector.select_strategy(intent_res)

    assert result.strategy == ReasoningStrategy.DIRECT_RESPONSE


def test_graceful_failures(selector: ReasoningStrategySelector) -> None:
    """Verifies unmapped intent without fallback returns UNKNOWN safely."""
    cfg = StrategySelectorConfig(enable_fallback=False)
    sel = ReasoningStrategySelector(config=cfg)
    sel.clear_strategies()

    intent_res = IntentAnalysisResult(intent=IntentCategory.FILE_SEARCH, confidence=IntentConfidence.HIGH)
    result = sel.select_strategy(intent_res)

    assert isinstance(result, StrategySelectionResult)
    assert result.strategy == ReasoningStrategy.UNKNOWN


def test_logging(caplog: pytest.LogCaptureFixture, selector: ReasoningStrategySelector) -> None:
    """Verifies logging output for strategy registration and selection."""
    with caplog.at_level(logging.INFO):
        selector.register_strategy(IntentCategory.HELP, ReasoningStrategy.HELP_REASONING)
        intent_res = IntentAnalysisResult(intent=IntentCategory.HELP, confidence=IntentConfidence.HIGH)
        selector.select_strategy(intent_res)

    assert "Strategy Registered" in caplog.text
    assert "Strategy Selected" in caplog.text


def test_fallback_behaviour(selector: ReasoningStrategySelector) -> None:
    """Verifies fallback to CLARIFICATION_REQUIRED for unmapped intent when enable_fallback is True."""
    selector.remove_strategy(IntentCategory.HELP)
    intent_res = IntentAnalysisResult(intent=IntentCategory.HELP, confidence=IntentConfidence.HIGH)
    result = selector.select_strategy(intent_res)

    assert result.strategy == ReasoningStrategy.CLARIFICATION_REQUIRED
    assert result.requires_clarification is True


def test_strict_matching(selector: ReasoningStrategySelector) -> None:
    """Verifies strict matching configuration parameter."""
    cfg = StrategySelectorConfig(strict_matching=True)
    sel = ReasoningStrategySelector(config=cfg)

    intent_res = IntentAnalysisResult(intent=IntentCategory.PLANNING, confidence=IntentConfidence.HIGH)
    result = sel.select_strategy(intent_res)
    assert result.strategy == ReasoningStrategy.PLANNING_REASONING


def test_singleton_compatibility() -> None:
    """Verifies ReasoningStrategySelector operates as expected when instantiated as a shared service."""
    s1 = ReasoningStrategySelector()
    s2 = ReasoningStrategySelector()
    assert isinstance(s1, ReasoningStrategySelector)
    assert isinstance(s2, ReasoningStrategySelector)


def test_backward_compatibility() -> None:
    """Verifies backward compatibility with pre-existing brain.reasoning exports."""
    from brain.reasoning import (
        ConstraintAnalyzer,
        IntentAnalyzer,
        ObjectiveBuilder,
        PriorityManager,
        ReasoningEngine,
        ReasoningStrategySelector,
    )

    engine = ReasoningEngine()
    selector = ReasoningStrategySelector()
    assert engine is not None
    assert selector is not None


def test_regression_validation(selector: ReasoningStrategySelector) -> None:
    """Verifies end-to-end intent-to-strategy flow with IntentAnalyzer."""
    from brain.reasoning import IntentAnalyzer

    analyzer = IntentAnalyzer()
    intent_res = analyzer.analyze("please delete test.txt")
    strategy_res = selector.select_strategy(intent_res)

    assert intent_res.intent == IntentCategory.FILE_MANAGEMENT
    assert strategy_res.strategy == ReasoningStrategy.FILE_REASONING
    assert strategy_res.priority == StrategyPriority.HIGH
