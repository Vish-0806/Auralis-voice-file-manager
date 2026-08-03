"""Conversation Runtime Subsystem for Auralis (Phase 13.2).

Provides conversation lifecycle management, state transitions, message history storage,
pagination, context maintenance, and topic tracking.
"""

from brain.assistant.conversation.context_manager import ContextManager
from brain.assistant.conversation.conversation_manager import ConversationManager
from brain.assistant.conversation.conversation_provider import ConversationProvider
from brain.assistant.conversation.conversation_runtime import ConversationRuntime
from brain.assistant.conversation.exceptions import (
    ConversationException,
    ConversationNotFoundError,
    ConversationStateError,
    ConversationStorageError,
    ConversationValidationError,
)
from brain.assistant.conversation.history_manager import HistoryManager
from brain.assistant.conversation.interfaces import (
    IConversationContextManager,
    IConversationHistoryManager,
    IConversationManager,
    IConversationProvider,
    IConversationRuntime,
)
from brain.assistant.conversation.models import (
    Conversation,
    ConversationContext,
    ConversationHealth,
    ConversationHistory,
    ConversationMessage,
    ConversationMetadata,
    ConversationParticipant,
    ConversationState,
    ConversationStatistics,
    ConversationType,
    MessageRole,
)
from brain.assistant.conversation.runtime import (
    get_conversation_runtime,
    reset_conversation_runtime,
)

__all__ = [
    # Models & Enums
    "ConversationState",
    "MessageRole",
    "ConversationType",
    "ConversationMetadata",
    "ConversationParticipant",
    "ConversationMessage",
    "ConversationContext",
    "ConversationHistory",
    "ConversationStatistics",
    "ConversationHealth",
    "Conversation",
    # Exceptions
    "ConversationException",
    "ConversationNotFoundError",
    "ConversationStateError",
    "ConversationValidationError",
    "ConversationStorageError",
    # Interfaces
    "IConversationManager",
    "IConversationHistoryManager",
    "IConversationContextManager",
    "IConversationProvider",
    "IConversationRuntime",
    # Managers & Providers
    "ConversationManager",
    "HistoryManager",
    "ContextManager",
    "ConversationProvider",
    "ConversationRuntime",
    # Singleton accessors
    "get_conversation_runtime",
    "reset_conversation_runtime",
]
