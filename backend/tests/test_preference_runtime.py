# pyrefly: ignore [missing-import]
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch, ANY

from core.intents import Intent
from core.models import ExecutionPlan as CoreExecutionPlan
from memory.models.domain_models import MemoryEntry, MemoryMetadata, MemoryType, AssistantContext
from memory import MemoryService
from memory.manager.context_builder import ContextBuilder, ContextWindowConfig
from brain.controller.brain_pipeline import BrainPipeline
from brain.planning.task_planner import TaskPlanner
from brain.execution.execution_engine import ExecutionEngine
from brain.capability.models import RoutedExecutionPlan, CapabilityRoute
from brain.reasoning.models import Objective, Priority, ReasoningResult

@pytest.mark.anyio
async def test_context_builder_loads_resolved_preferences():
    # Setup mock MemoryService
    memory_service = AsyncMock(spec=MemoryService)
    
    # Mock get_user_preferences to return raw entries
    raw_pref = MemoryEntry(
        id="Browser",
        content="Firefox",
        memory_type=MemoryType.PREFERENCE,
        metadata=MemoryMetadata(additional_info={"user_id": 99, "value": "Firefox"})
    )
    memory_service.get_user_preferences.return_value = [raw_pref]
    
    # Mock get_resolved_preferences
    memory_service.get_resolved_preferences.return_value = {"Browser": "Firefox"}
    memory_service.get_latest_context.return_value = None
    
    builder = ContextBuilder(memory_service=memory_service)
    
    context = await builder.build_context(user_id=99)
    
    assert context.resolved_preferences == {"Browser": "Firefox"}
    memory_service.get_resolved_preferences.assert_called_once_with(99)

@pytest.mark.anyio
async def test_brain_pipeline_receives_preferences_and_logs(caplog):
    import logging
    config = MagicMock()
    config.confidence_threshold = 0.5
    
    interpreter = MagicMock()
    goal_res = MagicMock()
    goal_res.goal.name = "RUN_WORKFLOW"
    goal_res.confidence.score = 0.8
    interpreter.interpret.return_value = goal_res
    
    reasoning_engine = MagicMock()
    reasoning_res = ReasoningResult(
        goal_name="RUN_WORKFLOW",
        objective=Objective(title="Run workflow", description="", target=""),
        required_capabilities=["workflow"],
        constraints=[],
        priority=Priority.CRITICAL,
        estimated_complexity="LOW"
    )
    reasoning_engine.reason.return_value = reasoning_res
    
    planner = MagicMock(spec=TaskPlanner)
    plan = CoreExecutionPlan(intent=Intent.RUN_WORKFLOW, target="macro", confidence=0.8)
    planner.plan.return_value = plan
    
    capability_selector = MagicMock()
    routed_plan = RoutedExecutionPlan(intent=Intent.RUN_WORKFLOW, target="macro", confidence=0.8)
    capability_selector.select_capabilities.return_value = routed_plan
    
    execution_engine = MagicMock()
    summary = MagicMock()
    summary.success = True
    execution_engine.execute_plan.return_value = summary
    execution_engine._progress_monitor._metrics_collector.get_metrics.return_value = {}
    
    pipeline = BrainPipeline(
        config=config,
        interpreter=interpreter,
        reasoning_engine=reasoning_engine,
        planner=planner,
        capability_selector=capability_selector,
        execution_engine=execution_engine,
        logger=logging.getLogger("BrainPipelineTest")
    )
    
    context = AssistantContext(
        resolved_preferences={"Browser": "Firefox", "Shell": "Bash"},
        metadata={"user_id": 99}
    )
    
    with caplog.at_level(logging.INFO):
        response = pipeline.execute("run workflow", dispatcher=MagicMock(), context=context)
    
    assert response.success is True
    assert any("Resolved Preferences Loaded" in record.message for record in caplog.records)
    execution_engine.execute_plan.assert_called_once_with(routed_plan, ANY, user_id=99)

def test_task_planner_applies_preferences_and_system_defaults():
    planner = TaskPlanner()
    reasoning = ReasoningResult(
        goal_name="RUN_WORKFLOW",
        objective=Objective(title="Run workflow", description="", target=""),
        required_capabilities=["workflow"],
        constraints=[],
        priority=Priority.CRITICAL,
        estimated_complexity="LOW"
    )
    
    mock_step = MagicMock()
    mock_step.intent = Intent.RUN_WORKFLOW
    mock_step.target = None
    mock_step.parameters = {}
    
    with patch.object(planner._plan_optimizer, "optimize_plan", return_value=[mock_step]):
        context = AssistantContext(
            resolved_preferences={"Browser": "Firefox"},
            metadata={"user_id": 99}
        )
        plan = planner.plan(reasoning, confidence=0.8, context=context)
        
        assert plan.parameters["shell"] == "PowerShell"
        assert plan.parameters["ide"] == "VS Code"
        assert plan.parameters["browser"] == "Firefox"

def test_task_planner_does_not_override_explicit_user_choices():
    planner = TaskPlanner()
    reasoning = ReasoningResult(
        goal_name="RUN_WORKFLOW",
        objective=Objective(title="Run workflow", description="", target=""),
        required_capabilities=["workflow"],
        constraints=[],
        priority=Priority.CRITICAL,
        estimated_complexity="LOW"
    )
    
    mock_step = MagicMock()
    mock_step.intent = Intent.RUN_WORKFLOW
    mock_step.target = None
    mock_step.parameters = {"shell": "Bash", "browser": "Chrome", "ide": "PyCharm"}
    
    with patch.object(planner._plan_optimizer, "optimize_plan", return_value=[mock_step]):
        context = AssistantContext(
            resolved_preferences={"Shell": "PowerShell", "Browser": "Firefox", "IDE": "VS Code"},
            metadata={"user_id": 99}
        )
        plan = planner.plan(reasoning, confidence=0.8, context=context)
        
        assert plan.parameters["shell"] == "Bash"
        assert plan.parameters["browser"] == "Chrome"
        assert plan.parameters["ide"] == "PyCharm"

@pytest.mark.anyio
async def test_execution_engine_records_observations_and_triggers_coordinator(caplog):
    import logging
    validator = MagicMock()
    scheduler = MagicMock()
    history = MagicMock()
    progress_monitor = MagicMock()
    
    routes = [CapabilityRoute(step_id="step_1", intent=Intent.RUN_WORKFLOW, capability_name="workflow_execution")]
    scheduler.schedule_steps.return_value = routes
    
    engine = ExecutionEngine(
        validator=validator,
        scheduler=scheduler,
        history=history,
        progress_monitor=progress_monitor,
        logger=logging.getLogger("ExecutionEngineTest")
    )
    
    plan = RoutedExecutionPlan(
        intent=Intent.RUN_WORKFLOW,
        target="echo 1",
        confidence=0.8,
        routes=routes,
        parameters={"shell": "Bash", "browser": "Firefox"}
    )
    
    dispatcher = MagicMock()
    dispatcher.dispatch.return_value = MagicMock(success=True, execution_time=0.1, response="ok", data={})
    
    with patch("memory.MemoryService") as mock_mem_class, \
         patch("memory.preferences.PreferenceLearningCoordinator") as mock_coordinator_class:
        
        mock_mem = AsyncMock()
        mock_mem_class.return_value = mock_mem
        
        mock_coordinator = AsyncMock()
        mock_coordinator_class.return_value = mock_coordinator
        
        with caplog.at_level(logging.INFO):
            summary = engine.execute_plan(plan, dispatcher, user_id=99)
            
            assert summary.success is True
            assert any("Preference Observation Recorded" in record.message for record in caplog.records)
            assert any("Preference Learning Triggered" in record.message for record in caplog.records)
            
            mock_mem.save.assert_called_once()
            mock_coordinator.process_new_execution.assert_called_once_with(99, ANY)
