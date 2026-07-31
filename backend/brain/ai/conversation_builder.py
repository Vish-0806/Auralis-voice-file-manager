"""ConversationBuilder component for constructing and managing conversation history (Phase 10.3).

Builds ordered conversation history, converts messages into provider-ready dictionaries,
enforces maximum history size limits, trims oldest messages first, and preserves system/developer turns.
"""

import logging
from typing import Any, Dict, List, Optional

from brain.ai.ai_models import PromptMessage, PromptRole
from brain.ai.token_estimator import TokenEstimator

logger = logging.getLogger(__name__)


class ConversationBuilder:
    """Builds, formats, and trims ordered conversation history."""

    def __init__(
        self,
        max_history_messages: int = 20,
        max_history_tokens: Optional[int] = None,
        token_estimator: Optional[TokenEstimator] = None,
    ) -> None:
        self.max_history_messages = max_history_messages
        self.max_history_tokens = max_history_tokens
        self.token_estimator = token_estimator or TokenEstimator()

    def build_conversation(
        self,
        raw_history: Optional[List[Any]] = None,
        max_messages: Optional[int] = None,
        max_tokens: Optional[int] = None,
    ) -> List[PromptMessage]:
        """Convert raw history objects/dictionaries into an ordered list of PromptMessage objects.

        Args:
            raw_history: List of dicts, tuples, or PromptMessage instances.
            max_messages: Override for max history messages.
            max_tokens: Override for max history tokens.

        Returns:
            Ordered list of PromptMessage objects, trimmed if exceeding caps.
        """
        if not raw_history:
            return []

        limit_messages = max_messages if max_messages is not None else self.max_history_messages
        limit_tokens = max_tokens if max_tokens is not None else self.max_history_tokens

        messages: List[PromptMessage] = []
        system_messages: List[PromptMessage] = []
        chat_messages: List[PromptMessage] = []

        for item in raw_history:
            msg = self._normalize_message(item)
            if msg is None:
                continue

            if msg.role in (PromptRole.SYSTEM, PromptRole.DEVELOPER):
                system_messages.append(msg)
            else:
                chat_messages.append(msg)

        # Enforce message count limit on chat messages (trim oldest first)
        if limit_messages is not None and len(chat_messages) > limit_messages:
            trimmed_count = len(chat_messages) - limit_messages
            logger.debug(f"Trimming {trimmed_count} oldest chat history messages.")
            chat_messages = chat_messages[-limit_messages:]

        # Enforce token limit if specified (trim oldest chat messages first)
        if limit_tokens is not None:
            while chat_messages:
                combined = system_messages + chat_messages
                est_tokens = self.token_estimator.estimate_tokens(combined)
                if est_tokens <= limit_tokens:
                    break
                chat_messages.pop(0)  # Trim oldest

        return system_messages + chat_messages

    def format_messages_for_provider(
        self,
        messages: List[PromptMessage],
    ) -> List[Dict[str, Any]]:
        """Convert PromptMessage objects into standard provider-ready message dictionaries."""
        formatted: List[Dict[str, Any]] = []

        for msg in messages:
            role_str = msg.role.value if hasattr(msg.role, "value") else str(msg.role)

            # Standardize non-standard roles for provider API compliance
            if role_str in ("developer", "memory", "workspace"):
                role_str = "system"

            entry: Dict[str, Any] = {"role": role_str, "content": msg.content}
            if msg.name:
                entry["name"] = msg.name
            formatted.append(entry)

        return formatted

    def _normalize_message(self, item: Any) -> Optional[PromptMessage]:
        """Normalize various input formats (PromptMessage, dict, tuple) into PromptMessage."""
        if isinstance(item, PromptMessage):
            return item

        if isinstance(item, dict):
            role_val = item.get("role", "user")
            content_val = item.get("content", "")

            # Map role string to PromptRole enum
            role_enum = self._map_role_string(str(role_val))
            return PromptMessage(
                role=role_enum,
                content=str(content_val),
                name=item.get("name"),
            )

        if isinstance(item, (list, tuple)) and len(item) >= 2:
            role_enum = self._map_role_string(str(item[0]))
            return PromptMessage(role=role_enum, content=str(item[1]))

        if isinstance(item, str):
            return PromptMessage(role=PromptRole.USER, content=item)

        return None

    def _map_role_string(self, role_str: str) -> PromptRole:
        """Map role string to PromptRole enum value."""
        clean_role = role_str.lower().strip()
        role_map = {
            "system": PromptRole.SYSTEM,
            "developer": PromptRole.DEVELOPER,
            "user": PromptRole.USER,
            "assistant": PromptRole.ASSISTANT,
            "tool": PromptRole.TOOL,
            "memory": PromptRole.MEMORY,
            "workspace": PromptRole.WORKSPACE,
        }
        return role_map.get(clean_role, PromptRole.USER)
