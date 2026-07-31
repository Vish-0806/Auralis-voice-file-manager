"""Comprehensive Unit Tests for Phase 10.4: Tool Calling Runtime.

Validates:
- Tool Metadata & Permission levels
- ToolRegistry registration, duplicate protection, lookup, and category filtering
- ToolParser parsing provider payloads, JSON strings, and malformed validation
- ToolExecutor execution success, duration tracking, exception handling, and error results
- Multi-tool batch execution without stopping on single tool failures
- Parameter schema validation and disabled tool enforcement
"""

import json
# pyrefly: ignore [missing-import]
import pytest
from typing import Any, Dict, List, Optional

from brain.ai import (
    AITool,
    DefaultToolExecutor,
    DefaultToolParser,
    DefaultToolRegistry,
    DefaultToolRouter,
    ToolCall,
    ToolCategory,
    ToolExecutionError,
    ToolMetadata,
    ToolNotFoundError,
    ToolParsingError,
    ToolPermissionLevel,
    ToolRegistrationError,
    ToolResult,
    ToolValidationError,
)


class DummyMockTool(AITool):
    """Mock AITool for testing runtime contracts."""

    def __init__(
        self,
        name: str = "mock_file_mover",
        category: ToolCategory = ToolCategory.FILESYSTEM,
        permission: ToolPermissionLevel = ToolPermissionLevel.WRITE,
        enabled: bool = True,
        should_fail: bool = False,
    ) -> None:
        self._name = name
        self._category = category
        self._permission = permission
        self._enabled = enabled
        self._should_fail = should_fail

    def get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            tool_name=self._name,
            description="Mock tool for file operations",
            category=self._category,
            parameters={
                "type": "object",
                "properties": {
                    "source": {"type": "string"},
                    "destination": {"type": "string"},
                },
                "required": ["source"],
            },
            permission_level=self._permission,
            enabled=self._enabled,
        )

    def execute(self, arguments: Dict[str, Any]) -> Any:
        if self._should_fail:
            raise RuntimeError(f"Mock failure in tool '{self._name}'")

        src = arguments.get("source", "")
        dst = arguments.get("destination", "/tmp")
        return {"status": "success", "moved": src, "to": dst}


# ---------------------------------------------------------------------------
# Tests: Tool Metadata & Permissions
# ---------------------------------------------------------------------------


def test_tool_metadata_and_permissions():
    """Test ToolMetadata model fields and permission enum levels."""
    tool = DummyMockTool(name="read_logs", permission=ToolPermissionLevel.READ)
    meta = tool.get_metadata()

    assert meta.tool_name == "read_logs"
    assert meta.category == ToolCategory.FILESYSTEM
    assert meta.permission_level == ToolPermissionLevel.READ
    assert meta.enabled is True
    assert "source" in meta.parameters["properties"]


# ---------------------------------------------------------------------------
# Tests: ToolRegistry
# ---------------------------------------------------------------------------


def test_tool_registry_registration_and_lookup():
    """Test tool registration, duplicate error handling, and lookup."""
    registry = DefaultToolRegistry()
    t1 = DummyMockTool(name="tool_alpha", category=ToolCategory.FILESYSTEM)
    t2 = DummyMockTool(name="tool_beta", category=ToolCategory.AUTOMATION)

    registry.register_tool(t1)
    registry.register_tool(t2)

    assert registry.tool_exists("tool_alpha") is True
    assert registry.tool_exists("Tool_Beta") is True  # Case insensitive lookup
    assert registry.tool_exists("nonexistent") is False

    # Duplicate registration error
    with pytest.raises(ToolRegistrationError):
        registry.register_tool(t1)

    # Retrieval
    retrieved = registry.get_tool("tool_alpha")
    assert retrieved == t1

    # Unregistered lookup error
    with pytest.raises(ToolNotFoundError):
        registry.get_tool("missing_tool")

    # Listing by category
    fs_tools = registry.list_by_category(ToolCategory.FILESYSTEM)
    assert len(fs_tools) == 1
    assert fs_tools[0].tool_name == "tool_alpha"

    # Unregister
    registry.unregister_tool("tool_alpha")
    assert registry.tool_exists("tool_alpha") is False


# ---------------------------------------------------------------------------
# Tests: ToolParser
# ---------------------------------------------------------------------------


def test_tool_parser_valid_payloads():
    """Test ToolParser parses OpenAI/Groq dict payloads, JSON strings, and ToolCall objects."""
    parser = DefaultToolParser()

    # 1. OpenAI / Groq dictionary payload
    payload_dict = {
        "choices": [
            {
                "message": {
                    "tool_calls": [
                        {
                            "id": "call_abc123",
                            "type": "function",
                            "function": {
                                "name": "move_file",
                                "arguments": json.dumps({"source": "/a.txt", "destination": "/b.txt"}),
                            },
                        }
                    ]
                }
            }
        ]
    }

    parsed = parser.parse_tool_calls(payload_dict)
    assert len(parsed) == 1
    tc = parsed[0]
    assert tc.call_id == "call_abc123"
    assert tc.tool_name == "move_file"
    assert tc.arguments == {"source": "/a.txt", "destination": "/b.txt"}

    # 2. JSON String payload
    json_str = json.dumps({"name": "copy_file", "arguments": {"source": "/doc.pdf"}})
    single = parser.parse_single_call(json_str)
    assert single.tool_name == "copy_file"
    assert single.arguments == {"source": "/doc.pdf"}


def test_tool_parser_malformed_payloads():
    """Test ToolParser raises ToolParsingError on malformed inputs."""
    parser = DefaultToolParser()

    with pytest.raises(ToolParsingError):
        parser.parse_single_call("invalid json { [")

    with pytest.raises(ToolParsingError):
        parser.parse_single_call({"no_tool_name": 123})

    with pytest.raises(ToolParsingError):
        parser.parse_tool_calls(12345)  # Invalid type


# ---------------------------------------------------------------------------
# Tests: ToolExecutor
# ---------------------------------------------------------------------------


def test_tool_executor_success_and_missing_arguments():
    """Test ToolExecutor executes tool, measures duration, and validates required arguments."""
    registry = DefaultToolRegistry()
    mock_tool = DummyMockTool(name="mover")
    registry.register_tool(mock_tool)

    executor = DefaultToolExecutor(registry=registry)

    # Valid execution
    tc = ToolCall(call_id="c1", tool_name="mover", arguments={"source": "/src.txt", "destination": "/dst.txt"})
    res = executor.execute_tool_call(tc)

    assert isinstance(res, ToolResult)
    assert res.success is True
    assert res.output["moved"] == "/src.txt"
    assert res.execution_time_ms >= 0.0
    assert res.error_message is None

    # Missing required argument 'source'
    tc_invalid = ToolCall(call_id="c2", tool_name="mover", arguments={})
    res_invalid = executor.execute_tool_call(tc_invalid)
    assert res_invalid.success is False
    assert "Missing required parameter" in res_invalid.error_message


def test_tool_executor_tool_failure_and_disabled_tool():
    """Test ToolExecutor handles tool runtime exceptions and disabled tools."""
    registry = DefaultToolRegistry()

    failing_tool = DummyMockTool(name="fail_tool", should_fail=True)
    disabled_tool = DummyMockTool(name="off_tool", enabled=False)

    registry.register_tool(failing_tool)
    registry.register_tool(disabled_tool)

    executor = DefaultToolExecutor(registry=registry)

    # 1. Failing tool execution
    tc_fail = ToolCall(call_id="c_fail", tool_name="fail_tool", arguments={"source": "/file"})
    res_fail = executor.execute_tool_call(tc_fail)
    assert res_fail.success is False
    assert "Mock failure in tool" in res_fail.error_message

    # 2. Disabled tool execution
    tc_off = ToolCall(call_id="c_off", tool_name="off_tool", arguments={"source": "/file"})
    res_off = executor.execute_tool_call(tc_off)
    assert res_off.success is False
    assert "currently disabled" in res_off.error_message


def test_tool_executor_multi_tool_batch_resilience():
    """Test ToolExecutor.execute_multiple runs sequentially without stopping when one tool fails."""
    registry = DefaultToolRegistry()

    good_tool = DummyMockTool(name="good_tool")
    bad_tool = DummyMockTool(name="bad_tool", should_fail=True)

    registry.register_tool(good_tool)
    registry.register_tool(bad_tool)

    executor = DefaultToolExecutor(registry=registry)

    batch_calls = [
        ToolCall(call_id="c1", tool_name="good_tool", arguments={"source": "/1.txt"}),
        ToolCall(call_id="c2", tool_name="bad_tool", arguments={"source": "/2.txt"}),
        ToolCall(call_id="c3", tool_name="good_tool", arguments={"source": "/3.txt"}),
    ]

    results = executor.execute_multiple(batch_calls)

    assert len(results) == 3
    assert results[0].success is True
    assert results[1].success is False  # Fails, but batch continues
    assert results[2].success is True


# ---------------------------------------------------------------------------
# Tests: ToolRouter Integration
# ---------------------------------------------------------------------------


def test_tool_router_integration_with_tool_calling_runtime():
    """Test DefaultToolRouter delegates tool registration and routing to registry and executor."""
    router = DefaultToolRouter()

    router.register_tool(
        name="router_tool",
        category="filesystem",
        description="Router test tool",
        schema={"type": "object", "properties": {"path": {"type": "string"}}},
    )

    tools_list = router.get_available_tools()
    assert len(tools_list) == 1
    assert tools_list[0]["name"] == "router_tool"

    tc = ToolCall(call_id="call-router-1", tool_name="router_tool", arguments={"path": "/tmp/a"})
    res = router.route_tool_call(tc)
    assert res.success is True
    assert res.tool_name == "router_tool"
