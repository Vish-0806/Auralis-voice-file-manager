"""Conversation Manager implementation for Auralis (Phase 13.2).

Manages conversation creation, retrieval, closure, archiving, state transitions,
and lifecycle validations. Thread-safe using threading.RLock().
"""

from datetime import datetime, timezone
import logging
import threading
from typing import Any, Dict, List, Optional

from brain.assistant.conversation.exceptions import (
    ConversationNotFoundError,
    ConversationStateError,
    ConversationValidationError,
)
from brain.assistant.conversation.interfaces import IConversationManager
from brain.assistant.conversation.models import (
    Conversation,
    ConversationContext,
    ConversationMetadata,
    ConversationParticipant,
    ConversationState,
    ConversationType,
    MessageRole,
)

logger = logging.getLogger(__name__)


class ConversationManager(IConversationManager):
    """Thread-safe manager handling conversation lifecycle and state transitions."""

    def __init__(self, lock: Optional[threading.RLock] = None) -> None:
        self._lock = lock or threading.RLock()
        self._conversations: Dict[str, Conversation] = {}

    def create_conversation(
        self,
        conversation_type: ConversationType = ConversationType.GENERAL,
        title: str = "New Conversation",
        user_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Conversation:
        """Create and register a new conversation instance."""
        with self._lock:
            meta = ConversationMetadata(
                title=title,
                created_by=user_id,
                custom_attributes=metadata or {},
            )
            ctx = ConversationContext(
                user_id=user_id,
                workspace_id=workspace_id,
                metadata=meta,
            )
            user_participant = ConversationParticipant(
                name=user_id or "User",
                role=MessageRole.USER,
            )

            conv = Conversation(
                conversation_type=conversation_type,
                state=ConversationState.ACTIVE,
                participants=[user_participant],
                context=ctx.model_copy(update={"conversation_id": ""}),
                metadata=meta,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            # Bind conversation_id cleanly
            conv_id = conv.conversation_id
            bound_ctx = conv.context.model_copy(update={"conversation_id": conv_id})
            final_conv = conv.model_copy(update={"context": bound_ctx})

            self._conversations[conv_id] = final_conv
            logger.debug("Created conversation id=%s title='%s'", conv_id, title)
            return final_conv

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Retrieve a conversation by ID."""
        with self._lock:
            return self._conversations.get(conversation_id)

    def update_state(
        self, conversation_id: str, new_state: ConversationState
    ) -> Conversation:
        """Update conversation state and validate lifecycle transition.

        Raises:
            ConversationNotFoundError: If conversation does not exist.
            ConversationStateError: If transition is invalid.
        """
        with self._lock:
            conv = self._conversations.get(conversation_id)
            if conv is None:
                raise ConversationNotFoundError(f"Conversation '{conversation_id}' not found")

            curr_state = conv.state
            if curr_state in (ConversationState.CLOSED, ConversationState.ARCHIVED) and new_state not in (
                ConversationState.ARCHIVED,
                ConversationState.CLOSED,
            ):
                raise ConversationStateError(
                    f"Cannot transition conversation '{conversation_id}' from {curr_state} to {new_state}"
                )

            closed_at = conv.closed_at
            if new_state == ConversationState.CLOSED and closed_at is None:
                closed_at = datetime.now(timezone.utc)

            updated = conv.model_copy(
                update={
                    "state": new_state,
                    "updated_at": datetime.now(timezone.utc),
                    "closed_at": closed_at,
                }
            )
            self._conversations[conversation_id] = updated
            logger.debug("Updated conversation '%s' state: %s -> %s", conversation_id, curr_state, new_state)
            return updated

    def close_conversation(self, conversation_id: str) -> Conversation:
        """Close an active conversation."""
        return self.update_state(conversation_id, ConversationState.CLOSED)

    def archive_conversation(self, conversation_id: str) -> Conversation:
        """Archive a conversation."""
        return self.update_state(conversation_id, ConversationState.ARCHIVED)

    def list_conversations(
        self, state: Optional[ConversationState] = None
    ) -> List[Conversation]:
        """List all active or filtered conversations."""
        with self._lock:
            if state is None:
                return list(self._conversations.values())
            return [c for c in self._conversations.values() if c.state == state]

    def clear(self) -> None:
        """Clear all stored conversations."""
        with self._lock:
            self._conversations.clear()
