"""Context Manager implementation for Auralis (Phase 13.2).

Maintains conversation contexts, active topics, variable scopes, and context merging.
Does NOT connect AI memory yet. Thread-safe using threading.RLock().
"""

from datetime import datetime, timezone
import logging
import threading
from typing import Any, Dict, Optional

from brain.assistant.conversation.interfaces import IConversationContextManager
from brain.assistant.conversation.models import ConversationContext, ConversationMetadata

logger = logging.getLogger(__name__)


class ContextManager(IConversationContextManager):
    """Thread-safe manager for conversation scope context, topic, and state merging."""

    def __init__(self, lock: Optional[threading.RLock] = None) -> None:
        self._lock = lock or threading.RLock()
        self._contexts: Dict[str, ConversationContext] = {}

    def get_context(self, conversation_id: str) -> Optional[ConversationContext]:
        """Retrieve conversation context by ID."""
        with self._lock:
            if conversation_id not in self._contexts:
                self._contexts[conversation_id] = ConversationContext(
                    conversation_id=conversation_id
                )
            return self._contexts.get(conversation_id)

    def set_topic(self, conversation_id: str, topic: str) -> ConversationContext:
        """Set or update the active conversation topic."""
        with self._lock:
            ctx = self.get_context(conversation_id) or ConversationContext(conversation_id=conversation_id)
            updated = ctx.model_copy(update={"current_topic": topic})
            self._contexts[conversation_id] = updated
            logger.debug("Set conversation '%s' topic to: %s", conversation_id, topic)
            return updated

    def merge_execution_context(
        self, conversation_id: str, execution_context: Dict[str, Any]
    ) -> ConversationContext:
        """Merge execution context into conversation context."""
        with self._lock:
            ctx = self.get_context(conversation_id) or ConversationContext(conversation_id=conversation_id)
            merged = {**ctx.execution_context, **execution_context}
            updated = ctx.model_copy(update={"execution_context": merged})
            self._contexts[conversation_id] = updated
            return updated

    def merge_assistant_context(
        self, conversation_id: str, assistant_context: Dict[str, Any]
    ) -> ConversationContext:
        """Merge assistant context into conversation context."""
        with self._lock:
            ctx = self.get_context(conversation_id) or ConversationContext(conversation_id=conversation_id)
            merged = {**ctx.assistant_context, **assistant_context}
            updated = ctx.model_copy(update={"assistant_context": merged})
            self._contexts[conversation_id] = updated
            return updated

    def update_variables(
        self, conversation_id: str, variables: Dict[str, Any]
    ) -> ConversationContext:
        """Update arbitrary conversation context variables."""
        with self._lock:
            ctx = self.get_context(conversation_id) or ConversationContext(conversation_id=conversation_id)
            merged = {**ctx.variables, **variables}
            updated = ctx.model_copy(update={"variables": merged})
            self._contexts[conversation_id] = updated
            return updated

    def clear(self) -> None:
        """Clear all stored contexts."""
        with self._lock:
            self._contexts.clear()
