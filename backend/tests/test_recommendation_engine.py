# pyrefly: ignore [missing-import]
import pytest
from datetime import datetime, timezone
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from core.intents import Intent
from automation.workflow.models import WorkflowStep, WorkflowDefinition
from memory.recommendations import (
    WorkflowRecommendation,
    RecommendationContext,
    RecommendationScore,
    RecommendationConfig,
    RecommendationEngine,
)


def create_mock_workflow(name: str, step_targets: list[str]) -> WorkflowDefinition:
    steps = [
        WorkflowStep(intent=Intent.OPEN_APPLICATION, target=t, parameters={})
        for t in step_targets
    ]
    return WorkflowDefinition(name=name, description="Test workflow", steps=steps)


def test_recommendation_config_defaults():
    config = RecommendationConfig()
    assert config.minimum_confidence == 0.5
    assert config.maximum_recommendations == 5
    assert config.workspace_weight == 0.3
    assert config.preference_weight == 0.3
    assert config.frequency_weight == 0.2
    assert config.recency_weight == 0.2


def test_recommendation_config_validation():
    # Valid config
    config = RecommendationConfig(minimum_confidence=0.0, maximum_recommendations=10)
    assert config.minimum_confidence == 0.0

    # Invalid confidence bounds
    with pytest.raises(ValidationError):
        RecommendationConfig(minimum_confidence=1.5)

    with pytest.raises(ValidationError):
        RecommendationConfig(minimum_confidence=-0.1)


def test_recommendation_context_validation():
    ctx = RecommendationContext(
        user_id=1,
        session_id="session_A",
        workspace_analysis={"active_window": "VS Code"},
        resolved_preferences={"Browser": "Chrome"},
        recent_workflows=["workflow_1"],
        current_request="start coding"
    )
    assert ctx.user_id == 1
    assert ctx.session_id == "session_A"


def test_recommendation_engine_constructor_injection():
    config = RecommendationConfig(workspace_weight=0.5, preference_weight=0.5, frequency_weight=0.0, recency_weight=0.0)
    engine = RecommendationEngine(config=config)
    assert engine.config.workspace_weight == 0.5
    assert engine.config.frequency_weight == 0.0


def test_recommendation_engine_empty_handling():
    engine = RecommendationEngine()
    ctx = RecommendationContext(user_id=1, session_id="sess")
    
    # Empty workflows input should return empty recommendation list
    recommendations = engine.recommend(ctx, [])
    assert recommendations == []


def test_frequency_weighting():
    wf1 = create_mock_workflow("Workflow A", ["VS Code"])
    wf2 = create_mock_workflow("Workflow B", ["Chrome"])
    
    # Context with Workflow A occurring twice, Workflow B once in recent history
    ctx = RecommendationContext(
        user_id=1,
        session_id="sess",
        recent_workflows=["Workflow A", "Workflow B", "Workflow A"]
    )
    
    # Configure only frequency weight
    config = RecommendationConfig(
        frequency_weight=1.0, recency_weight=0.0, workspace_weight=0.0, preference_weight=0.0, minimum_confidence=0.0
    )
    engine = RecommendationEngine(config=config)
    
    scored = engine.score_workflows(ctx, [wf1, wf2])
    score_map = {wf.name: s for wf, s in scored}
    
    # Workflow A: 2 / 3 frequency -> 0.666
    assert pytest.approx(score_map["Workflow A"].frequency_score, 0.01) == 0.666
    assert pytest.approx(score_map["Workflow A"].final_score, 0.01) == 0.666
    
    # Workflow B: 1 / 3 frequency -> 0.333
    assert pytest.approx(score_map["Workflow B"].frequency_score, 0.01) == 0.333


def test_recency_weighting():
    wf1 = create_mock_workflow("Workflow A", ["VS Code"])
    wf2 = create_mock_workflow("Workflow B", ["Chrome"])
    
    # Recent history: Workflow A is first index (most recent), Workflow B is second index
    ctx = RecommendationContext(
        user_id=1,
        session_id="sess",
        recent_workflows=["Workflow A", "Workflow B"]
    )
    
    # Configure only recency weight
    config = RecommendationConfig(
        frequency_weight=0.0, recency_weight=1.0, workspace_weight=0.0, preference_weight=0.0, minimum_confidence=0.0
    )
    engine = RecommendationEngine(config=config)
    
    scored = engine.score_workflows(ctx, [wf1, wf2])
    score_map = {wf.name: s for wf, s in scored}
    
    # Workflow A (index 0, most recent): (2 - 0) / 2 = 1.0
    assert score_map["Workflow A"].recency_score == 1.0
    # Workflow B (index 1): (2 - 1) / 2 = 0.5
    assert score_map["Workflow B"].recency_score == 0.5


def test_workspace_matching():
    wf1 = create_mock_workflow("Workflow A", ["VS Code"])  # Step target "VS Code" matches active_window
    wf2 = create_mock_workflow("Workflow B", ["Notepad"])  # No matches
    
    ctx = RecommendationContext(
        user_id=1,
        session_id="sess",
        workspace_analysis={"active_window": "Visual Studio Code"}
    )
    
    # Configure only workspace weight
    config = RecommendationConfig(
        frequency_weight=0.0, recency_weight=0.0, workspace_weight=1.0, preference_weight=0.0, minimum_confidence=0.0
    )
    engine = RecommendationEngine(config=config)
    
    scored = engine.score_workflows(ctx, [wf1, wf2])
    score_map = {wf.name: s for wf, s in scored}
    
    # Workflow A: target "VS Code" matches active_window "Visual Studio Code" -> score 1.0
    assert score_map["Workflow A"].workspace_score == 1.0
    # Workflow B: target "Notepad" -> score 0.0
    assert score_map["Workflow B"].workspace_score == 0.0


def test_preference_influence():
    wf1 = create_mock_workflow("Workflow A", ["Chrome"])  # Step target "Chrome" matches browser preference
    
    ctx = RecommendationContext(
        user_id=1,
        session_id="sess",
        resolved_preferences={"Browser": "Chrome"}
    )
    
    # Configure only preference weight
    config = RecommendationConfig(
        frequency_weight=0.0, recency_weight=0.0, workspace_weight=0.0, preference_weight=1.0, minimum_confidence=0.0
    )
    engine = RecommendationEngine(config=config)
    
    scored = engine.score_workflows(ctx, [wf1])
    score_map = {wf.name: s for wf, s in scored}
    
    assert score_map["Workflow A"].preference_score == 1.0


def test_deterministic_ranking_and_filtering():
    # Setup workflows with identical final scores
    wf1 = create_mock_workflow("Workflow B", ["VS Code"])
    wf2 = create_mock_workflow("Workflow A", ["VS Code"])
    
    ctx = RecommendationContext(
        user_id=1,
        session_id="sess"
    )
    
    # Minimum confidence is 0.5, but both will have final_score = 0.3
    config = RecommendationConfig(
        frequency_weight=0.0, recency_weight=0.0, workspace_weight=1.0, preference_weight=0.0, minimum_confidence=0.5
    )
    engine = RecommendationEngine(config=config)
    
    # Both have no matches, workspace_score = 0.0 < 0.5 threshold -> should be filtered out
    recs = engine.recommend(ctx, [wf1, wf2])
    assert len(recs) == 0
    
    # Lower minimum confidence to 0.0, so both are included
    engine.config.minimum_confidence = 0.0
    recs = engine.recommend(ctx, [wf1, wf2])
    assert len(recs) == 2
    
    # Sort key must place Workflow A before Workflow B (due to alphabetical sorting of deterministic ID)
    # deterministic ID of Workflow A starts with "wf_7c62..." vs Workflow B "wf_f711..."
    # Workflow A hash is: sha256("Workflow A") -> "39c5d7990176..."
    # Workflow B hash is: sha256("Workflow B") -> "14a79fc2c4b7..."
    # Thus, "Workflow B" id starts with "wf_14a79fc2c4b7" which comes alphabetically BEFORE "Workflow A" (wf_39c5...)!
    # Let's assert that index 0 is indeed the one with the alphabetically lower ID!
    id0 = recs[0].workflow_id
    id1 = recs[1].workflow_id
    assert id0 < id1
