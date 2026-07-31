"""Auralis AI Architecture Subsystem (Phase 10.1).

Exports all interfaces, models, exceptions, managers, builders, routers, and orchestrator.
"""

from brain.ai.exceptions import (
    AIException,
    AIOrchestrationError,
    ContextBuildError,
    PromptBuildError,
    ProviderNotFoundError,
    ProviderRegistrationError,
    ProviderUnavailableError,
    ToolRoutingError,
)
from brain.ai.ai_models import (
    AIContext,
    AIRequest,
    AIResponse,
    FinishReason,
    Prompt,
    PromptMessage,
    PromptRole,
    ProviderInfo,
    ToolCall,
    ToolCategory,
    ToolResult,
)
from brain.ai.interfaces import (
    AIProvider,
    ContextBuilder,
    PromptBuilder,
    ToolRouter,
)
from brain.ai.provider_manager import ProviderManager
from brain.ai.context_builder import DefaultContextBuilder
from brain.ai.prompt_engine import DefaultPromptBuilder
from brain.ai.tool_router import DefaultToolRouter
from brain.ai.orchestrator import AIOrchestrator

__all__ = [
    # Exceptions
    "AIException",
    "ProviderNotFoundError",
    "ProviderRegistrationError",
    "ProviderUnavailableError",
    "ContextBuildError",
    "PromptBuildError",
    "ToolRoutingError",
    "AIOrchestrationError",
    # Models
    "ToolCategory",
    "FinishReason",
    "PromptRole",
    "ProviderInfo",
    "ToolCall",
    "ToolResult",
    "AIContext",
    "PromptMessage",
    "Prompt",
    "AIRequest",
    "AIResponse",
    # Interfaces
    "AIProvider",
    "ContextBuilder",
    "PromptBuilder",
    "ToolRouter",
    # Implementations & Managers
    "ProviderManager",
    "DefaultContextBuilder",
    "DefaultPromptBuilder",
    "DefaultToolRouter",
    "AIOrchestrator",
]
