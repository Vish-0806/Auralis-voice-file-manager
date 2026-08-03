"""History Manager implementation for Auralis (Phase 13.2).

Manages conversation message appending, pagination, trimming, and maximum history bounds.
Does NOT perform AI summarization or reasoning. Thread-safe using threading.RLock().
"""

from datetime import datetime, timezone
import logging
import threading
from typing import Any, Dict, List, Optional

from brain.assistant.conversation.exceptions import ConversationValidationError
from brain.assistant.conversation.interfaces import IConversationHistoryManager
from brain.assistant.conversation.models import (
    ConversationHistory,
    ConversationMessage,
    MessageRole,
)

logger = logging.getLogger(__name__)


class HistoryManager(IConversationHistoryManager):
    """Thread-safe history manager handling message storage, pagination, and trimming."""

    def __init__(
        self,
        max_history_per_conversation: int = 1000,
        lock: Optional[threading.RLock] = None,
    ) -> None:
        self._lock = lock or threading.RLock()
        self._max_history = max_history_per_conversation
        self._histories: Dict[str, List[ConversationMessage]] = {}

    def append_message(
        self,
        conversation_id: str,
        role: Any,
        content: str,
        sender_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConversationMessage:
        """Append a message to the conversation history."""
        if not conversation_id:
            raise ConversationValidationError("conversation_id cannot be empty")

        if isinstance(role, MessageRole):
            msg_role = role
        elif isinstance(role, str):
            try:
                msg_role = MessageRole(role.upper())
            except ValueError:
                msg_role = MessageRole.USER
        else:
            msg_role = MessageRole.USER

        tokens_est = max(1, len(content) // 4)

        message = ConversationMessage(
            conversation_id=conversation_id,
            role=msg_role,
            content=content,
            sender_id=sender_id,
            timestamp=datetime.now(timezone.utc),
            metadata=metadata or {},
            tokens_estimate=tokens_est,
        )

        with self._lock:
            if conversation_id not in self._histories:
                self._histories[conversation_id] = []

            self._histories[conversation_id].append(message)

            # Auto-trim if max bound is exceeded
            if len(self._histories[conversation_id]) > self._max_history:
                self._histories[conversation_id] = self._histories[conversation_id][-self._max_history :]

            logger.debug("Appended message msg_id=%s to conv_id=%s", message.message_id, conversation_id)
            return message

    def get_history(
        self,
        conversation_id: str,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> ConversationHistory:
        """Retrieve conversation message history with pagination."""
        with self._lock:
            all_msgs = self._histories.get(conversation_id, [])
            total_msgs = len(all_msgs)

            if offset < 0:
                offset = 0

            if limit is not None and limit >= 0:
                sliced = all_msgs[offset : offset + limit]
            else:
                sliced = all_msgs[offset:]

            total_tokens = sum(m.tokens_estimate for m in sliced)

            return ConversationHistory(
                conversation_id=conversation_id,
                messages=sliced,
                total_messages=total_msgs,
                total_tokens_estimate=total_tokens,
                trimmed=len(all_msgs) > len(sliced),
                last_updated=datetime.now(timezone.utc),
            )

    def trim_history(
        self, conversation_id: str, max_messages: int
    ) -> ConversationHistory:
        """Trim message history to retain the most recent max_messages."""
        with self._lock:
            all_msgs = self._histories.get(conversation_id, [])
            if len(all_msgs) > max_messages:
                trimmed_msgs = all_msgs[-max_messages:]
                self._histories[conversation_id] = trimmed_msgs
                is_trimmed = True
            else:
                trimmed_msgs = list(all_msgs)
                is_trimmed = False

            total_tokens = sum(m.tokens_estimate for m in trimmed_msgs)

            return ConversationHistory(
                conversation_id=conversation_id,
                messages=trimmed_msgs,
                total_messages=len(trimmed_msgs),
                total_tokens_estimate=total_tokens,
                trimmed=is_trimmed,
                last_updated=datetime.now(timezone.utc),
            )

    def clear(self) -> None:
        """Clear all stored histories."""
        with self._lock:
            self._histories.clear()
