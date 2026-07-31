"""Abstract interfaces for Tool Calling Runtime (Phase 10.4).

Defines ABCs for:
- AITool
- ToolRegistryInterface
- ToolParserInterface
- ToolExecutorInterface
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from brain.ai.ai_models import ToolCall, ToolCategory, ToolResult
from brain.ai.tools.metadata import ToolMetadata


class AITool(ABC):
    """Abstract interface for a executable AI tool."""

    @abstractmethod
    def get_metadata(self) -> ToolMetadata:
        """Return tool metadata description and JSON schema."""
        pass

    @abstractmethod
    def execute(self, arguments: Dict[str, Any]) -> Any:
        """Execute tool logic given parsed arguments dictionary."""
        pass


class ToolRegistryInterface(ABC):
    """Abstract interface for registering, querying, and managing AI tools."""

    @abstractmethod
    def register_tool(self, tool: AITool) -> None:
        """Register an AITool instance."""
        pass

    @abstractmethod
    def unregister_tool(self, tool_name: str) -> None:
        """Unregister an AITool by name."""
        pass

    @abstractmethod
    def get_tool(self, tool_name: str) -> AITool:
        """Retrieve an AITool instance by name."""
        pass

    @abstractmethod
    def list_tools(self, enabled_only: bool = True) -> List[ToolMetadata]:
        """List metadata for all registered tools."""
        pass

    @abstractmethod
    def list_by_category(
        self,
        category: Union[str, ToolCategory],
        enabled_only: bool = True,
    ) -> List[ToolMetadata]:
        """List tool metadata filtered by category."""
        pass

    @abstractmethod
    def tool_exists(self, tool_name: str) -> bool:
        """Check if a tool is registered."""
        pass


class ToolParserInterface(ABC):
    """Abstract interface for parsing raw provider tool call payloads into ToolCall models."""

    @abstractmethod
    def parse_tool_calls(self, payload: Any) -> List[ToolCall]:
        """Parse raw completion payload or list of tool calls into ToolCall models."""
        pass

    @abstractmethod
    def parse_single_call(self, raw_call: Any) -> ToolCall:
        """Parse a single raw tool call payload into a ToolCall model."""
        pass


class ToolExecutorInterface(ABC):
    """Abstract interface for validating and executing tool calls."""

    @abstractmethod
    def execute_tool_call(self, tool_call: ToolCall) -> ToolResult:
        """Validate and execute a single ToolCall object."""
        pass

    @abstractmethod
    def execute_multiple(self, tool_calls: List[ToolCall]) -> List[ToolResult]:
        """Execute multiple ToolCall objects sequentially."""
        pass
