"""Assistant Memory & Context Integration Subsystem for Auralis (Phase 13.5).

Integrates, merges, prioritizes, deduplicates, and exposes context across Conversation,
Dialogue, Decision, Execution, and AI Memory runtimes without duplicating memory engines.
"""

from brain.assistant.memory.assistant_context_manager import AssistantContextManager
from brain.assistant.memory.assistant_memory_provider import AssistantMemoryProvider
from brain.assistant.memory.assistant_memory_runtime import AssistantMemoryRuntime
from brain.assistant.memory.exceptions import (
    AssistantContextMergeError,
    AssistantMemoryException,
    AssistantMemoryRetrievalError,
    AssistantMemoryValidationError,
    AssistantPreferenceError,
)
from brain.assistant.memory.interfaces import (
    IAssistantContextManager,
    IAssistantMemoryCoordinator,
    IAssistantMemoryProvider,
    IAssistantMemoryRuntime,
    IAssistantPreferenceManager,
)
from brain.assistant.memory.memory_coordinator import MemoryCoordinator
from brain.assistant.memory.models import (
    AssistantContextPriority,
    AssistantConversationSummary,
    AssistantMemoryContext,
    AssistantMemoryHealth,
    AssistantMemoryReference,
    AssistantMemoryScope,
    AssistantMemorySnapshot,
    AssistantMemorySource,
    AssistantMemoryStatistics,
    AssistantPreference,
    AssistantWorkingContext,
)
from brain.assistant.memory.preference_manager import PreferenceManager
from brain.assistant.memory.runtime import (
    get_assistant_memory_runtime,
    reset_assistant_memory_runtime,
)

__all__ = [
    # Enums & Models
    "AssistantMemoryScope",
    "AssistantContextPriority",
    "AssistantMemorySource",
    "AssistantMemoryReference",
    "AssistantConversationSummary",
    "AssistantPreference",
    "AssistantMemoryContext",
    "AssistantWorkingContext",
    "AssistantMemorySnapshot",
    "AssistantMemoryStatistics",
    "AssistantMemoryHealth",
    # Exceptions
    "AssistantMemoryException",
    "AssistantMemoryRetrievalError",
    "AssistantContextMergeError",
    "AssistantPreferenceError",
    "AssistantMemoryValidationError",
    # Interfaces
    "IAssistantContextManager",
    "IAssistantPreferenceManager",
    "IAssistantMemoryCoordinator",
    "IAssistantMemoryProvider",
    "IAssistantMemoryRuntime",
    # Managers & Components
    "AssistantContextManager",
    "PreferenceManager",
    "MemoryCoordinator",
    "AssistantMemoryProvider",
    "AssistantMemoryRuntime",
    # Singleton accessors
    "get_assistant_memory_runtime",
    "reset_assistant_memory_runtime",
]
