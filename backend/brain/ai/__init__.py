"""Auralis AI Architecture Subsystem (Phases 10.1 - 10.3).

Exports all interfaces, models, exceptions, managers, builders, routers, orchestrator,
provider configurations, concrete LLM providers, and prompt intelligence pipeline services.
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
from brain.ai.provider_config import (
    ProviderConfig,
    get_groq_default_config,
    load_provider_config_from_env,
)
from brain.ai.providers import (
    BaseAIProvider,
    GroqProvider,
)
from brain.ai.provider_manager import ProviderManager
from brain.ai.context_builder import DefaultContextBuilder
from brain.ai.prompt_templates import PromptTemplates
from brain.ai.token_estimator import TokenEstimator
from brain.ai.conversation_builder import ConversationBuilder
from brain.ai.memory_injector import (
    DefaultMemoryProvider,
    MemoryInjector,
    MemoryProviderInterface,
)
from brain.ai.workspace_context import (
    MockWorkspaceContextProvider,
    WorkspaceContextInjector,
    WorkspaceContextProviderInterface,
)
from brain.ai.prompt_optimizer import PromptOptimizer, ROLE_PRIORITY
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
    # Provider Config & Providers
    "ProviderConfig",
    "load_provider_config_from_env",
    "get_groq_default_config",
    "BaseAIProvider",
    "GroqProvider",
    # Prompt Intelligence Services
    "PromptTemplates",
    "TokenEstimator",
    "ConversationBuilder",
    "MemoryInjector",
    "MemoryProviderInterface",
    "DefaultMemoryProvider",
    "WorkspaceContextInjector",
    "WorkspaceContextProviderInterface",
    "MockWorkspaceContextProvider",
    "PromptOptimizer",
    "ROLE_PRIORITY",
    # Implementations & Managers
    "ProviderManager",
    "DefaultContextBuilder",
    "DefaultPromptBuilder",
    "DefaultToolRouter",
    "AIOrchestrator",
]
