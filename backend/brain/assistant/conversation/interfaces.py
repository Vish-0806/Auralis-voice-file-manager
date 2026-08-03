"""Abstract Interfaces for the Conversation Runtime Subsystem (Phase 13.2).

Defines Python ABC interfaces for conversation lifecycle management, message history,
context scoping, provider aggregation, and runtime orchestration.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from brain.assistant.conversation.models import (
    Conversation,
    ConversationContext,
    ConversationHealth,
    ConversationHistory,
    ConversationMessage,
    ConversationState,
    ConversationStatistics,
    ConversationType,
)


class IConversationManager(ABC):
    """Abstract interface for managing conversation lifecycle and states."""

    @abstractmethod
    def create_conversation(
        self,
        conversation_type: ConversationType = ConversationType.GENERAL,
        title: str = "New Conversation",
        user_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Conversation:
        """Create and register a new conversation instance."""
        pass

    @abstractmethod
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Retrieve a conversation by ID."""
        pass

    @abstractmethod
    def update_state(
        self, conversation_id: str, new_state: ConversationState
    ) -> Conversation:
        """Update conversation state and validate lifecycle transition."""
        pass

    @abstractmethod
    def close_conversation(self, conversation_id: str) -> Conversation:
        """Close an active conversation."""
        pass

    @abstractmethod
    def archive_conversation(self, conversation_id: str) -> Conversation:
        """Archive a conversation."""
        pass

    @abstractmethod
    def list_conversations(
        self, state: Optional[ConversationState] = None
    ) -> List[Conversation]:
        """List all active or filtered conversations."""
        pass


class IConversationHistoryManager(ABC):
    """Abstract interface for managing message history, append, and pagination."""

    @abstractmethod
    def append_message(
        self,
        conversation_id: str,
        role: Any,
        content: str,
        sender_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConversationMessage:
        """Append a message to the conversation history."""
        pass

    @abstractmethod
    def get_history(
        self,
        conversation_id: str,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> ConversationHistory:
        """Retrieve conversation message history with pagination."""
        pass

    @abstractmethod
    def trim_history(
        self, conversation_id: str, max_messages: int
    ) -> ConversationHistory:
        """Trim message history to maximum message bounds."""
        pass


class IConversationContextManager(ABC):
    """Abstract interface for conversation scope, topic, and context merging."""

    @abstractmethod
    def get_context(self, conversation_id: str) -> Optional[ConversationContext]:
        """Retrieve context for a conversation."""
        pass

    @abstractmethod
    def set_topic(self, conversation_id: str, topic: str) -> ConversationContext:
        """Set or update the active topic."""
        pass

    @abstractmethod
    def merge_execution_context(
        self, conversation_id: str, execution_context: Dict[str, Any]
    ) -> ConversationContext:
        """Merge execution context into conversation context."""
        pass

    @abstractmethod
    def merge_assistant_context(
        self, conversation_id: str, assistant_context: Dict[str, Any]
    ) -> ConversationContext:
        """Merge assistant context into conversation context."""
        pass

    @abstractmethod
    def update_variables(
        self, conversation_id: str, variables: Dict[str, Any]
    ) -> ConversationContext:
        """Update arbitrary context variables."""
        pass


class IConversationProvider(ABC):
    """Abstract interface aggregating conversation services, health, stats, and capabilities."""

    @property
    @abstractmethod
    def manager(self) -> IConversationManager:
        """Get the conversation lifecycle manager."""
        pass

    @property
    @abstractmethod
    def history_manager(self) -> IConversationHistoryManager:
        """Get the history manager."""
        pass

    @property
    @abstractmethod
    def context_manager(self) -> IConversationContextManager:
        """Get the context manager."""
        pass

    @abstractmethod
    def get_health(self) -> ConversationHealth:
        """Get diagnostic health report."""
        pass

    @abstractmethod
    def get_statistics(self) -> ConversationStatistics:
        """Get aggregated runtime statistics."""
        pass

    @abstractmethod
    def initialize(self) -> None:
        """Initialize provider resources."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown provider resources."""
        pass

    @property
    @abstractmethod
    def is_initialized(self) -> bool:
        """Check if provider is initialized."""
        pass


class IConversationRuntime(ABC):
    """Abstract interface for top-level Conversation Runtime orchestration."""

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the conversation runtime."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the conversation runtime."""
        pass

    @abstractmethod
    def get_health(self) -> ConversationHealth:
        """Get health status."""
        pass

    @abstractmethod
    def get_statistics(self) -> ConversationStatistics:
        """Get performance statistics."""
        pass

    @property
    @abstractmethod
    def is_initialized(self) -> bool:
        """Check if runtime is initialized."""
        pass
