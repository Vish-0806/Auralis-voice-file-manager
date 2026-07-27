"""Unit tests for the AI Brain and Memory integration."""

from unittest.mock import MagicMock
# pyrefly: ignore [missing-import]
import pytest
import asyncio

from brain.controller.brain_controller import BrainController
from brain.controller.models import BrainRequest
from core.models import ExecutionResult
from memory import MemoryService, MemoryType


@pytest.fixture
def mock_dispatcher():
    """Returns a mock dispatcher."""
    dispatcher = MagicMock()
    dispatcher._capabilities = {"desktop": MagicMock(), "mock_file": MagicMock(), "workflow": MagicMock()}
    dispatcher.dispatch.return_value = ExecutionResult(
        success=True,
        response="Executed successfully",
        data={},
        execution_time=0.01,
    )
    return dispatcher


def test_brain_controller_saves_memories(mock_dispatcher) -> None:
    """Verify that BrainController correctly utilizes MemoryService to save request/response/activity."""
    # Use MemoryService with default in_memory provider
    memory_service = MemoryService()
    
    controller = BrainController(memory_service=memory_service)
    
    # Process a request
    req = BrainRequest(
        message="start coding",
        correlation_id="test_integration_corr_id",
    )
    
    res = controller.process_request(req, mock_dispatcher)
    
    assert res.success is True
    
    # Retrieve all memories asynchronously using the service
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    all_memories = loop.run_until_complete(memory_service.list())
    
    # Assertions on captured memories
    assert len(all_memories) == 5
    
    # 1. User Prompt Conversation Memory
    user_mem = next(m for m in all_memories if m.id.endswith("_user"))
    assert user_mem.content == "start coding"
    assert user_mem.memory_type == MemoryType.CONVERSATION
    assert user_mem.metadata.additional_info.get("role") == "user"
    assert user_mem.metadata.additional_info.get("session_id") == "test_integration_corr_id"
    
    # 2. Assistant Response Conversation Memory
    assistant_mem = next(m for m in all_memories if m.id.endswith("_assistant"))
    assert assistant_mem.memory_type == MemoryType.CONVERSATION
    assert assistant_mem.metadata.additional_info.get("role") == "assistant"
    
    # 3. Execution Activity Memory
    activity_mem = next(m for m in all_memories if m.id.endswith("_activity"))
    assert activity_mem.memory_type == MemoryType.ACTIVITY
    assert "Execution completed" in activity_mem.content
    assert activity_mem.metadata.additional_info.get("status") == "COMPLETED"
