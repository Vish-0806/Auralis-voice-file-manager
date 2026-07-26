# pyrefly: ignore [missing-import]
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch, ANY

from core.intents import Intent
from memory import MemoryService
from memory.workflows import (
    WorkflowStepObservation,
    WorkflowSequence,
    WorkflowObservation,
    WorkflowObserver,
)
from brain.execution.execution_engine import ExecutionEngine
from brain.capability.models import RoutedExecutionPlan, CapabilityRoute


@pytest.mark.anyio
async def test_execution_engine_invokes_observer():
    mock_observer = AsyncMock(spec=WorkflowObserver)
    
    # Setup scheduler, history, progress monitor, validator
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
        workflow_observer=mock_observer
    )
    
    plan = RoutedExecutionPlan(
        intent=Intent.RUN_WORKFLOW,
        target="echo 1",
        confidence=0.8,
        routes=routes,
        parameters={"my_param": "value"}
    )
    
    dispatcher = MagicMock()
    dispatcher.dispatch.return_value = MagicMock(success=True, execution_time=0.1, response="ok", data={})
    
    import asyncio
    summary = engine.execute_plan(plan, dispatcher, user_id=99)
    await asyncio.sleep(0.1)
    
    assert summary.success is True
    # Verify observe_execution was invoked
    mock_observer.observe_execution.assert_called_once()
    args, kwargs = mock_observer.observe_execution.call_args
    assert kwargs["user_id"] == 99
    assert kwargs["success"] is True
    assert len(kwargs["steps"]) == 1
    assert kwargs["steps"][0].step_id == "step_1"


@pytest.mark.anyio
async def test_execution_engine_graceful_observation_failure(caplog):
    import logging
    mock_observer = AsyncMock(spec=WorkflowObserver)
    mock_observer.observe_execution.side_effect = RuntimeError("Failed database write")
    
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
        workflow_observer=mock_observer,
        logger=logging.getLogger("ExecutionEngineWorkflowFailureTest")
    )
    
    plan = RoutedExecutionPlan(
        intent=Intent.RUN_WORKFLOW,
        target="echo 1",
        confidence=0.8,
        routes=routes,
        parameters={}
    )
    
    dispatcher = MagicMock()
    dispatcher.dispatch.return_value = MagicMock(success=True, execution_time=0.1, response="ok", data={})
    
    import asyncio
    with caplog.at_level(logging.WARNING):
        summary = engine.execute_plan(plan, dispatcher, user_id=99)
        await asyncio.sleep(0.1)
        
    # The execution must succeed even if observation fails
    assert summary.success is True
    # Warning must be logged
    assert any("Workflow observation recording encountered a failure" in record.message for record in caplog.records)


@pytest.mark.anyio
async def test_memory_service_workflow_delegation():
    # Setup mock MemoryManager
    mock_manager = AsyncMock()
    memory_service = MemoryService()
    memory_service._manager = mock_manager
    
    # 1. save_workflow_observation
    obs = MagicMock(spec=WorkflowObservation)
    await memory_service.save_workflow_observation(obs)
    mock_manager.save_workflow_observation.assert_called_once_with(obs)
    
    # 2. get_workflow_observations
    mock_manager.get_workflow_observations.return_value = ["obs1", "obs2"]
    res1 = await memory_service.get_workflow_observations(user_id=123)
    assert res1 == ["obs1", "obs2"]
    mock_manager.get_workflow_observations.assert_called_once_with(123)
    
    # 3. get_workflow_sequences
    mock_manager.get_workflow_sequences.return_value = ["seq1"]
    res2 = await memory_service.get_workflow_sequences(user_id=123)
    assert res2 == ["seq1"]
    mock_manager.get_workflow_sequences.assert_called_once_with(123)
