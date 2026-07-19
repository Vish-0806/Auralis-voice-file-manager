"""End-to-end integration tests for the Auralis AI Brain Controller orchestrator."""

from __future__ import annotations

from datetime import datetime, UTC
from unittest.mock import MagicMock, patch
# pyrefly: ignore [missing-import]
import pytest

from core.assistant import AuralisAssistant
from core.intents import Intent
from core.models import AssistantRequest, ExecutionResult
from brain.controller.models import BrainRequest, BrainStatus
from brain.controller.brain_controller import BrainController
from brain.planning.task_planner import TaskPlanner
from brain.execution.models import ExecutionStatus


@pytest.fixture
def mock_dispatcher():
    """Returns a mock dispatcher that records calls and supports recovery testing."""
    dispatcher = MagicMock()
    dispatcher._capabilities = {"desktop": MagicMock(), "mock_file": MagicMock(), "workflow": MagicMock()}

    def dispatch_side_effect(plan, context=None):
        target = plan.target
        intent = plan.intent

        # Chrome fails to trigger recovery testing
        if intent == Intent.OPEN_APPLICATION and target in ["Chrome", "Google Chrome"]:
            return ExecutionResult(
                success=False,
                response="",
                error="Could not resolve executable path for Chrome",
                execution_time=0.01,
            )
        
        return ExecutionResult(
            success=True,
            response=f"Executed {intent.value} on {target or 'system'}",
            data={},
            execution_time=0.01,
        )

    dispatcher.dispatch.side_effect = dispatch_side_effect
    return dispatcher


# --- E2E Integration Scenario Tests ---

def test_controller_start_coding(mock_dispatcher):
    """E2E Test: Start Coding goal triggers VS Code, Terminal, and volume configuration."""
    controller = BrainController()
    req = BrainRequest(
        message="start coding",
        correlation_id="test_start_coding",
    )
    
    res = controller.process_request(req, mock_dispatcher)
    
    assert res.success is True
    assert res.goal_name == "START_CODING"
    assert len(res.summary.records) == 3
    assert res.summary.records[0].intent == Intent.OPEN_APPLICATION
    assert res.summary.records[0].capability == "Desktop"
    assert res.summary.records[2].intent == Intent.SET_VOLUME


def test_controller_study_mode_with_chrome_recovery(mock_dispatcher):
    """E2E Test: Study Mode triggers Chrome launch, fails, and recovers via Microsoft Edge."""
    from automation.workflow.models import WorkflowDefinition, WorkflowStep
    from automation.workflow.workflow_registry import WorkflowRegistry
    from core.models import ExecutionPlan as CoreExecutionPlan

    # Register dynamic workflow with Chrome as step 1
    WorkflowRegistry._dynamic_registry["Study Mode"] = WorkflowDefinition(
        name="Study Mode",
        description="Focused study workflow using Chrome",
        steps=[
            WorkflowStep(intent=Intent.OPEN_APPLICATION, target="Chrome"),
            WorkflowStep(intent=Intent.MUTE),
        ],
    )

    controller = BrainController()
    req = BrainRequest(
        message="study mode",
        correlation_id="test_study_mode",
    )

    # Force TaskPlanner to plan a dynamic RUN_WORKFLOW to use our dynamically registered study mode
    mock_plan = CoreExecutionPlan(
        intent=Intent.RUN_WORKFLOW,
        target="Study Mode",
        confidence=1.0,
    )

    with patch.object(TaskPlanner, "plan", return_value=mock_plan):
        res = controller.process_request(req, mock_dispatcher)
    
    WorkflowRegistry._dynamic_registry.pop("Study Mode", None)

    assert res.success is True
    assert res.goal_name == "STUDY"
    assert len(res.summary.records) == 2
    assert res.summary.records[0].intent == Intent.OPEN_APPLICATION
    assert res.summary.records[0].status == ExecutionStatus.SUCCESS
    assert "Recovered" in res.summary.records[0].response
    assert res.summary.records[1].intent == Intent.MUTE
    assert res.metrics.recovery_count == 1


def test_controller_meeting_prep(mock_dispatcher):
    """E2E Test: Meeting Prep workspace setups (Notepad, mute volume, show desktop)."""
    controller = BrainController()
    req = BrainRequest(
        message="meeting mode",
        correlation_id="test_meeting_prep",
    )

    res = controller.process_request(req, mock_dispatcher)

    assert res.success is True
    assert res.goal_name == "MEETING"
    assert len(res.summary.records) == 3
    assert res.summary.records[0].intent == Intent.OPEN_APPLICATION
    assert res.summary.records[1].intent == Intent.MUTE
    assert res.summary.records[2].intent == Intent.SHOW_DESKTOP


def test_controller_downloads_organization(mock_dispatcher):
    """E2E Test: Downloads clean/organization targets File capability routing."""
    controller = BrainController()
    req = BrainRequest(
        message="clean downloads",
        correlation_id="test_downloads_org",
    )

    res = controller.process_request(req, mock_dispatcher)

    assert res.success is True
    assert res.goal_name == "ORGANIZE_DOWNLOADS"
    assert len(res.summary.records) == 1
    assert res.summary.records[0].capability == "File"


# --- Assistant Integration Tests ---

def test_assistant_brain_routing_success(mock_dispatcher):
    """Validates that AuralisAssistant routes requests successfully via BrainController."""
    from core.planner import Planner
    planner = Planner()
    assistant = AuralisAssistant(planner=planner, dispatcher=mock_dispatcher)

    req = AssistantRequest(
        message="start coding",
        source="test_client",
        timestamp=datetime.now(UTC),
    )

    response = assistant.process_request(req)

    assert response.response == "Pipeline completed successfully."
    assert response.plan.target == "Start Coding"
    assert response.result.success is True
    assert "execution_id" in response.result.data


def test_controller_context_builder_integration(mock_dispatcher):
    """Verifies that ContextBuilder is invoked and AssistantContext is passed to the pipeline."""
    from unittest.mock import patch
    from memory import AssistantContext
    from brain.controller.brain_pipeline import BrainPipeline

    controller = BrainController()
    req = BrainRequest(
        message="start coding",
        correlation_id="test_ctx_integration",
        context={"user_id": 999}
    )

    # Let's mock the pipeline's execute method to capture what context is received
    captured_context = None
    orig_execute = BrainPipeline.execute

    def mock_execute(self, message, dispatcher, context=None):
        nonlocal captured_context
        captured_context = context
        return orig_execute(self, message, dispatcher, context=context)

    with patch.object(BrainPipeline, "execute", side_effect=mock_execute, autospec=True):
        res = controller.process_request(req, mock_dispatcher)

    assert res.success is True
    assert isinstance(captured_context, AssistantContext)
    assert captured_context.metadata.get("user_id") == 999


def test_controller_context_builder_failure_grace(mock_dispatcher):
    """Verifies that if ContextBuilder fails, the pipeline still executes with an empty AssistantContext."""
    from unittest.mock import patch
    from memory import AssistantContext
    from brain.controller.brain_pipeline import BrainPipeline
    from memory.manager.context_builder import ContextBuilder

    controller = BrainController()
    req = BrainRequest(
        message="start coding",
        correlation_id="test_ctx_failure_grace",
        context={"user_id": 999}
    )

    async def raise_error(*args, **kwargs):
        raise RuntimeError("Mock context builder failure")

    captured_context = None
    orig_execute = BrainPipeline.execute

    def mock_execute(self, message, dispatcher, context=None):
        nonlocal captured_context
        captured_context = context
        return orig_execute(self, message, dispatcher, context=context)

    with patch.object(ContextBuilder, "build_context", side_effect=raise_error):
        with patch.object(BrainPipeline, "execute", side_effect=mock_execute, autospec=True):
            res = controller.process_request(req, mock_dispatcher)

    assert res.success is True
    assert isinstance(captured_context, AssistantContext)
    # The failed context builder should fallback to an empty context
    assert len(captured_context.recent_conversations) == 0
    assert len(captured_context.recent_executions) == 0
    assert captured_context.current_context is None
