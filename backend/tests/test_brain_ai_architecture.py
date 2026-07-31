"""Unit tests for Auralis AI Architecture Foundation (Phase 10.1).

Validates:
- Import resolution & package structure
- ABC enforcement for abstract interfaces
- ProviderManager lifecycle & health status
- DefaultContextBuilder & DefaultPromptBuilder snapshot generation
- DefaultToolRouter tool registration, categorization, and routing stubs
- AIOrchestrator pipeline sequence with stubbed AIProvider
- Exception hierarchy handling
"""

# pyrefly: ignore [missing-import]
import pytest
from typing import Any, Dict
from datetime import datetime, timezone

from brain.runtime.brain_models import BrainRequest, PipelineStatus
from brain.ai import (
    AIContext,
    AIException,
    AIOrchestrationError,
    AIOrchestrator,
    AIProvider,
    AIRequest,
    AIResponse,
    ContextBuilder,
    ContextBuildError,
    DefaultContextBuilder,
    DefaultPromptBuilder,
    DefaultToolRouter,
    FinishReason,
    Prompt,
    PromptBuilder,
    PromptBuildError,
    ProviderInfo,
    ProviderManager,
    ProviderNotFoundError,
    ProviderRegistrationError,
    ProviderUnavailableError,
    ToolCall,
    ToolCategory,
    ToolResult,
    ToolRouter,
    ToolRoutingError,
)


class StubAIProvider(AIProvider):
    """Stub AIProvider for testing architecture contracts without external APIs."""

    def __init__(
        self,
        name: str = "stub-provider",
        available: bool = True,
        response_text: str = "Stubbed AI response",
    ):
        self._name = name
        self._available = available
        self._response_text = response_text

    def get_info(self) -> ProviderInfo:
        return ProviderInfo(
            provider_id=f"id-{self._name}",
            name=self._name,
            version="1.0.0",
            is_available=self._available,
            supported_features=["text_completion", "tool_calling"],
            max_context_window=32768,
            default_model_name="stub-model-v1",
        )

    def generate_response(self, request: AIRequest) -> AIResponse:
        if not self._available:
            raise ProviderUnavailableError(self._name)
        return AIResponse(
            response_id="res-123",
            request_id=request.request_id,
            text=self._response_text,
            tool_calls=[],
            finish_reason=FinishReason.STOP,
            usage_stats={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            raw_response={"stub": True},
            provider_name=self._name,
        )

    def is_available(self) -> bool:
        return self._available

    def health_check(self) -> Dict[str, Any]:
        return {"status": "ok" if self._available else "degraded", "latency_ms": 1.2}


# ---------------------------------------------------------------------------
# Tests: Package & ABC Interfaces
# ---------------------------------------------------------------------------


def test_abc_interface_instantiation_protection():
    """Ensure ABC interfaces cannot be instantiated directly."""
    with pytest.raises(TypeError):
        AIProvider()  # type: ignore

    with pytest.raises(TypeError):
        ContextBuilder()  # type: ignore

    with pytest.raises(TypeError):
        PromptBuilder()  # type: ignore

    with pytest.raises(TypeError):
        ToolRouter()  # type: ignore


# ---------------------------------------------------------------------------
# Tests: ProviderManager
# ---------------------------------------------------------------------------


def test_provider_manager_lifecycle():
    """Test ProviderManager registration, selection, unregistration, and health checks."""
    manager = ProviderManager()
    assert manager.get_active_provider() is None
    assert manager.list_providers() == []

    p1 = StubAIProvider(name="ProviderAlpha")
    p2 = StubAIProvider(name="ProviderBeta", available=False)

    # Register p1
    manager.register_provider(p1)
    assert manager.get_active_provider() == p1
    assert len(manager.list_providers()) == 1

    # Duplicate registration error
    with pytest.raises(ProviderRegistrationError):
        manager.register_provider(p1)

    # Register p2
    manager.register_provider(p2)
    assert len(manager.list_providers()) == 2

    # Query provider by name (case-insensitive)
    assert manager.get_provider("provideralpha") == p1
    assert manager.get_provider("ProviderBeta") == p2

    # Set active provider
    manager.set_active_provider("provideralpha")
    assert manager.get_active_provider() == p1

    # Setting unavailable provider as active should raise error
    with pytest.raises(ProviderUnavailableError):
        manager.set_active_provider("ProviderBeta")

    # Health status
    health = manager.health_status()
    assert health["total_registered"] == 2
    assert health["active_provider"] == "provideralpha"
    assert health["providers"]["provideralpha"]["available"] is True
    assert health["providers"]["providerbeta"]["available"] is False

    # Unregister provider
    manager.unregister_provider("provideralpha")
    assert manager.get_active_provider() == p2
    with pytest.raises(ProviderNotFoundError):
        manager.get_provider("provideralpha")


# ---------------------------------------------------------------------------
# Tests: ContextBuilder & PromptBuilder
# ---------------------------------------------------------------------------


def test_default_context_builder():
    """Test DefaultContextBuilder converts BrainRequest into AIContext snapshot."""
    builder = DefaultContextBuilder()
    req = BrainRequest(
        request_id="req-test-01",
        raw_text="Organize my Downloads folder",
        session_id="session-01",
        conversation_id="conv-01",
    )

    ctx = builder.build_context(
        request=req,
        conversation_history=[{"role": "user", "content": "hello"}],
        memory_context={"pref": "dark_mode"},
        workspace_context={"root": "/home/user"},
    )

    assert isinstance(ctx, AIContext)
    assert ctx.request_id == "req-test-01"
    assert ctx.raw_query == "Organize my Downloads folder"
    assert ctx.session_id == "session-01"
    assert ctx.conversation_id == "conv-01"
    assert ctx.conversation_history == [{"role": "user", "content": "hello"}]
    assert ctx.memory_context == {"pref": "dark_mode"}
    assert ctx.workspace_context == {"root": "/home/user"}


def test_default_prompt_builder():
    """Test DefaultPromptBuilder renders Prompt object from AIContext."""
    ctx_builder = DefaultContextBuilder()
    prompt_builder = DefaultPromptBuilder(base_system_prompt="Test System Prompt")

    req = BrainRequest(raw_text="Delete redundant logs")
    ctx = ctx_builder.build_context(req, memory_context={"user": "Alice"})
    prompt = prompt_builder.build_prompt(ctx)

    assert isinstance(prompt, Prompt)
    assert prompt.system_prompt == "Test System Prompt"
    assert prompt.user_prompt == "Delete redundant logs"
    assert "user" in prompt.memory_prompt
    assert len(prompt.formatted_messages) >= 3
    assert prompt.token_estimate > 0


# ---------------------------------------------------------------------------
# Tests: ToolRouter
# ---------------------------------------------------------------------------


def test_default_tool_router():
    """Test DefaultToolRouter tool registration, filtering, and call routing stubs."""
    router = DefaultToolRouter()

    # Invalid category
    with pytest.raises(ToolRoutingError):
        router.register_tool(
            name="invalid_tool",
            category="magic",
            description="desc",
            schema={},
        )

    # Register valid tools
    router.register_tool(
        name="read_file",
        category="filesystem",
        description="Read file contents",
        schema={"type": "object", "properties": {"path": {"type": "string"}}},
    )
    router.register_tool(
        name="store_memory",
        category="memory",
        description="Store memory key-value",
        schema={"type": "object"},
    )

    all_tools = router.get_available_tools()
    assert len(all_tools) == 2

    fs_tools = router.get_available_tools(category="filesystem")
    assert len(fs_tools) == 1
    assert fs_tools[0]["name"] == "read_file"

    # Route call
    tc = ToolCall(
        call_id="call-01",
        tool_name="read_file",
        arguments={"path": "/tmp/test.txt"},
        category=ToolCategory.FILESYSTEM,
    )
    result = router.route_tool_call(tc)
    assert isinstance(result, ToolResult)
    assert result.call_id == "call-01"
    assert result.success is True

    # Route unregistered tool call
    tc_unregistered = ToolCall(
        call_id="call-02",
        tool_name="nonexistent",
        arguments={},
    )
    with pytest.raises(ToolRoutingError):
        router.route_tool_call(tc_unregistered)

    # Unregister tool
    router.unregister_tool("read_file")
    assert len(router.get_available_tools()) == 1


# ---------------------------------------------------------------------------
# Tests: AIOrchestrator
# ---------------------------------------------------------------------------


def test_ai_orchestrator_pipeline_success():
    """Test AIOrchestrator request flow with registered StubAIProvider."""
    manager = ProviderManager()
    provider = StubAIProvider(name="MainProvider", response_text="Completed task")
    manager.register_provider(provider)

    orchestrator = AIOrchestrator(provider_manager=manager)
    req = BrainRequest(request_id="req-orch-1", raw_text="Summarize file")

    res = orchestrator.process_request(req)
    assert res.success is True
    assert res.pipeline_status == PipelineStatus.COMPLETED
    assert res.text == "Completed task"
    assert res.request_id == "req-orch-1"


def test_ai_orchestrator_no_provider_failure():
    """Test AIOrchestrator handles case when no provider is registered."""
    orchestrator = AIOrchestrator()  # Empty manager
    req = BrainRequest(request_id="req-orch-2", raw_text="Summarize file")

    res = orchestrator.process_request(req)
    assert res.success is False
    assert res.pipeline_status == PipelineStatus.FAILED
    assert res.error == "No active AI provider registered."
