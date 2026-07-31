"""ToolRouter implementation integrating Tool Calling Runtime (Phase 10.1 & Phase 10.4).

Bridges AI tool discovery and routing to ToolRegistry, ToolParser, and ToolExecutor.
"""

from typing import Any, Dict, List, Optional

from brain.ai.exceptions import ToolRoutingError
from brain.ai.interfaces import ToolRouter
from brain.ai.ai_models import ToolCall, ToolCategory, ToolResult
from brain.ai.tools.exceptions import ToolException, ToolNotFoundError
from brain.ai.tools.interfaces import (
    AITool,
    ToolExecutorInterface,
    ToolParserInterface,
    ToolRegistryInterface,
)
from brain.ai.tools.metadata import ToolMetadata
from brain.ai.tools.registry import DefaultToolRegistry
from brain.ai.tools.parser import DefaultToolParser
from brain.ai.tools.executor import DefaultToolExecutor


class SchemaWrapperTool(AITool):
    """Wrapper tool for metadata-only schemas registered via simple dict signature."""

    def __init__(self, metadata: ToolMetadata) -> None:
        self._metadata = metadata

    def get_metadata(self) -> ToolMetadata:
        return self._metadata

    def execute(self, arguments: Dict[str, Any]) -> Any:
        return {"status": "stub_routed", "arguments": arguments}


class DefaultToolRouter(ToolRouter):
    """Default implementation of ToolRouter interface bridging to Phase 10.4 Tool Calling Runtime."""

    SUPPORTED_CATEGORIES = {cat.value for cat in ToolCategory}

    def __init__(
        self,
        registry: Optional[ToolRegistryInterface] = None,
        executor: Optional[ToolExecutorInterface] = None,
        parser: Optional[ToolParserInterface] = None,
    ) -> None:
        self.registry = registry or DefaultToolRegistry()
        self.executor = executor or DefaultToolExecutor(registry=self.registry)
        self.parser = parser or DefaultToolParser()

    def register_tool(
        self,
        name: str,
        category: str,
        description: str,
        schema: Dict[str, Any],
    ) -> None:
        """Register a tool metadata schema.

        Args:
            name: Unique tool identifier.
            category: Tool category string.
            description: Description of tool functionality.
            schema: JSON schema dictionary specifying inputs/parameters.

        Raises:
            ToolRoutingError: If category is unknown or registration fails.
        """
        cat_lower = category.lower().strip()
        if cat_lower not in self.SUPPORTED_CATEGORIES:
            raise ToolRoutingError(
                f"Unsupported tool category '{category}'. "
                f"Allowed categories: {sorted(list(self.SUPPORTED_CATEGORIES))}"
            )

        if not name:
            raise ToolRoutingError("Tool name cannot be empty.")

        try:
            cat_enum = ToolCategory(cat_lower)
            meta = ToolMetadata(
                tool_name=name,
                description=description,
                category=cat_enum,
                parameters=schema,
            )
            wrapper_tool = SchemaWrapperTool(meta)
            self.registry.register_tool(wrapper_tool)
        except Exception as exc:
            raise ToolRoutingError(f"Failed to register tool '{name}': {exc}") from exc

    def unregister_tool(self, name: str) -> None:
        """Unregister a tool by name."""
        try:
            self.registry.unregister_tool(name)
        except ToolNotFoundError:
            raise ToolRoutingError(f"Tool '{name}' is not registered.")
        except Exception as exc:
            raise ToolRoutingError(f"Failed to unregister tool '{name}': {exc}") from exc

    def get_available_tools(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """List registered tools, optionally filtered by category."""
        if category:
            metadata_list = self.registry.list_by_category(category)
        else:
            metadata_list = self.registry.list_tools()

        return [
            {
                "name": meta.tool_name,
                "category": meta.category.value if hasattr(meta.category, "value") else str(meta.category),
                "description": meta.description,
                "schema": meta.parameters,
            }
            for meta in metadata_list
        ]

    def route_tool_call(self, tool_call: ToolCall) -> ToolResult:
        """Route and execute a tool execution call."""
        if not self.registry.tool_exists(tool_call.tool_name):
            raise ToolRoutingError(
                f"Cannot route call: Tool '{tool_call.tool_name}' is not registered."
            )

        try:
            return self.executor.execute_tool_call(tool_call)
        except Exception as exc:
            raise ToolRoutingError(f"Tool routing execution failed: {exc}") from exc
