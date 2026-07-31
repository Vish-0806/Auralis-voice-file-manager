"""TokenEstimator component for approximating prompt size and token counts (Phase 10.3).

Provides character count, estimated token count (~4 characters per token + per-message overhead),
and detailed breakdown by role and prompt section without external tokenizer dependencies.
"""

import logging
from typing import Any, Dict, List, Union, Optional

from brain.ai.ai_models import Prompt, PromptMessage, PromptRole

logger = logging.getLogger(__name__)


class TokenEstimator:
    """Estimates character counts, token counts, and section breakdowns for prompts."""

    CHARS_PER_TOKEN: float = 4.0
    PER_MESSAGE_OVERHEAD_TOKENS: int = 4

    def estimate_characters(
        self,
        item: Union[str, PromptMessage, List[PromptMessage], List[Dict[str, Any]], Prompt],
    ) -> int:
        """Calculate total character count of string, PromptMessage, list of messages, or Prompt object."""
        if item is None:
            return 0

        if isinstance(item, str):
            return len(item)

        if isinstance(item, PromptMessage):
            return len(item.content)

        if isinstance(item, list):
            total = 0
            for msg in item:
                if isinstance(msg, PromptMessage):
                    total += len(msg.content)
                elif isinstance(msg, dict):
                    content = msg.get("content", "")
                    total += len(content) if isinstance(content, str) else len(str(content))
                elif isinstance(msg, str):
                    total += len(msg)
            return total

        if isinstance(item, Prompt):
            total = (
                len(item.system_prompt)
                + len(item.developer_prompt)
                + len(item.user_prompt)
                + len(item.tool_prompt)
                + len(item.memory_prompt)
                + len(getattr(item, "workspace_prompt", ""))
            )
            if item.formatted_messages:
                total += sum(len(msg.content) for msg in item.formatted_messages)
            return total

        return len(str(item))

    def estimate_tokens(
        self,
        item: Union[str, PromptMessage, List[PromptMessage], List[Dict[str, Any]], Prompt],
    ) -> int:
        """Estimate token count for text or message structures.

        Uses ~4 characters per token calculation rule plus fixed per-message overhead.
        """
        if item is None:
            return 0

        if isinstance(item, str):
            if not item.strip():
                return 0
            return max(1, int(len(item) / self.CHARS_PER_TOKEN))

        if isinstance(item, PromptMessage):
            content_tokens = int(len(item.content) / self.CHARS_PER_TOKEN)
            return content_tokens + self.PER_MESSAGE_OVERHEAD_TOKENS

        if isinstance(item, list):
            total_tokens = 0
            for msg in item:
                if isinstance(msg, PromptMessage):
                    total_tokens += self.estimate_tokens(msg)
                elif isinstance(msg, dict):
                    content = str(msg.get("content", ""))
                    total_tokens += int(len(content) / self.CHARS_PER_TOKEN) + self.PER_MESSAGE_OVERHEAD_TOKENS
                elif isinstance(msg, str):
                    total_tokens += self.estimate_tokens(msg)
            return total_tokens

        if isinstance(item, Prompt):
            if item.formatted_messages:
                return self.estimate_tokens(item.formatted_messages)

            raw_chars = self.estimate_characters(item)
            return int(raw_chars / self.CHARS_PER_TOKEN)

        return int(len(str(item)) / self.CHARS_PER_TOKEN)

    def estimate_prompt_breakdown(self, prompt: Prompt) -> Dict[str, Any]:
        """Generate a detailed breakdown of characters, tokens, and message counts per section/role."""
        breakdown: Dict[str, Any] = {
            "total_characters": self.estimate_characters(prompt),
            "total_tokens": self.estimate_tokens(prompt),
            "message_count": len(prompt.formatted_messages),
            "sections": {
                "system": {
                    "characters": len(prompt.system_prompt),
                    "tokens": self.estimate_tokens(prompt.system_prompt),
                },
                "developer": {
                    "characters": len(prompt.developer_prompt),
                    "tokens": self.estimate_tokens(prompt.developer_prompt),
                },
                "memory": {
                    "characters": len(prompt.memory_prompt),
                    "tokens": self.estimate_tokens(prompt.memory_prompt),
                },
                "workspace": {
                    "characters": len(getattr(prompt, "workspace_prompt", "")),
                    "tokens": self.estimate_tokens(getattr(prompt, "workspace_prompt", "")),
                },
                "tool": {
                    "characters": len(prompt.tool_prompt),
                    "tokens": self.estimate_tokens(prompt.tool_prompt),
                },
                "user": {
                    "characters": len(prompt.user_prompt),
                    "tokens": self.estimate_tokens(prompt.user_prompt),
                },
            },
            "by_role": {},
        }

        role_counts: Dict[str, int] = {}
        role_tokens: Dict[str, int] = {}

        for msg in prompt.formatted_messages:
            role_key = msg.role.value if hasattr(msg.role, "value") else str(msg.role)
            role_counts[role_key] = role_counts.get(role_key, 0) + 1
            role_tokens[role_key] = role_tokens.get(role_key, 0) + self.estimate_tokens(msg)

        for role_key in role_counts:
            breakdown["by_role"][role_key] = {
                "count": role_counts[role_key],
                "tokens": role_tokens[role_key],
            }

        return breakdown
