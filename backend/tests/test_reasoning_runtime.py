"""Unit tests for ReasoningRuntimeCoordinator (Phase 9.2.6)."""

from concurrent.futures import ThreadPoolExecutor
import logging
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from brain.reasoning import (
    ConstraintAnalyzer,
    GoalExtractor,
    GoalType,
    IntentAnalyzer,
    IntentCategory,
    ReasoningContext,
    ReasoningContextBuilder,
    ReasoningEngine,
    ReasoningRuntimeCoordinator,
    ReasoningRuntimeHealth,
    ReasoningRuntimeStats,
    ReasoningRuntimeStatus,
    ReasoningStrategy,
    ReasoningStrategySelector,
    get_reasoning_runtime,
    reset_reasoning_runtime,
)


@pytest.fixture(autouse=True)
def auto_reset_runtime() -> None:
    """Fixture to reset reasoning runtime singleton before and after each test."""
    reset_reasoning_runtime()
    yield
    reset_reasoning_runtime()


def test_initialization() -> None:
    """Verifies runtime initialization and READY status transition."""
    coordinator = ReasoningRuntimeCoordinator()
    assert coordinator.status == ReasoningRuntimeStatus.INITIALIZING

    res = coordinator.initialize()
    assert res is True
    assert coordinator.status == ReasoningRuntimeStatus.READY


def test_shutdown() -> None:
    """Verifies runtime shutdown sequence and status transition."""
    coordinator = ReasoningRuntimeCoordinator()
    coordinator.initialize()

    res = coordinator.shutdown()
    assert res is True
    assert coordinator.status == ReasoningRuntimeStatus.SHUTDOWN


def test_health_checks() -> None:
    """Verifies health check output structure and healthy flag."""
    coordinator = ReasoningRuntimeCoordinator()
    coordinator.initialize()

    health = coordinator.health_check()
    assert isinstance(health, ReasoningRuntimeHealth)
    assert health.healthy is True
    assert health.status == ReasoningRuntimeStatus.READY
    assert len(health.components) == 5


def test_runtime_status_transitions() -> None:
    """Verifies status transitions across runtime lifecycle."""
    coordinator = ReasoningRuntimeCoordinator()
    assert coordinator.status == ReasoningRuntimeStatus.INITIALIZING
    coordinator.initialize()
    assert coordinator.status == ReasoningRuntimeStatus.READY
    coordinator.shutdown()
    assert coordinator.status == ReasoningRuntimeStatus.SHUTDOWN


def test_request_processing() -> None:
    """Verifies request processing through 5-stage reasoning pipeline."""
    coordinator = ReasoningRuntimeCoordinator()
    coordinator.initialize()

    context = coordinator.process_request("move report.pdf to Archive")
    assert isinstance(context, ReasoningContext)
    assert context.request == "move report.pdf to Archive"
    assert context.intent.intent == IntentCategory.FILE_MANAGEMENT
    assert context.strategy.strategy == ReasoningStrategy.FILE_REASONING
    assert context.goal.goal_type == GoalType.MOVE_FILES
    assert context.constraints.constraint_count >= 1


def test_statistics_updates() -> None:
    """Verifies requests_processed and runtime statistics updates."""
    coordinator = ReasoningRuntimeCoordinator()
    coordinator.initialize()

    coordinator.process_request("find all pdfs")
    coordinator.process_request("open budget.xlsx")

    stats = coordinator.get_statistics()
    assert isinstance(stats, ReasoningRuntimeStats)
    assert stats.requests_processed == 2
    assert stats.contexts_built == 2
    assert stats.average_runtime_ms >= 0.0


def test_immutable_outputs() -> None:
    """Verifies ReasoningRuntimeHealth and ReasoningRuntimeStats are immutable snapshots."""
    coordinator = ReasoningRuntimeCoordinator()
    coordinator.initialize()

    health = coordinator.health_check()
    with pytest.raises((TypeError, ValidationError)):
        health.healthy = False

    stats = coordinator.get_statistics()
    with pytest.raises((TypeError, ValidationError)):
        stats.requests_processed = 999


def test_thread_safety() -> None:
    """Verifies thread safety during concurrent initialization and statistics generation."""
    coordinator = ReasoningRuntimeCoordinator()

    def worker(idx: int) -> None:
        coordinator.initialize()
        coordinator.health_check()
        coordinator.get_statistics()

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker, i) for i in range(50)]
        for f in futures:
            f.result()

    assert coordinator.status == ReasoningRuntimeStatus.READY


def test_concurrent_processing() -> None:
    """Verifies thread safety during concurrent request processing."""
    coordinator = ReasoningRuntimeCoordinator()
    coordinator.initialize()

    def worker(idx: int) -> None:
        coordinator.process_request(f"move file_{idx}.txt to Archive")

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker, i) for i in range(30)]
        for f in futures:
            f.result()

    stats = coordinator.get_statistics()
    assert stats.requests_processed == 30


def test_singleton_compatibility() -> None:
    """Verifies get_reasoning_runtime singleton accessor."""
    rt1 = get_reasoning_runtime()
    rt2 = get_reasoning_runtime()

    assert rt1 is rt2
    assert rt1.status == ReasoningRuntimeStatus.READY


def test_invalid_requests() -> None:
    """Verifies non-string request inputs return a default context without throwing exceptions."""
    coordinator = ReasoningRuntimeCoordinator()
    coordinator.initialize()

    ctx = coordinator.process_request(12345)  # type: ignore
    assert isinstance(ctx, ReasoningContext)
    assert ctx.request == ""


def test_empty_requests() -> None:
    """Verifies empty string request inputs return a default context cleanly."""
    coordinator = ReasoningRuntimeCoordinator()
    coordinator.initialize()

    ctx = coordinator.process_request("")
    assert isinstance(ctx, ReasoningContext)
    assert ctx.intent.intent == IntentCategory.UNKNOWN


def test_configuration_injection() -> None:
    """Verifies passing custom component instances to ReasoningRuntimeCoordinator constructor."""
    custom_analyzer = IntentAnalyzer()
    coordinator = ReasoningRuntimeCoordinator(intent_analyzer=custom_analyzer)

    assert coordinator.intent_analyzer is custom_analyzer


def test_component_availability() -> None:
    """Verifies list_components returns all 5 reasoning stage component names."""
    coordinator = ReasoningRuntimeCoordinator()
    components = coordinator.list_components()

    assert len(components) == 5
    assert "IntentAnalyzer" in components
    assert "ReasoningStrategySelector" in components
    assert "GoalExtractor" in components
    assert "ConstraintAnalyzer" in components
    assert "ReasoningContextBuilder" in components


def test_diagnostics() -> None:
    """Verifies detailed breakdown in health check statistics."""
    coordinator = ReasoningRuntimeCoordinator()
    coordinator.initialize()

    coordinator.process_request("hello")
    health = coordinator.health_check()

    assert "statistics" in health.model_dump()
    assert health.statistics["requests_processed"] == 1


def test_clear() -> None:
    """Verifies clear() resets runtime statistics counters."""
    coordinator = ReasoningRuntimeCoordinator()
    coordinator.initialize()

    coordinator.process_request("search invoices")
    coordinator.clear()

    stats = coordinator.get_statistics()
    assert stats.requests_processed == 0
    assert stats.contexts_built == 0


def test_logging(caplog: pytest.LogCaptureFixture) -> None:
    """Verifies logging output on lifecycle and request events."""
    coordinator = ReasoningRuntimeCoordinator()
    with caplog.at_level(logging.INFO):
        coordinator.initialize()
        coordinator.process_request("delete temp files")
        coordinator.health_check()
        coordinator.clear()
        coordinator.shutdown()

    assert "Runtime Initialized" in caplog.text
    assert "Request Processed" in caplog.text
    assert "Health Check" in caplog.text
    assert "Runtime Cleared" in caplog.text
    assert "Runtime Shutdown" in caplog.text


def test_integration_with_intent_analyzer() -> None:
    """Verifies IntentAnalyzer integration in coordinator."""
    coordinator = ReasoningRuntimeCoordinator()
    ctx = coordinator.process_request("what is Python?")
    assert ctx.intent.intent == IntentCategory.QUESTION_ANSWERING


def test_integration_with_strategy_selector() -> None:
    """Verifies ReasoningStrategySelector integration in coordinator."""
    coordinator = ReasoningRuntimeCoordinator()
    ctx = coordinator.process_request("create project folder")
    assert ctx.strategy.strategy == ReasoningStrategy.FILE_REASONING


def test_integration_with_goal_extractor() -> None:
    """Verifies GoalExtractor integration in coordinator."""
    coordinator = ReasoningRuntimeCoordinator()
    ctx = coordinator.process_request("schedule backup daily")
    assert ctx.goal.goal_type == GoalType.SCHEDULE_TASK


def test_integration_with_constraint_analyzer() -> None:
    """Verifies ConstraintAnalyzer integration in coordinator."""
    coordinator = ReasoningRuntimeCoordinator()
    ctx = coordinator.process_request("copy report.pdf from Downloads to Desktop")
    assert ctx.constraints.constraint_count >= 1


def test_integration_with_context_builder() -> None:
    """Verifies ReasoningContextBuilder integration in coordinator."""
    coordinator = ReasoningRuntimeCoordinator()
    ctx = coordinator.process_request("rename report.pdf to final.pdf")
    assert isinstance(ctx, ReasoningContext)
    assert ctx.request == "rename report.pdf to final.pdf"


def test_backward_compatibility() -> None:
    """Verifies 100% backward compatibility with existing reasoning engine exports."""
    from brain.reasoning import (
        ConstraintAnalyzer,
        GoalExtractor,
        IntentAnalyzer,
        ObjectiveBuilder,
        PriorityManager,
        ReasoningContext,
        ReasoningContextBuilder,
        ReasoningEngine,
        ReasoningRuntimeCoordinator,
        ReasoningStrategySelector,
        get_reasoning_runtime,
    )

    rt = get_reasoning_runtime()
    assert rt is not None


def test_regression_validation() -> None:
    """Verifies full pipeline end-to-end regression execution via get_reasoning_runtime."""
    rt = get_reasoning_runtime()
    ctx = rt.process_request("move photos to Archive before January")

    assert ctx.intent.intent == IntentCategory.FILE_MANAGEMENT
    assert ctx.strategy.strategy == ReasoningStrategy.FILE_REASONING
    assert ctx.goal.goal_type == GoalType.MOVE_FILES
    assert ctx.constraints.constraint_count >= 1
