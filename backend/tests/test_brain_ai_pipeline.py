"""End-to-End AI Pipeline Validation Test Suite (Phase 10.5.1).

Validates the full integrated execution sequence across:
- Provider Framework (ProviderManager, BaseAIProvider, GroqProvider)
- Prompt Intelligence (DefaultPromptBuilder, PromptTemplates, TokenEstimator, ConversationBuilder, MemoryInjector, WorkspaceContextInjector, PromptOptimizer)
- Tool Calling Runtime (DefaultToolRegistry, DefaultToolParser, DefaultToolExecutor, ToolMetadata, ToolPermissionLevel)
- Memory-aware AI (AIMemoryProvider, DefaultMemoryRetriever, DefaultMemoryRanker, DefaultMemoryFilter)

Includes full end-to-end integration tests, tool execution loops, failure scenarios, and boundary isolation checks.
"""

import os
import json
# pyrefly: ignore [missing-import]
import pytest
from typing import Any, Dict, List, Optional
from unittest.mock import patch
# pyrefly: ignore [missing-import]
import httpx

from brain.runtime.brain_models import BrainRequest, BrainResponse, PipelineStatus
from brain.ai import (
    AIContext,
    AIMemoryItem,
    AIMemoryProvider,
    AIOrchestrator,
    AIRequest,
    AIResponse,
    AITool,
    ConversationBuilder,
    DefaultContextBuilder,
    DefaultMemoryFilter,
    DefaultMemoryRanker,
    DefaultMemoryRetriever,
    DefaultPromptBuilder,
    DefaultToolExecutor,
    DefaultToolParser,
    DefaultToolRegistry,
    DefaultToolRouter,
    FinishReason,
    GroqProvider,
    MemoryInjector,
    MemoryQueryResult,
    MemoryScope,
    MockWorkspaceContextProvider,
    Prompt,
    PromptMessage,
    PromptOptimizer,
    PromptRole,
    PromptTemplates,
    ProviderConfig,
    ProviderManager,
    ProviderUnavailableError,
    TokenEstimator,
    ToolCall,
    ToolCategory,
    ToolExecutorInterface,
    ToolMetadata,
    ToolNotFoundError,
    ToolParserInterface,
    ToolParsingError,
    ToolPermissionLevel,
    ToolRegistryInterface,
    ToolResult,
    WorkspaceContextInjector,
)


class ExecutableMockTool(AITool):
    """Mock executable AITool for pipeline validation."""

    def __init__(
        self,
        name: str = "mock_file_organizer",
        category: ToolCategory = ToolCategory.FILESYSTEM,
        permission: ToolPermissionLevel = ToolPermissionLevel.WRITE,
        should_fail: bool = False,
    ) -> None:
        self._name = name
        self._category = category
        self._permission = permission
        self._should_fail = should_fail

    def get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            tool_name=self._name,
            description="Mock tool to organize files in target directory",
            category=self._category,
            parameters={
                "type": "object",
                "properties": {
                    "directory": {"type": "string"},
                    "mode": {"type": "string"},
                },
                "required": ["directory"],
            },
            permission_level=self._permission,
            enabled=True,
        )

    def execute(self, arguments: Dict[str, Any]) -> Any:
        if self._should_fail:
            raise RuntimeError(f"Simulated execution failure in '{self._name}'")

        target_dir = arguments.get("directory", "/tmp")
        return {"status": "success", "organized_dir": target_dir, "files_processed": 5}


# ---------------------------------------------------------------------------
# Tests: Full Integrated Execution Flow
# ---------------------------------------------------------------------------


def test_full_integrated_pipeline_execution(monkeypatch):
    """Test full pipeline: BrainRequest -> ContextBuilder -> Memory/Workspace -> PromptIntelligence -> GroqProvider -> Tool Calling -> Response."""
    monkeypatch.setenv("GROQ_API_KEY", "gsk_dummy_pipeline_key")

    # 1. Setup Tool Registry & Executor
    registry = DefaultToolRegistry()
    organizer_tool = ExecutableMockTool(name="organize_files")
    registry.register_tool(organizer_tool)

    executor = DefaultToolExecutor(registry=registry)
    parser = DefaultToolParser()
    router = DefaultToolRouter(registry=registry, executor=executor, parser=parser)

    # 2. Setup Memory & Workspace Pipeline
    mem_provider = AIMemoryProvider()
    mem_injector = MemoryInjector(memory_provider=mem_provider)
    ws_injector = WorkspaceContextInjector(workspace_provider=MockWorkspaceContextProvider(default_dir="/home/user/documents"))

    # 3. Setup Prompt Intelligence Engine
    prompt_builder = DefaultPromptBuilder(
        memory_injector=mem_injector,
        workspace_injector=ws_injector,
    )

    # 4. Setup Provider Manager with GroqProvider
    groq_provider = GroqProvider()
    provider_manager = ProviderManager()
    provider_manager.register_provider(groq_provider, set_active=True, priority=100)

    # 5. Setup Orchestrator
    orchestrator = AIOrchestrator(
        provider_manager=provider_manager,
        context_builder=DefaultContextBuilder(),
        prompt_builder=prompt_builder,
        tool_router=router,
    )

    # 6. Mock Groq API response returning text completion
    mock_groq_json = {
        "id": "chatcmpl-pipeline-1",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "I have reviewed your workspace and memory preferences. Your files are ready.",
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 40, "completion_tokens": 15, "total_tokens": 55},
    }

    mock_response = httpx.Response(status_code=200, json=mock_groq_json)

    with patch.object(httpx.Client, "post", return_value=mock_response):
        req = BrainRequest(
            request_id="req-pipe-01",
            raw_text="Organize my project files",
            session_id="sess-01",
            conversation_id="conv-01",
        )

        res = orchestrator.process_request(req)

        assert isinstance(res, BrainResponse)
        assert res.success is True
        assert res.pipeline_status == PipelineStatus.COMPLETED
        assert "reviewed your workspace" in res.text
        assert res.execution_summary["provider"] == "groq"
        assert res.execution_summary["finish_reason"] == FinishReason.STOP


def test_full_pipeline_tool_calling_loop(monkeypatch):
    """Test full pipeline loop when model returns tool calls: parsing -> execution -> result generation."""
    monkeypatch.setenv("GROQ_API_KEY", "gsk_dummy_pipeline_key")

    registry = DefaultToolRegistry()
    registry.register_tool(ExecutableMockTool(name="organize_files"))
    executor = DefaultToolExecutor(registry=registry)
    parser = DefaultToolParser()
    router = DefaultToolRouter(registry=registry, executor=executor, parser=parser)

    provider_manager = ProviderManager()
    provider_manager.register_provider(GroqProvider(), set_active=True)

    orchestrator = AIOrchestrator(
        provider_manager=provider_manager,
        tool_router=router,
    )

    # Mock Groq response returning tool call
    mock_groq_tool_json = {
        "id": "chatcmpl-pipeline-tool-2",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_org_100",
                            "type": "function",
                            "function": {
                                "name": "organize_files",
                                "arguments": json.dumps({"directory": "/home/user/downloads"}),
                            },
                        }
                    ],
                },
                "finish_reason": "tool_calls",
            }
        ],
        "usage": {"prompt_tokens": 50, "completion_tokens": 20, "total_tokens": 70},
    }

    mock_response = httpx.Response(status_code=200, json=mock_groq_tool_json)

    with patch.object(httpx.Client, "post", return_value=mock_response):
        req = BrainRequest(request_id="req-pipe-tool", raw_text="Organize my downloads")
        res = orchestrator.process_request(req)

        assert res.success is True
        assert res.execution_summary["tool_calls_count"] == 1


# ---------------------------------------------------------------------------
# Tests: Pipeline Failure Scenarios
# ---------------------------------------------------------------------------


def test_failure_scenario_empty_memory_and_workspace(monkeypatch):
    """Test pipeline operates cleanly with fallback text when memory and workspace are empty."""
    monkeypatch.setenv("GROQ_API_KEY", "gsk_dummy_pipeline_key")

    prompt_builder = DefaultPromptBuilder(
        memory_injector=MemoryInjector(memory_provider=AIMemoryProvider()),
        workspace_injector=WorkspaceContextInjector(workspace_provider=MockWorkspaceContextProvider(default_dir="", default_active_workspace="")),
    )

    provider_manager = ProviderManager()
    provider_manager.register_provider(GroqProvider(), set_active=True)

    orchestrator = AIOrchestrator(provider_manager=provider_manager, prompt_builder=prompt_builder)

    mock_response = httpx.Response(
        status_code=200,
        json={"id": "c1", "choices": [{"message": {"content": "Fallback handled cleanly"}, "finish_reason": "stop"}]},
    )

    with patch.object(httpx.Client, "post", return_value=mock_response):
        req = BrainRequest(raw_text="Hello")
        res = orchestrator.process_request(req)
        assert res.success is True
        assert res.text == "Fallback handled cleanly"


def test_failure_scenario_provider_timeout(monkeypatch):
    """Test pipeline handles provider timeout / network failure gracefully."""
    monkeypatch.setenv("GROQ_API_KEY", "gsk_dummy_pipeline_key")

    provider_manager = ProviderManager()
    provider_manager.register_provider(GroqProvider(), set_active=True)

    orchestrator = AIOrchestrator(provider_manager=provider_manager)

    # Mock timeout exception
    with patch.object(httpx.Client, "post", side_effect=httpx.TimeoutException("Connection timed out")):
        req = BrainRequest(raw_text="Test timeout")
        with pytest.raises(Exception):
            orchestrator.process_request(req)


def test_failure_scenario_missing_tool_execution():
    """Test DefaultToolExecutor returns failure ToolResult for unregistered tool."""
    registry = DefaultToolRegistry()
    executor = DefaultToolExecutor(registry=registry)

    tc = ToolCall(call_id="call-missing", tool_name="unregistered_tool", arguments={})
    res = executor.execute_tool_call(tc)

    assert isinstance(res, ToolResult)
    assert res.success is False
    assert "not registered" in res.error_message


def test_failure_scenario_tool_execution_exception():
    """Test DefaultToolExecutor captures tool runtime exception into ToolResult without crashing."""
    registry = DefaultToolRegistry()
    failing_tool = ExecutableMockTool(name="bad_tool", should_fail=True)
    registry.register_tool(failing_tool)

    executor = DefaultToolExecutor(registry=registry)

    tc = ToolCall(call_id="call-fail", tool_name="bad_tool", arguments={"directory": "/tmp"})
    res = executor.execute_tool_call(tc)

    assert res.success is False
    assert "Simulated execution failure" in res.error_message


def test_failure_scenario_malformed_tool_payload():
    """Test DefaultToolParser raises ToolParsingError for malformed payload."""
    parser = DefaultToolParser()

    with pytest.raises(ToolParsingError):
        parser.parse_tool_calls({"invalid": "structure", "no_choices": True})


# ---------------------------------------------------------------------------
# Tests: Architectural Boundary & Dependency Injection Verification
# ---------------------------------------------------------------------------


def test_architectural_dependency_injection():
    """Verify that all pipeline components accept dependency injection."""
    custom_registry = DefaultToolRegistry()
    custom_executor = DefaultToolExecutor(registry=custom_registry)
    custom_parser = DefaultToolParser()
    custom_router = DefaultToolRouter(registry=custom_registry, executor=custom_executor, parser=custom_parser)

    custom_mem_provider = AIMemoryProvider()
    custom_mem_injector = MemoryInjector(memory_provider=custom_mem_provider)
    custom_prompt_builder = DefaultPromptBuilder(memory_injector=custom_mem_injector)

    custom_manager = ProviderManager()
    orchestrator = AIOrchestrator(
        provider_manager=custom_manager,
        prompt_builder=custom_prompt_builder,
        tool_router=custom_router,
    )

    assert orchestrator.provider_manager == custom_manager
    assert orchestrator.prompt_builder == custom_prompt_builder
    assert orchestrator.tool_router == custom_router


def test_architectural_package_imports_and_no_circular_dependencies():
    """Verify clean import resolution across all brain.ai subpackages."""
    import brain.ai
    import brain.ai.providers
    import brain.ai.tools
    import brain.ai.memory

    assert hasattr(brain.ai, "AIOrchestrator")
    assert hasattr(brain.ai.providers, "GroqProvider")
    assert hasattr(brain.ai.tools, "DefaultToolExecutor")
    assert hasattr(brain.ai.memory, "AIMemoryProvider")
