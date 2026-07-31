"""PromptOptimizer component for merging, deduplicating, ordering, and trimming prompts (Phase 10.3).

Responsibilities:
- Merge prompt layers into ordered message list
- Enforce strict priority ordering: System -> Developer -> Memory -> Workspace -> Conversation -> User
- Remove duplicate messages while preserving priority order
- Enforce max token limits by trimming lower-priority messages first
"""

import logging
from typing import Any, Dict, List, Optional

from brain.ai.ai_models import Prompt, PromptMessage, PromptRole
from brain.ai.token_estimator import TokenEstimator

logger = logging.getLogger(__name__)


# Priority rank for prompt ordering (1 = Highest, 6 = Lowest)
ROLE_PRIORITY: Dict[PromptRole, int] = {
    PromptRole.SYSTEM: 1,
    PromptRole.DEVELOPER: 2,
    PromptRole.MEMORY: 3,
    PromptRole.WORKSPACE: 4,
    PromptRole.ASSISTANT: 5,
    PromptRole.TOOL: 5,
    PromptRole.USER: 6,
}


class PromptOptimizer:
    """Optimizes, merges, deduplicates, and trims structured Prompt objects."""

    def __init__(self, token_estimator: Optional[TokenEstimator] = None) -> None:
        self.token_estimator = token_estimator or TokenEstimator()

    def optimize_prompt(
        self,
        prompt: Prompt,
        max_tokens: Optional[int] = None,
        deduplicate: bool = True,
    ) -> Prompt:
        """Optimize a Prompt object by merging layers, sorting by priority, deduplicating, and trimming.

        Args:
            prompt: Structured Prompt model input.
            max_tokens: Optional token limit cap.
            deduplicate: If True, remove duplicate messages.

        Returns:
            Optimized Prompt instance.
        """
        # 1. Collect all messages from sections and formatted_messages
        all_messages: List[PromptMessage] = []

        if prompt.system_prompt:
            all_messages.append(PromptMessage(role=PromptRole.SYSTEM, content=prompt.system_prompt))
        if prompt.developer_prompt:
            all_messages.append(PromptMessage(role=PromptRole.DEVELOPER, content=prompt.developer_prompt))
        if prompt.memory_prompt:
            all_messages.append(PromptMessage(role=PromptRole.MEMORY, content=prompt.memory_prompt))
        if getattr(prompt, "workspace_prompt", ""):
            all_messages.append(PromptMessage(role=PromptRole.WORKSPACE, content=getattr(prompt, "workspace_prompt", "")))
        if prompt.tool_prompt:
            all_messages.append(PromptMessage(role=PromptRole.TOOL, content=prompt.tool_prompt))

        # Add explicit formatted messages if present
        all_messages.extend(prompt.formatted_messages)

        if prompt.user_prompt and not any(m.role == PromptRole.USER and m.content == prompt.user_prompt for m in prompt.formatted_messages):
            all_messages.append(PromptMessage(role=PromptRole.USER, content=prompt.user_prompt))

        # 2. Deduplicate messages if requested
        if deduplicate:
            all_messages = self._deduplicate_messages(all_messages)

        # 3. Sort by priority order while maintaining stable relative order within same priority
        all_messages = self._sort_by_priority(all_messages)

        # 4. Enforce max token limit if specified
        if max_tokens is not None and max_tokens > 0:
            all_messages = self._trim_to_token_limit(all_messages, max_tokens)

        # 5. Calculate updated token estimate
        new_token_estimate = self.token_estimator.estimate_tokens(all_messages)

        return Prompt(
            system_prompt=prompt.system_prompt,
            developer_prompt=prompt.developer_prompt,
            user_prompt=prompt.user_prompt,
            tool_prompt=prompt.tool_prompt,
            memory_prompt=prompt.memory_prompt,
            workspace_prompt=getattr(prompt, "workspace_prompt", ""),
            formatted_messages=all_messages,
            token_estimate=new_token_estimate,
            metadata={
                **prompt.metadata,
                "optimized": True,
                "deduplicated": deduplicate,
                "max_tokens_limit": max_tokens,
            },
        )

    def _deduplicate_messages(self, messages: List[PromptMessage]) -> List[PromptMessage]:
        """Remove duplicate messages based on (role, content) tuple, keeping first occurrence."""
        seen = set()
        deduped: List[PromptMessage] = []

        for msg in messages:
            role_key = msg.role.value if hasattr(msg.role, "value") else str(msg.role)
            key = (role_key, msg.content.strip())
            if key not in seen and msg.content.strip():
                seen.add(key)
                deduped.append(msg)

        return deduped

    def _sort_by_priority(self, messages: List[PromptMessage]) -> List[PromptMessage]:
        """Sort messages into canonical priority order: System -> Developer -> Memory -> Workspace -> Conversation -> User."""
        # Use stable sort (Python sort is stable) with priority weight
        def get_priority(msg: PromptMessage) -> int:
            return ROLE_PRIORITY.get(msg.role, 99)

        return sorted(messages, key=get_priority)

    def _trim_to_token_limit(
        self,
        messages: List[PromptMessage],
        max_tokens: int,
    ) -> List[PromptMessage]:
        """Trim lower-priority / oldest conversation messages when total tokens exceed max_tokens."""
        current_tokens = self.token_estimator.estimate_tokens(messages)
        if current_tokens <= max_tokens:
            return messages

        # Preserve System (1) and Developer (2) prompts at all costs
        # Trimming order: Conversation (5) -> User (6) -> Workspace (4) -> Memory (3)
        trimmed = list(messages)

        # First pass: trim conversation history messages (role ASSISTANT / TOOL or non-last USER)
        indices_to_remove = []
        for idx, msg in enumerate(trimmed):
            if msg.role in (PromptRole.ASSISTANT, PromptRole.TOOL):
                indices_to_remove.append(idx)

        for idx in reversed(indices_to_remove):
            trimmed.pop(idx)
            if self.token_estimator.estimate_tokens(trimmed) <= max_tokens:
                return trimmed

        # Second pass: trim workspace / memory if still over limit
        for idx in range(len(trimmed) - 1, -1, -1):
            if trimmed[idx].role in (PromptRole.WORKSPACE, PromptRole.MEMORY):
                trimmed.pop(idx)
                if self.token_estimator.estimate_tokens(trimmed) <= max_tokens:
                    return trimmed

        return trimmed
