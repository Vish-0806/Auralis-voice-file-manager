"""Tests for the workflow automation engine capability and its subcomponents."""

from __future__ import annotations

# pyrefly: ignore [missing-import]
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, UTC

from core.assistant import AuralisAssistant
from core.dispatcher import ActionDispatcher
from core.planner import Planner
from core.models import AssistantRequest, ExecutionResult
from core.intents import Intent
from capabilities.desktop.desktop_capability import DesktopCapability
from automation.workflow.workflow_parser import WorkflowParser
from automation.workflow.workflow_registry import WorkflowRegistry
from automation.workflow.workflow_validator import WorkflowValidator
from automation.workflow.workflow_executor import WorkflowExecutor
from automation.workflow.workflow_engine import WorkflowEngine


# --- WorkflowParser Tests ---

def test_workflow_parser_normalization():
    parser = WorkflowParser()
    assert parser.parse_workflow_name("start coding now") == "Start Coding"
    assert parser.parse_workflow_name("study") == "Study Mode"
    assert parser.parse_workflow_name("meeting mode") == "Meeting Mode"
    assert parser.parse_workflow_name("movie mode") == "Movie Mode"
    assert parser.parse_workflow_name("clean workspace") == "Clean Workspace"
    assert parser.parse_workflow_name("unknown workflow") == "Unknown Workflow"


# --- WorkflowRegistry and Validator Tests ---

def test_workflow_registry_and_validator():
    reg = WorkflowRegistry()
    val = WorkflowValidator()

    coding_wf = reg.get_workflow("Start Coding")
    assert coding_wf is not None
    assert len(coding_wf.steps) == 3
    assert val.validate(coding_wf) is True

    from automation.workflow.models import WorkflowDefinition, WorkflowStep
    invalid_wf = WorkflowDefinition(
        name="Invalid App Mode",
        description="Invalid app dependency",
        steps=[WorkflowStep(intent=Intent.OPEN_APPLICATION, target="InvalidAppName123")],
    )
    assert val.validate(invalid_wf) is False


# --- WorkflowExecutor Tests ---

def test_workflow_executor_sequential_runs():
    reg = WorkflowRegistry()
    exec_wf = WorkflowExecutor()
    mock_dispatcher = MagicMock()
    mock_dispatcher.dispatch.return_value = ExecutionResult(success=True, response="Step succeeded", execution_time=0.1)

    coding_wf = reg.get_workflow("Start Coding")
    result = exec_wf.execute(coding_wf, mock_dispatcher)

    assert result.success is True
    assert len(exec_wf.history_logs) == 3
    assert exec_wf.history_logs[0]["success"] is True


# --- End-to-End Pipeline Integration Tests ---

@patch.object(DesktopCapability, "execute_plan")
def test_integration_workflow_commands(mock_desktop_exec):
    mock_desktop_exec.return_value = ExecutionResult(success=True, response="Mocked desktop execution", execution_time=0.1)

    planner = Planner()
    desktop_cap = DesktopCapability()
    workflow_engine = WorkflowEngine()
    dispatcher = ActionDispatcher(capabilities={
        desktop_cap.name: desktop_cap,
        workflow_engine.name: workflow_engine,
    })
    workflow_engine.set_dispatcher(dispatcher)
    assistant = AuralisAssistant(planner=planner, dispatcher=dispatcher)

    # 1. Start Coding
    req = AssistantRequest(
        message="Start Coding",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)
    assert res.result.success is True
    assert res.plan.intent == Intent.RUN_WORKFLOW
    assert res.plan.target == "Start Coding"

    # 2. Study Mode
    req = AssistantRequest(
        message="Study Mode",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)
    assert res.result.success is True
    assert res.plan.intent == Intent.RUN_WORKFLOW
    assert res.plan.target == "Study Mode"

    # 3. Meeting Mode
    req = AssistantRequest(
        message="Meeting Mode",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)
    assert res.result.success is True
    assert res.plan.intent == Intent.RUN_WORKFLOW
    assert res.plan.target == "Meeting Mode"

    # 4. Movie Mode
    req = AssistantRequest(
        message="Movie Mode",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)
    assert res.result.success is True
    assert res.plan.intent == Intent.RUN_WORKFLOW
    assert res.plan.target == "Movie Mode"

    # 5. List Workflows
    req = AssistantRequest(
        message="List Workflows",
        source="test",
        timestamp=datetime.now(UTC),
    )
    res = assistant.process_request(req)
    assert res.result.success is True
    assert res.plan.intent == Intent.LIST_WORKFLOWS
    assert "Start Coding" in res.response
    assert "Study Mode" in res.response
