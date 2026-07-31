"""ToolRouter implementation for managing and routing AI tool calls (Phase 10.1).

Allows AI to request and discover tools across domain categories:
- filesystem
- memory
- automation
- voice
- planner
- execution

No tool execution logic implemented yet (stubs/TODO placeholders).
"""

from typing import Any, Dict, List, Optional

from brain.ai.exceptions import ToolRoutingError
from brain.ai.interfaces import ToolRouter
from brain.ai.ai_models import ToolCall, ToolCategory, ToolResult


class DefaultToolRouter(ToolRouter):
    """Default implementation of ToolRouter interface."""

    SUPPORTED_CATEGORIES = {cat.value for cat in ToolCategory}

    def __init__(self) -> None:
        self._tools: Dict[str, Dict[str, Any]] = {}

    def register_tool(
        self,
        name: str,
        category: str,
        description: str,
        schema: Dict[str, Any],
    ) -> None:
        """Register a tool metadata schema.

        Args:
            name: Unique name identifier of the tool.
            category: Tool category string (must be valid ToolCategory).
            description: Description of tool functionality for prompt injection.
            schema: JSON schema dictionary specifying inputs/parameters.

        Raises:
            ToolRoutingError: If category is unknown or name is invalid.
        """
        cat_lower = category.lower()
        if cat_lower not in self.SUPPORTED_CATEGORIES:
            raise ToolRoutingError(
                f"Unsupported tool category '{category}'. "
                f"Allowed categories: {sorted(list(self.SUPPORTED_CATEGORIES))}"
            )

        if not name:
            raise ToolRoutingError("Tool name cannot be empty.")

        self._tools[name] = {
            "name": name,
            "category": cat_lower,
            "description": description,
            "schema": schema,
        }

    def unregister_tool(self, name: str) -> None:
        """Unregister a tool by name.

        Args:
            name: Name of tool to remove.

        Raises:
            ToolRoutingError: If tool is not registered.
        """
        if name not in self._tools:
            raise ToolRoutingError(f"Tool '{name}' is not registered.")
        del self._tools[name]

    def get_available_tools(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """List registered tools, optionally filtered by category.

        Args:
            category: Optional category filter string.

        Returns:
            List of tool schema dictionaries.
        """
        if category:
            cat_lower = category.lower()
            return [
                tool for tool in self._tools.values() if tool["category"] == cat_lower
            ]
        return list(self._tools.values())

    def route_tool_call(self, tool_call: ToolCall) -> ToolResult:
        """Route a tool execution call.

        Note: Execution logic is not implemented in Phase 10.1 (stub placeholder).

        Args:
            tool_call: ToolCall object received from AI completion.

        Returns:
            ToolResult stub object.

        Raises:
            ToolRoutingError: If tool is not registered.
        """
        if tool_call.tool_name not in self._tools:
            raise ToolRoutingError(
                f"Cannot route call: Tool '{tool_call.tool_name}' is not registered."
            )

        # TODO: Connect to concrete execution engine dispatchers in Phase 10+
        return ToolResult(
            call_id=tool_call.call_id,
            tool_name=tool_call.tool_name,
            success=True,
            output={"status": "stub_routed", "arguments": tool_call.arguments},
            error_message=None,
            execution_time_ms=0.0,
        )
