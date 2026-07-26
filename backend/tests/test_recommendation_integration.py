# pyrefly: ignore [missing-import]
import pytest
import hashlib
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from core.intents import Intent
from memory import MemoryService, AssistantContext
from memory.models.domain_models import MemoryEntry, MemoryType, MemoryMetadata, WorkspaceAnalysis
from brain.controller.brain_controller import BrainController
from brain.controller.models import BrainRequest
from automation.workflow.workflow_registry import WorkflowRegistry


def test_recommendation_pipeline_runtime_invocation_and_attachment():
    # Reset registry dynamic state
    WorkflowRegistry._dynamic_registry.clear()
    
    controller = BrainController()
    
    # Pre-populate dynamic registry with a mined workflow definition to recommend
    from automation.workflow.models import WorkflowDefinition, WorkflowStep
    wf = WorkflowDefinition(
        name="Mined Workflow wf_123456789abc",
        description="Mined dev workspace workflow",
        steps=[
            WorkflowStep(intent=Intent.OPEN_APPLICATION, target="VS Code", parameters={})
        ]
    )
    WorkflowRegistry._dynamic_registry[wf.name] = wf

    # Build valid WorkspaceAnalysis model
    analysis = WorkspaceAnalysis(
        workspace_path="C:/Projects/Auralis",
        project_name="Auralis",
        project_type="python",
        repository_type="git",
        dominant_language="python",
        language_statistics={},
        language_counts={},
        total_files=10,
        total_directories=2,
        maximum_depth=2,
        total_size=1000,
        last_indexed=datetime.now(timezone.utc),
        analysis_timestamp=datetime.now(timezone.utc)
    )
    
    # Build current_context with active window information
    current_context = MemoryEntry(
        id="current_state",
        content="C:/Projects/Auralis",
        memory_type=MemoryType.ACTIVITY,
        metadata=MemoryMetadata(
            created_at=datetime.now(timezone.utc),
            additional_info={
                "active_window": "Visual Studio Code",
                "active_directory": "C:/Projects/Auralis",
                "workspace_path": "C:/Projects/Auralis"
            }
        )
    )
    
    context = AssistantContext(
        workspace_analysis=analysis,
        current_context=current_context,
        metadata={"user_id": 1, "session_id": "session_X"},
        recent_workflows=[],
        historical_feedback={}
    )
    
    req = BrainRequest(message="open dev space", correlation_id="session_X")
    
    summary_mock = MagicMock()
    summary_mock.success = True
    summary_mock.error = None
    
    with patch("memory.manager.context_builder.ContextBuilder.build_context", return_value=context):
        with patch("brain.execution.execution_engine.ExecutionEngine.execute_plan", return_value=summary_mock):
            response = controller.process_request(req, dispatcher=MagicMock())
            
            assert response.success is True
            assert response.recommendations is not None
            assert len(response.recommendations) > 0
            
            rec = response.recommendations[0]
            assert rec.workflow_name == wf.name
            assert rec.confidence > 0.0


@pytest.mark.anyio
async def test_recommendation_feedback_persistence_and_learning_influence():
    WorkflowRegistry._dynamic_registry.clear()
    
    from automation.workflow.models import WorkflowDefinition, WorkflowStep
    wf = WorkflowDefinition(
        name="Mined Workflow wf_feed12345678",
        description="Mined testing workflow",
        steps=[
            WorkflowStep(intent=Intent.OPEN_APPLICATION, target="VS Code", parameters={})
        ]
    )
    WorkflowRegistry._dynamic_registry[wf.name] = wf

    memory_service = MemoryService()
    
    user_id = 99
    # Deterministic workflow ID from name hash
    wf_hash = hashlib.sha256(wf.name.encode("utf-8")).hexdigest()[:12]
    workflow_id = f"wf_{wf_hash}"
    
    from memory.recommendations import RecommendationContext, RecommendationEngine
    
    # Active workspace matching "VS Code"
    workspace_analysis_dict = {
        "active_window": "Visual Studio Code",
        "active_directory": "C:/Projects/Auralis"
    }
    
    ctx_initial = RecommendationContext(
        user_id=user_id,
        session_id="session_initial",
        workspace_analysis=workspace_analysis_dict,
        recent_workflows=[],
        historical_feedback={}
    )
    
    engine = RecommendationEngine()
    scored_initial = engine.score_workflows(ctx_initial, [wf])
    initial_score = scored_initial[0][1].final_score
    assert initial_score > 0.5
    
    # 1. Test Acceptance learning (increases score by 0.1)
    ctx_acc = RecommendationContext(
        user_id=user_id,
        session_id="session_acc",
        workspace_analysis=workspace_analysis_dict,
        recent_workflows=[],
        historical_feedback={workflow_id: ["accepted"]}
    )
    scored_acc = engine.score_workflows(ctx_acc, [wf])
    acc_score = scored_acc[0][1].final_score
    assert acc_score > initial_score
    assert pytest.approx(acc_score - initial_score, 0.01) == 0.1
    
    # 2. Test Rejection Penalty (decreases score by 0.2)
    ctx_rej = RecommendationContext(
        user_id=user_id,
        session_id="session_rej",
        workspace_analysis=workspace_analysis_dict,
        recent_workflows=[],
        historical_feedback={workflow_id: ["rejected"]}
    )
    scored_rej = engine.score_workflows(ctx_rej, [wf])
    rej_score = scored_rej[0][1].final_score
    assert rej_score < initial_score
    assert pytest.approx(initial_score - rej_score, 0.01) == 0.2

    # 3. Test Ignored penalty (decreases score by 0.05)
    ctx_ign = RecommendationContext(
        user_id=user_id,
        session_id="session_ign",
        workspace_analysis=workspace_analysis_dict,
        recent_workflows=[],
        historical_feedback={workflow_id: ["ignored"]}
    )
    scored_ign = engine.score_workflows(ctx_ign, [wf])
    ign_score = scored_ign[0][1].final_score
    assert rej_score < ign_score < initial_score
    assert pytest.approx(initial_score - ign_score, 0.01) == 0.05

    # 4. Verify memory feedback persistence API
    await memory_service.record_recommendation_acceptance(user_id=user_id, workflow_id=workflow_id)
    await memory_service.record_recommendation_rejection(user_id=user_id, workflow_id=workflow_id)
    await memory_service.record_recommendation_ignored(user_id=user_id, workflow_id=workflow_id)
    
    from memory.models.domain_models import MemoryQuery
    query = MemoryQuery(
        text="",
        memory_type=MemoryType.PREFERENCE,
        filters={"type": "recommendation_feedback", "user_id": user_id}
    )
    results = await memory_service.search(query)
    assert len(results) == 3
    statuses = [res.entry.content for res in results]
    assert "accepted" in statuses
    assert "rejected" in statuses
    assert "ignored" in statuses
