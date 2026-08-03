"""Unit tests for Phase 13.8 – Proactive Assistant & Notification Runtime."""

from concurrent.futures import ThreadPoolExecutor
import threading
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from brain.assistant.proactive import (
    EvaluationResult,
    IProactiveProvider,
    NotificationManager,
    NotificationType,
    ProactiveCapabilities,
    ProactiveContext,
    ProactiveCoordinator,
    ProactiveEvaluation,
    ProactiveEvent,
    ProactiveException,
    ProactiveHealth,
    ProactiveNotification,
    ProactiveProvider,
    ProactiveRecommendation,
    ProactiveRule,
    ProactiveRuntime,
    ProactiveState,
    ProactiveStatistics,
    ProactiveSuggestion,
    RecommendationEngine,
    RuleEvaluator,
    SuggestionPriority,
    SuggestionType,
    get_proactive_runtime,
    reset_proactive_runtime,
)


@pytest.fixture(autouse=True)
def cleanup_singleton():
    """Ensure clean singleton state before and after each test."""
    reset_proactive_runtime()
    yield
    reset_proactive_runtime()


# ---------------------------------------------------------------------------
# 1. Immutable Domain Models
# ---------------------------------------------------------------------------

def test_immutable_models() -> None:
    """Verify all 10 Pydantic v2 models are frozen and immutable."""
    event = ProactiveEvent()
    sug = ProactiveSuggestion()
    rec = ProactiveRecommendation()
    notif = ProactiveNotification()
    ctx = ProactiveContext()
    rule = ProactiveRule()
    stats = ProactiveStatistics()
    health = ProactiveHealth()
    caps = ProactiveCapabilities()
    eval_model = ProactiveEvaluation()

    models = [event, sug, rec, notif, ctx, rule, stats, health, caps, eval_model]
    for m in models:
        with pytest.raises((ValidationError, TypeError, AttributeError)):
            m.priority = SuggestionPriority.HIGH  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# 2. Recommendation Generation & Duplicate Suppression
# ---------------------------------------------------------------------------

def test_recommendation_generation_and_deduplication() -> None:
    """Verify RecommendationEngine generates scored, ranked, and deduplicated recommendations."""
    engine = RecommendationEngine()

    ctx = ProactiveContext(idle_time_seconds=600.0, last_decision_action="CLARIFICATION_REQUIRED")
    recs = engine.generate_recommendations(ctx)

    assert len(recs) >= 2
    assert recs[0].confidence >= recs[1].confidence  # Ranked by confidence descending
    assert engine.total_recommendations_generated >= 2

    # Second generation with same context triggers duplicate suppression
    recs2 = engine.generate_recommendations(ctx)
    assert engine.duplicates_suppressed_count >= 1


# ---------------------------------------------------------------------------
# 3. Notification Creation & Lifecycle Management
# ---------------------------------------------------------------------------

def test_notification_lifecycle() -> None:
    """Verify NotificationManager creates, orders by priority, dismisses, and archives notifications."""
    mgr = NotificationManager()

    n_low = mgr.create_notification("Low Notif", "Details low", priority="LOW")
    n_high = mgr.create_notification("High Notif", "Details high", priority="HIGH")

    active = mgr.list_active_notifications()
    assert len(active) == 2
    assert active[0].notification_id == n_high.notification_id  # Higher priority first

    assert mgr.dismiss_notification(n_high.notification_id) is True
    assert mgr.dismissed_count == 1

    active_remaining = mgr.list_active_notifications()
    assert len(active_remaining) == 1
    assert active_remaining[0].notification_id == n_low.notification_id

    assert mgr.archive_notification(n_low.notification_id) is True
    assert mgr.archived_count == 1
    assert len(mgr.list_active_notifications()) == 0


# ---------------------------------------------------------------------------
# 4. Rule Evaluation, Cooldowns & Suppression
# ---------------------------------------------------------------------------

def test_rule_evaluation_and_cooldowns() -> None:
    """Verify RuleEvaluator evaluates rule conditions, min confidence, and cooldown periods."""
    evaluator = RuleEvaluator()
    rule = ProactiveRule(
        rule_id="r1",
        name="Idle Check",
        cooldown_seconds=10.0,
        min_confidence=0.7,
        conditions={"idle": True},
    )
    evaluator.register_rule(rule)

    # 1. Triggered
    ctx_pass = ProactiveContext(context_variables={"confidence": 0.85, "idle": True})
    res1 = evaluator.evaluate_rule(rule, ctx_pass)
    assert res1 == EvaluationResult.TRIGGERED

    # 2. Cooldown active
    res2 = evaluator.evaluate_rule(rule, ctx_pass)
    assert res2 == EvaluationResult.COOLDOWN_ACTIVE
    assert evaluator.cooldowns_enforced_count == 1

    # 3. Low confidence suppression
    rule2 = ProactiveRule(rule_id="r2", cooldown_seconds=0.0, min_confidence=0.9)
    ctx_low_conf = ProactiveContext(context_variables={"confidence": 0.5})
    res3 = evaluator.evaluate_rule(rule2, ctx_low_conf)
    assert res3 == EvaluationResult.SUPPRESSED


# ---------------------------------------------------------------------------
# 5. Proactive Coordinator Orchestration
# ---------------------------------------------------------------------------

def test_proactive_coordinator() -> None:
    """Verify ProactiveCoordinator evaluates behavior and coordinates recommendations & notifications."""
    coord = ProactiveCoordinator()
    ctx = ProactiveContext(idle_time_seconds=400.0)

    evaluation = coord.evaluate_proactive_behavior(context=ctx)
    assert isinstance(evaluation, ProactiveEvaluation)
    assert evaluation.result == EvaluationResult.TRIGGERED
    assert evaluation.recommendation is not None
    assert evaluation.notification is not None


# ---------------------------------------------------------------------------
# 6. Statistics, Capabilities & Health Diagnostics
# ---------------------------------------------------------------------------

def test_statistics_capabilities_and_health() -> None:
    """Verify ProactiveProvider health diagnostics, statistics, and capabilities."""
    runtime = get_proactive_runtime()
    provider = runtime.get_provider()
    assert isinstance(provider, ProactiveProvider)

    caps = runtime.get_capabilities()
    assert caps.supports_proactive_reminders is True
    assert caps.supports_duplicate_suppression is True

    health = runtime.get_health()
    assert health.healthy is True
    assert health.status == "READY"

    stats = runtime.get_statistics()
    assert isinstance(stats, ProactiveStatistics)


# ---------------------------------------------------------------------------
# 7. Singleton Identity & Restart Mechanics
# ---------------------------------------------------------------------------

def test_singleton_identity_and_restart() -> None:
    """Verify get_proactive_runtime singleton identity and restart() behavior."""
    rt1 = get_proactive_runtime()
    rt2 = get_proactive_runtime()
    assert rt1 is rt2
    assert rt1.is_initialized is True

    rt1.restart()
    assert rt1.is_initialized is True

    reset_proactive_runtime()
    rt3 = get_proactive_runtime()
    assert rt3 is not rt1


# ---------------------------------------------------------------------------
# 8. Concurrent Execution with ThreadPoolExecutor
# ---------------------------------------------------------------------------

def test_concurrent_execution_thread_pool() -> None:
    """Verify concurrent proactive evaluations safety using ThreadPoolExecutor without race conditions."""
    runtime = get_proactive_runtime()
    provider = runtime.get_provider()
    assert isinstance(provider, ProactiveProvider)

    def worker(idx: int) -> bool:
        ctx = ProactiveContext(idle_time_seconds=float(idx * 50))
        eval_res = provider.coordinator.evaluate_proactive_behavior(context=ctx)
        notif = provider.notification_manager.create_notification(
            title=f"Worker {idx}",
            message=f"Notification content {idx}",
        )
        _ = provider.notification_manager.dismiss_notification(notif.notification_id)
        return eval_res.result in (EvaluationResult.TRIGGERED, EvaluationResult.NO_ACTION)

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(worker, i) for i in range(20)]
        results = [f.result() for f in futures]

    assert all(results)
    stats = runtime.get_statistics()
    assert stats.total_evaluations == 20
    assert stats.notifications_dismissed == 20


# ---------------------------------------------------------------------------
# 9. Dependency Injection & Backward Compatibility
# ---------------------------------------------------------------------------

def test_dependency_injection_and_compatibility() -> None:
    """Verify constructor dependency injection and backward compatibility with Phases 9–13.7."""
    from brain.assistant import get_assistant_runtime
    from brain.assistant.conversation import get_conversation_runtime
    from brain.assistant.dialogue import get_dialogue_runtime
    from brain.assistant.memory import get_assistant_memory_runtime
    from brain.assistant.reasoning import get_decision_runtime
    from brain.assistant.response import get_response_runtime
    from brain.assistant.voice import get_voice_runtime

    ast_rt = get_assistant_runtime()
    conv_rt = get_conversation_runtime()
    dial_rt = get_dialogue_runtime()
    dec_rt = get_decision_runtime()
    mem_rt = get_assistant_memory_runtime()
    resp_rt = get_response_runtime()
    voice_rt = get_voice_runtime()

    assert ast_rt.is_initialized is True
    assert conv_rt.is_initialized is True
    assert dial_rt.is_initialized is True
    assert dec_rt.is_initialized is True
    assert mem_rt.is_initialized is True
    assert resp_rt.is_initialized is True
    assert voice_rt.is_initialized is True

    custom_rule = RuleEvaluator()
    custom_rec = RecommendationEngine()
    custom_notif = NotificationManager()
    custom_coord = ProactiveCoordinator(recommendation_engine=custom_rec, notification_manager=custom_notif, rule_evaluator=custom_rule)

    provider = ProactiveProvider(
        coordinator=custom_coord,
        recommendation_engine=custom_rec,
        notification_manager=custom_notif,
        rule_evaluator=custom_rule,
    )

    proactive_rt = ProactiveRuntime(provider=provider)
    proactive_rt.initialize()
    assert proactive_rt.is_initialized is True
