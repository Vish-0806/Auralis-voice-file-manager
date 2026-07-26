# pyrefly: ignore [missing-import]
import pytest
from datetime import datetime, timezone, timedelta
from memory.recommendations import (
    WorkflowRecommendation,
    RecommendationPolicy,
    RecommendationDecision,
    RecommendationPolicyEngine,
)


def create_recommendation(wf_id: str, confidence: float) -> WorkflowRecommendation:
    return WorkflowRecommendation(
        workflow_id=wf_id,
        workflow_name=f"Workflow {wf_id}",
        confidence=confidence,
        recommendation_reason="Test reason",
        trigger_type="test",
        suggested_parameters={}
    )


def test_confidence_threshold():
    policy = RecommendationPolicy(minimum_confidence=0.7)
    engine = RecommendationPolicyEngine(policy=policy)
    
    rec_low = create_recommendation("wf1", 0.5)
    rec_high = create_recommendation("wf2", 0.8)
    
    assert engine.evaluate_policy(rec_low).should_show is False
    assert engine.evaluate_policy(rec_high).should_show is True


def test_rejection_cooldown():
    policy = RecommendationPolicy(cooldown_duration_seconds=100, minimum_confidence=0.5)
    engine = RecommendationPolicyEngine(policy=policy)
    
    rec = create_recommendation("wf1", 0.8)
    now = datetime.now(timezone.utc)
    
    # Verify showing initially
    assert engine.evaluate_policy(rec, now).should_show is True
    
    # Record rejection
    engine.record_rejection("wf1", now)
    
    # Show request 10 seconds later (under 100s cooldown) -> should be suppressed
    assert engine.evaluate_policy(rec, now + timedelta(seconds=10)).should_show is False
    
    # Show request 120 seconds later (past 100s cooldown) -> should be allowed
    assert engine.evaluate_policy(rec, now + timedelta(seconds=120)).should_show is True


def test_active_cooldown():
    policy = RecommendationPolicy(minimum_confidence=0.5)
    engine = RecommendationPolicyEngine(policy=policy)
    
    rec = create_recommendation("wf1", 0.8)
    now = datetime.now(timezone.utc)
    
    # Add explicit 500s cooldown
    engine.add_cooldown("wf1", 500, now)
    
    # Verify suppressed
    assert engine.evaluate_policy(rec, now + timedelta(seconds=200)).should_show is False
    # Verify allowed after 600s
    assert engine.evaluate_policy(rec, now + timedelta(seconds=600)).should_show is True


def test_duplicate_suppression():
    policy = RecommendationPolicy(suppress_duplicates=True, cooldown_duration_seconds=300, minimum_confidence=0.5)
    engine = RecommendationPolicyEngine(policy=policy)
    
    rec = create_recommendation("wf1", 0.8)
    now = datetime.now(timezone.utc)
    
    # Record shown
    engine.record_shown("wf1", now)
    
    # Duplicate suggestion within 300s window -> should be suppressed
    assert engine.evaluate_policy(rec, now + timedelta(seconds=100)).should_show is False
    
    # Allowed after 400s
    assert engine.evaluate_policy(rec, now + timedelta(seconds=400)).should_show is True


def test_policy_engine_workflow_list_limiting():
    policy = RecommendationPolicy(maximum_recommendations=2, minimum_confidence=0.1)
    engine = RecommendationPolicyEngine(policy=policy)
    
    recs = [
        create_recommendation("wf1", 0.9),
        create_recommendation("wf2", 0.8),
        create_recommendation("wf3", 0.7)
    ]
    
    # Standard list filtering: keep those that should_show and respect max count
    now = datetime.now(timezone.utc)
    allowed = []
    for r in recs:
        decision = engine.evaluate_policy(r, now)
        if decision.should_show:
            allowed.append(r)
            
    # Policy evaluation doesn't slice counts automatically (it evaluates single recommendation rules),
    # but the orchestrator or consumer uses maximum_recommendations limit to slice the results:
    sliced_allowed = allowed[:engine.policy.maximum_recommendations]
    assert len(sliced_allowed) == 2
    assert sliced_allowed[0].workflow_id == "wf1"
    assert sliced_allowed[1].workflow_id == "wf2"
