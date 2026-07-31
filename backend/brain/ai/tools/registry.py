"""ToolRegistry implementation for managing AITool instances (Phase 10.4).

Provides registration, unregistration, lookup, and category filtering of AI tools.
"""

import logging
from typing import Dict, List, Union, Optional

from brain.ai.ai_models import ToolCategory
from brain.ai.tools.exceptions import ToolNotFoundError, ToolRegistrationError
from brain.ai.tools.interfaces import AITool, ToolRegistryInterface
from brain.ai.tools.metadata import ToolMetadata

logger = logging.getLogger(__name__)


class DefaultToolRegistry(ToolRegistryInterface):
    """Concrete implementation of ToolRegistryInterface."""

    def __init__(self) -> None:
        self._tools: Dict[str, AITool] = {}

    def register_tool(self, tool: AITool) -> None:
        """Register an AITool instance.

        Args:
            tool: Concrete instance of AITool.

        Raises:
            ToolRegistrationError: If object is invalid or tool name is already registered.
        """
        if not isinstance(tool, AITool):
            raise ToolRegistrationError("Object does not implement AITool interface.")

        meta = tool.get_metadata()
        name = meta.tool_name.lower().strip()

        if not name:
            raise ToolRegistrationError("Tool name cannot be empty.")

        if name in self._tools:
            raise ToolRegistrationError(f"Tool '{meta.tool_name}' is already registered.")

        self._tools[name] = tool
        logger.debug(f"Registered tool '{meta.tool_name}' under category '{meta.category}'.")

    def unregister_tool(self, tool_name: str) -> None:
        """Unregister a tool by name.

        Args:
            tool_name: Unique tool name.

        Raises:
            ToolNotFoundError: If tool is not registered.
        """
        key = tool_name.lower().strip()
        if key not in self._tools:
            raise ToolNotFoundError(tool_name)

        del self._tools[key]
        logger.debug(f"Unregistered tool '{tool_name}'.")

    def get_tool(self, tool_name: str) -> AITool:
        """Retrieve a registered AITool by name.

        Args:
            tool_name: Unique tool name.

        Returns:
            AITool instance.

        Raises:
            ToolNotFoundError: If tool is not registered.
        """
        key = tool_name.lower().strip()
        if key not in self._tools:
            raise ToolNotFoundError(tool_name)
        return self._tools[key]

    def list_tools(self, enabled_only: bool = True) -> List[ToolMetadata]:
        """List metadata for registered tools.

        Args:
            enabled_only: If True, only include enabled tools.

        Returns:
            List of ToolMetadata objects.
        """
        results: List[ToolMetadata] = []
        for tool in self._tools.values():
            meta = tool.get_metadata()
            if enabled_only and not meta.enabled:
                continue
            results.append(meta)
        return results

    def list_by_category(
        self,
        category: Union[str, ToolCategory],
        enabled_only: bool = True,
    ) -> List[ToolMetadata]:
        """List tool metadata filtered by category.

        Args:
            category: ToolCategory enum or string category name.
            enabled_only: If True, filter out disabled tools.

        Returns:
            Filtered list of ToolMetadata objects.
        """
        cat_str = category.value.lower() if isinstance(category, ToolCategory) else str(category).lower()
        results: List[ToolMetadata] = []

        for tool in self._tools.values():
            meta = tool.get_metadata()
            tool_cat = meta.category.value.lower() if hasattr(meta.category, "value") else str(meta.category).lower()
            if tool_cat == cat_str:
                if enabled_only and not meta.enabled:
                    continue
                results.append(meta)

        return results

    def tool_exists(self, tool_name: str) -> bool:
        """Check whether a tool is registered by name."""
        key = tool_name.lower().strip()
        return key in self._tools
