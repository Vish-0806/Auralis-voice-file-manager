"""Abstract interfaces for the Auralis AI Architecture (Phase 10.1).

Defines ABC interfaces for:
- AIProvider
- PromptBuilder
- ContextBuilder
- ToolRouter
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from brain.runtime.brain_models import BrainRequest
from brain.ai.ai_models import (
    AIContext,
    AIRequest,
    AIResponse,
    Prompt,
    ProviderInfo,
    ToolCall,
    ToolResult,
)


class AIProvider(ABC):
    """Abstract interface for all external and local LLM providers."""

    @abstractmethod
    def get_info(self) -> ProviderInfo:
        """Return provider metadata and feature capabilities."""
        pass

    @abstractmethod
    def generate_response(self, request: AIRequest) -> AIResponse:
        """Generate an AI response payload given an AIRequest."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider service is currently operational."""
        pass

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Perform health diagnostic check and return status dictionary."""
        pass


class ContextBuilder(ABC):
    """Abstract interface for building structured AIContext objects from BrainRequests."""

    @abstractmethod
    def build_context(
        self,
        request: BrainRequest,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        memory_context: Optional[Dict[str, Any]] = None,
        workspace_context: Optional[Dict[str, Any]] = None,
        execution_context: Optional[Dict[str, Any]] = None,
    ) -> AIContext:
        """Build and assemble an AIContext snapshot from inputs."""
        pass


class PromptBuilder(ABC):
    """Abstract interface for generating structured Prompt objects from AIContext."""

    @abstractmethod
    def build_prompt(self, context: AIContext) -> Prompt:
        """Build and assemble structured prompt layers from AIContext."""
        pass


class ToolRouter(ABC):
    """Abstract interface for AI tool registration, schema discovery, and execution routing."""

    @abstractmethod
    def register_tool(
        self,
        name: str,
        category: str,
        description: str,
        schema: Dict[str, Any],
    ) -> None:
        """Register a tool with its category, description, and JSON schema."""
        pass

    @abstractmethod
    def unregister_tool(self, name: str) -> None:
        """Unregister a tool by name."""
        pass

    @abstractmethod
    def get_available_tools(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """List schemas of registered tools, optionally filtered by category."""
        pass

    @abstractmethod
    def route_tool_call(self, tool_call: ToolCall) -> ToolResult:
        """Route and dispatch a tool call request to the target tool handler."""
        pass
