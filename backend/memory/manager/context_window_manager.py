"""Standalone Context Window Manager for optimizing AssistantContext token limits."""

import logging
import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from memory.models.domain_models import MemoryEntry, AssistantContext
from memory.manager.context_builder import ContextWindowConfig

logger = logging.getLogger(__name__)


class ContextWindowManager:
    """Manages the token budget of AssistantContext by pruning low-priority elements."""

    def __init__(self, config: Optional[ContextWindowConfig] = None) -> None:
        """Initializes the ContextWindowManager.

        Args:
            config: Optional ContextWindowConfig parameter.
        """
        self.config = config or ContextWindowConfig()

    def estimate_tokens(self, text: str) -> int:
        """Lightweight heuristic estimator. Establishes ~4 characters per token.

        Easily replaceable in the future with tiktoken or sentencepiece.

        Args:
            text: Input string.

        Returns:
            Estimated token count.
        """
        if not text:
            return 0
        return max(1, (len(text) + 3) // 4)

    def estimate_entry_tokens(self, entry: MemoryEntry) -> int:
        """Estimates the tokens consumed by a single MemoryEntry content and metadata.

        Args:
            entry: The MemoryEntry structure.

        Returns:
            Estimated token count.
        """
        tokens = self.estimate_tokens(entry.content)
        if entry.metadata and entry.metadata.additional_info:
            tokens += self.estimate_tokens(str(entry.metadata.additional_info))
        return tokens

    def _get_created_at(self, entry: MemoryEntry) -> datetime:
        """Safe extraction of timezone-aware created_at timestamp for sorting.

        Args:
            entry: The MemoryEntry structure.

        Returns:
            A timezone-aware datetime instance.
        """
        if entry.metadata and entry.metadata.created_at:
            dt = entry.metadata.created_at
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt
        return datetime.fromtimestamp(0, timezone.utc)

    def optimize_context_window(
        self, context: AssistantContext, query_text: Optional[str] = None
    ) -> AssistantContext:
        """Prunes low-priority elements in AssistantContext to fit within the token budget.

        Honors mandatory elements (current session, minimum conversation history, and query).

        Args:
            context: The raw AssistantContext model to optimize.
            query_text: Optional current user prompt text.

        Returns:
            An optimized AssistantContext fitting the token budget.
        """
        logger.info("Context Window Started")

        # 1. Calculate the available token budget
        total_budget = self.config.token_budget
        reserved = self.config.reserved_response_tokens + self.config.safety_margin_tokens
        available_budget = total_budget - reserved

        query_tokens = 0
        if query_text:
            query_tokens = self.estimate_tokens(query_text)
            available_budget -= query_tokens

        logger.info(
            f"Token limits computed: total={total_budget}, reserved={reserved}, available={available_budget}"
        )

        if available_budget < 0:
            logger.warning("Mandatory system/response reservation exceeds total token budget.")
            available_budget = 0

        # Extract context fields into local lists
        conversations = list(context.recent_conversations)
        executions = list(context.recent_executions)
        preferences = list(context.preferences)
        current_context = context.current_context
        workspace_context = context.workspace_context

        # 2. Keep Mandatory Context
        mandatory_tokens = 0
        final_conversations = []
        final_executions = []
        final_preferences = []
        final_current_context = current_context
        final_workspace_context = workspace_context

        # Current context is mandatory
        if current_context:
            mandatory_tokens += self.estimate_entry_tokens(current_context)

        # Minimum recent conversations are mandatory to protect chat context
        sorted_by_recency = sorted(conversations, key=self._get_created_at, reverse=True)
        min_conv_count = min(len(sorted_by_recency), self.config.minimum_recent_conversations)
        protected_convs = sorted_by_recency[:min_conv_count]
        remaining_convs = sorted_by_recency[min_conv_count:]

        for c in protected_convs:
            mandatory_tokens += self.estimate_entry_tokens(c)

        workspace_tokens = 0
        if workspace_context:
            workspace_tokens = self.estimate_entry_tokens(workspace_context)

        # Remaining budget after mandatory items
        remaining_budget = available_budget - mandatory_tokens
        logger.info(f"Estimated Tokens for mandatory items: {mandatory_tokens}, Budget Remaining: {remaining_budget}")

        items_removed = 0

        # If mandatory items exceed budget, drop all optional items and return
        if remaining_budget <= 0:
            logger.warning("Mandatory items exceed available token budget.")
            # Drop all optional items
            items_removed = len(remaining_convs) + len(executions) + len(preferences)
            if workspace_context:
                items_removed += 1
                final_workspace_context = None

            # Sort conversations chronologically before packaging
            final_conversations = sorted(protected_convs, key=self._get_created_at)

            final_token_count = mandatory_tokens + query_tokens
            logger.info(
                f"Items Removed: {items_removed}, Final Token Count: {final_token_count}"
            )
            logger.info("Context Window Completed")
            return AssistantContext(
                recent_conversations=final_conversations,
                recent_executions=final_executions,
                current_context=final_current_context,
                preferences=final_preferences,
                workspace_context=final_workspace_context,
                workspace_analysis=context.workspace_analysis,
                metadata=context.metadata,
            )

        # 3. Add other items according to priority, count limits, and relevance
        # Group A: Workspace Profile (High priority workspace path metadata)
        if workspace_context:
            if remaining_budget >= workspace_tokens:
                final_workspace_context = workspace_context
                remaining_budget -= workspace_tokens
            else:
                final_workspace_context = None
                items_removed += 1

        # Group B: User Preferences (usually small, high value)
        for pref in preferences:
            pref_tokens = self.estimate_entry_tokens(pref)
            if remaining_budget >= pref_tokens:
                final_preferences.append(pref)
                remaining_budget -= pref_tokens
            else:
                items_removed += 1

        # Group C: Remaining conversations (ranked order from ContextBuilder)
        # Filters remaining conversations preserving their relative ranked order
        ranked_remaining_convs = [c for c in conversations if c in remaining_convs]
        keep_remaining_convs = []
        max_additional = max(0, self.config.maximum_conversations - len(protected_convs))
        
        for c in ranked_remaining_convs:
            if len(keep_remaining_convs) >= max_additional:
                items_removed += 1
                continue
            c_tokens = self.estimate_entry_tokens(c)
            if remaining_budget >= c_tokens:
                keep_remaining_convs.append(c)
                remaining_budget -= c_tokens
            else:
                items_removed += 1

        # Merge protected turns and additional relevant turns, sort chronologically
        all_kept_convs = protected_convs + keep_remaining_convs
        final_conversations = sorted(all_kept_convs, key=self._get_created_at)

        # Group D: Executions (ranked order from ContextBuilder)
        for ex in executions:
            if len(final_executions) >= self.config.maximum_execution_history:
                items_removed += 1
                continue
            ex_tokens = self.estimate_entry_tokens(ex)
            if remaining_budget >= ex_tokens:
                final_executions.append(ex)
                remaining_budget -= ex_tokens
            else:
                items_removed += 1

        # Placeholder / Extension points for alternative strategies
        if self.config.truncation_strategy == "truncation_suffix":
            pass  # Extension point: Truncate single strings with [...]
        elif self.config.truncation_strategy == "level_of_detail":
            pass  # Extension point: Summarize logs

        # Calculate final token count
        final_token_count = (total_budget - reserved) - remaining_budget + query_tokens
        logger.info(
            f"Items Removed: {items_removed}, Final Token Count: {final_token_count}"
        )
        logger.info("Context Window Completed")

        return AssistantContext(
            recent_conversations=final_conversations,
            recent_executions=final_executions,
            current_context=final_current_context,
            preferences=final_preferences,
            workspace_context=final_workspace_context,
            workspace_analysis=context.workspace_analysis,
            metadata=context.metadata,
        )
