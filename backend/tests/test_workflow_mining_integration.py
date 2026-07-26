# pyrefly: ignore [missing-import]
import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from core.intents import Intent
from memory import MemoryService
from memory.workflows import WorkflowStepObservation, WorkflowSequence, WorkflowObservation
from automation.workflow.workflow_registry import WorkflowRegistry
from brain.planning.workflow_library import WorkflowLibrary


def create_observation(user_id: int, execution_id: str, intents: list[str], session_id: str = "session_A") -> WorkflowObservation:
    steps = []
    t = datetime.now(timezone.utc)
    for i, intent in enumerate(intents):
        steps.append(
            WorkflowStepObservation(
                step_id=f"s_{i}",
                intent=intent,
                status="SUCCESS",
                duration_ms=100.0,
                timestamp=t
            )
        )
    seq = WorkflowSequence(
        steps=steps,
        sequence_id=f"seq_{execution_id}",
        sequence_hash=f"hash_{execution_id}",
        total_duration_ms=100.0 * len(intents)
    )
    return WorkflowObservation(
        user_id=user_id,
        execution_id=execution_id,
        sequence=seq,
        success=True,
        timestamp=t,
        context_metadata={"session_id": session_id}
    )


@pytest.mark.anyio
async def test_workflow_mining_integration_async_promotion():
    # Reset registry dynamic state before test
    WorkflowRegistry._dynamic_registry.clear()
    
    memory_service = MemoryService()
    
    # Save 3 identical observations to satisfy default min_support=3 threshold for mining
    obs1 = create_observation(user_id=7, execution_id="ex1", intents=["OPEN_APPLICATION", "SET_VOLUME"])
    obs2 = create_observation(user_id=7, execution_id="ex2", intents=["OPEN_APPLICATION", "SET_VOLUME"])
    obs3 = create_observation(user_id=7, execution_id="ex3", intents=["OPEN_APPLICATION", "SET_VOLUME"])
    
    # Save observations via memory service
    await memory_service.save_workflow_observation(obs1)
    await memory_service.save_workflow_observation(obs2)
    await memory_service.save_workflow_observation(obs3)
    
    # Wait briefly to let the background task _run_mining complete
    await asyncio.sleep(0.2)
    
    # Verify that the workflow has been dynamically registered in WorkflowRegistry!
    registry = WorkflowRegistry()
    workflows = registry.list_workflows()
    
    mined_workflow = next((w for w in workflows if "Mined Workflow wf_" in w.name), None)
    assert mined_workflow is not None
    assert len(mined_workflow.steps) == 2
    assert mined_workflow.steps[0].intent == Intent.OPEN_APPLICATION
    assert mined_workflow.steps[1].intent == Intent.SET_VOLUME
    
    # Verify visibility in WorkflowLibrary
    library = WorkflowLibrary(registry=registry)
    library_workflow = library.get_workflow(mined_workflow.name)
    assert library_workflow == mined_workflow


@pytest.mark.anyio
async def test_workflow_mining_graceful_recovery_on_failure(caplog):
    import logging
    memory_service = MemoryService()
    
    # Set up observation
    obs = create_observation(user_id=8, execution_id="ex_fail", intents=["MUTE"])
    
    # Force _run_mining to raise an exception by mocking get_workflow_sequences
    with patch.object(memory_service._manager, "get_workflow_sequences", side_effect=RuntimeError("Mock DB Error")):
        with caplog.at_level(logging.WARNING):
            # Saving should complete successfully and not throw any exception
            await memory_service.save_workflow_observation(obs)
            await asyncio.sleep(0.1)
            
    # Verify warning was logged
    assert any("Workflow mining execution failed gracefully" in record.message for record in caplog.records)
