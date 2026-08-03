"""Unit tests for Phase 13.4 – Decision & Reasoning Coordinator."""

import threading
import pytest
from pydantic import ValidationError

from brain.assistant.reasoning import (
    DecisionAction,
    DecisionCandidate,
    DecisionContext,
    DecisionCoordinator,
    DecisionEvaluator,
    DecisionException,
    DecisionHealth,
    DecisionMetadata,
    DecisionOutcome,
    DecisionPolicy,
    DecisionPriority,
    DecisionProvider,
    DecisionRequest,
    DecisionResult,
    DecisionRuntime,
    DecisionStatistics,
    DecisionValidationError,
    IDecisionProvider,
    PolicyManager,
    get_decision_runtime,
    reset_decision_runtime,
)


@pytest.fixture(autouse=True)
def cleanup_singleton():
    """Ensure clean singleton state before and after each test."""
    reset_decision_runtime()
    yield
    reset_decision_runtime()


# ---------------------------------------------------------------------------
# 1. Immutable Models
# ---------------------------------------------------------------------------

def test_immutable_models() -> None:
    """Verify all 8 Pydantic v2 domain models are frozen and immutable."""
    meta = DecisionMetadata()
    pol = DecisionPolicy()
    ctx = DecisionContext()
    req = DecisionRequest()
    cand = DecisionCandidate()
    res = DecisionResult()
    stats = DecisionStatistics()
    health = DecisionHealth()

    models = [meta, pol, ctx, req, cand, res, stats, health]
    for m in models:
        with pytest.raises((ValidationError, TypeError, AttributeError)):
            m.priority = DecisionPriority.HIGH  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# 2. Decision Routing & Evaluation
# ---------------------------------------------------------------------------

def test_routing_decisions() -> None:
    """Verify deterministic request evaluation and decision routing."""
    runtime = get_decision_runtime()
    provider = runtime.get_provider()
    assert isinstance(provider, DecisionProvider)

    req = DecisionRequest(user_prompt="open my downloads folder")
    res = provider.evaluate_request(req)

    assert isinstance(res, DecisionResult)
    assert res.recommended_action == DecisionAction.DIRECT_EXECUTION
    assert res.priority in (DecisionPriority.HIGH, DecisionPriority.MEDIUM)
    assert res.outcome == DecisionOutcome.ACCEPTED


# ---------------------------------------------------------------------------
# 3. Policy Evaluation: Clarification Routing
# ---------------------------------------------------------------------------

def test_clarification_routing() -> None:
    """Verify policy evaluation detects clarification requirement for empty or ambiguous request."""
    runtime = get_decision_runtime()
    provider = runtime.get_provider()
    assert isinstance(provider, DecisionProvider)

    req_empty = DecisionRequest(user_prompt="")
    res = provider.evaluate_request(req_empty)

    assert res.recommended_action == DecisionAction.CLARIFICATION_REQUIRED
    assert res.requires_clarification is True
    assert res.clarification_prompt is not None
    assert "clarification" in res.clarification_prompt.lower()


# ---------------------------------------------------------------------------
# 4. Policy Evaluation: Confirmation Routing
# ---------------------------------------------------------------------------

def test_confirmation_routing() -> None:
    """Verify policy evaluation detects confirmation requirement for destructive actions."""
    runtime = get_decision_runtime()
    provider = runtime.get_provider()
    assert isinstance(provider, DecisionProvider)

    req_destruct = DecisionRequest(user_prompt="delete all logs and temp files")
    res = provider.evaluate_request(req_destruct)

    assert res.recommended_action == DecisionAction.CONFIRMATION_REQUIRED
    assert res.requires_confirmation is True
    assert res.confirmation_prompt is not None
    assert "confirm" in res.confirmation_prompt.lower() or "action" in res.confirmation_prompt.lower()


# ---------------------------------------------------------------------------
# 5. Candidate Scoring & Conflict Resolution
# ---------------------------------------------------------------------------

def test_decision_scoring_and_conflict_resolution() -> None:
    """Verify DecisionEvaluator candidate scoring and conflict resolution."""
    evaluator = DecisionEvaluator()
    ctx = DecisionContext(execution_ready=True)

    cand_low = DecisionCandidate(
        action=DecisionAction.AI_REQUIRED,
        score=0.7,
        priority=DecisionPriority.LOW,
    )
    cand_high = DecisionCandidate(
        action=DecisionAction.DIRECT_EXECUTION,
        score=0.9,
        priority=DecisionPriority.HIGH,
    )

    winner = evaluator.evaluate_candidates([cand_low, cand_high], ctx)
    assert winner.candidate_id == cand_high.candidate_id
    assert winner.action == DecisionAction.DIRECT_EXECUTION


# ---------------------------------------------------------------------------
# 6. Execution Readiness & Planner Evaluation
# ---------------------------------------------------------------------------

def test_execution_readiness_and_planner() -> None:
    """Verify execution readiness scoring and multi-step planner detection."""
    runtime = get_decision_runtime()
    provider = runtime.get_provider()
    assert isinstance(provider, DecisionProvider)

    req_plan = DecisionRequest(user_prompt="organize pipeline workflow")
    res = provider.evaluate_request(req_plan)

    assert res.recommended_action == DecisionAction.PLANNER_REQUIRED
    assert res.requires_planner is True


# ---------------------------------------------------------------------------
# 7. Statistics & Health Reporting
# ---------------------------------------------------------------------------

def test_statistics_and_health() -> None:
    """Verify metrics statistics and diagnostic health reporting."""
    runtime = get_decision_runtime()
    provider = runtime.get_provider()
    assert isinstance(provider, DecisionProvider)

    provider.evaluate_request(DecisionRequest(user_prompt="open file"))
    provider.evaluate_request(DecisionRequest(user_prompt="delete file"))
    provider.evaluate_request(DecisionRequest(user_prompt="organize pipeline"))

    stats = runtime.get_statistics()
    assert stats.total_requests_evaluated == 3
    assert stats.direct_executions_routed >= 1
    assert stats.confirmations_routed >= 1

    health = runtime.get_health()
    assert health.healthy is True
    assert health.status == "READY"


# ---------------------------------------------------------------------------
# 8. Singleton Identity & Reset
# ---------------------------------------------------------------------------

def test_singleton_identity() -> None:
    """Verify get_decision_runtime singleton identity and reset_decision_runtime."""
    rt1 = get_decision_runtime()
    rt2 = get_decision_runtime()
    assert rt1 is rt2
    assert rt1.is_initialized is True

    reset_decision_runtime()
    rt3 = get_decision_runtime()
    assert rt3 is not rt1
    assert rt3.is_initialized is True


# ---------------------------------------------------------------------------
# 9. Thread Safety
# ---------------------------------------------------------------------------

def test_thread_safety() -> None:
    """Verify thread safety under concurrent request evaluation."""
    runtime = get_decision_runtime()
    provider = runtime.get_provider()
    assert isinstance(provider, DecisionProvider)

    errors = []

    def worker(idx: int) -> None:
        try:
            for i in range(10):
                req = DecisionRequest(user_prompt=f"command {i} thread {idx}")
                _ = provider.evaluate_request(req)
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0
    stats = runtime.get_statistics()
    assert stats.total_requests_evaluated == 100


# ---------------------------------------------------------------------------
# 10. Dependency Injection & Backward Compatibility
# ---------------------------------------------------------------------------

def test_dependency_injection_and_compatibility() -> None:
    """Verify constructor dependency injection and backward compatibility with Phase 13.1-13.3."""
    from brain.assistant import get_assistant_runtime
    from brain.assistant.conversation import get_conversation_runtime
    from brain.assistant.dialogue import get_dialogue_runtime

    ast_rt = get_assistant_runtime()
    conv_rt = get_conversation_runtime()
    dial_rt = get_dialogue_runtime()

    assert ast_rt.is_initialized is True
    assert conv_rt.is_initialized is True
    assert dial_rt.is_initialized is True

    custom_policy = PolicyManager()
    custom_eval = DecisionEvaluator()
    custom_coord = DecisionCoordinator(policy_manager=custom_policy, evaluator=custom_eval)
    custom_provider = DecisionProvider(coordinator=custom_coord, policy_manager=custom_policy, evaluator=custom_eval)

    dec_rt = DecisionRuntime(provider=custom_provider)
    dec_rt.initialize()
    assert dec_rt.is_initialized is True
