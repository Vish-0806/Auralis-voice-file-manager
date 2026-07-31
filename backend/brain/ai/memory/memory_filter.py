"""DefaultMemoryFilter for deduplication and token budgeting of AI memory items (Phase 10.5).

Removes duplicate items and trims memory payloads to fit within configurable token budgets
while preserving highest-ranked memories.
"""

import logging
from typing import List, Optional, Set

from brain.ai.token_estimator import TokenEstimator
from brain.ai.memory.exceptions import MemoryFilterError
from brain.ai.memory.interfaces import MemoryFilterInterface
from brain.ai.memory.memory_models import AIMemoryItem, MemoryScope

logger = logging.getLogger(__name__)


class DefaultMemoryFilter(MemoryFilterInterface):
    """Deduplicates and token-budgets memory items while preserving ranking order."""

    def __init__(self, token_estimator: Optional[TokenEstimator] = None) -> None:
        self.token_estimator = token_estimator or TokenEstimator()

    def filter_and_budget(
        self,
        items: List[AIMemoryItem],
        max_tokens: Optional[int] = None,
        deduplicate: bool = True,
    ) -> List[AIMemoryItem]:
        """Deduplicate items and trim to stay within token budget while preserving rank order.

        Args:
            items: Ranked list of AIMemoryItem objects.
            max_tokens: Maximum total tokens allowed for memory payload.
            deduplicate: If True, remove duplicate items.

        Returns:
            Filtered list of AIMemoryItem objects.

        Raises:
            MemoryFilterError: If filtering fails.
        """
        if not items:
            return []

        try:
            # 1. Deduplicate if enabled
            processed_items = self._deduplicate_items(items) if deduplicate else list(items)

            # 2. Enforce token budget if max_tokens specified
            if max_tokens is not None and max_tokens > 0:
                processed_items = self._apply_token_budget(processed_items, max_tokens)

            return processed_items

        except Exception as exc:
            raise MemoryFilterError(f"Failed to filter memory items: {exc}") from exc

    def _deduplicate_items(self, items: List[AIMemoryItem]) -> List[AIMemoryItem]:
        """Deduplicate memory items by (key, content) while preserving ranking order."""
        seen: Set[str] = set()
        deduped: List[AIMemoryItem] = []

        for item in items:
            normalized_content = item.content.strip().lower()
            key_hash = f"{item.key}:{normalized_content}"

            if key_hash not in seen and normalized_content:
                seen.add(key_hash)
                deduped.append(item)

        return deduped

    def _apply_token_budget(self, items: List[AIMemoryItem], max_tokens: int) -> List[AIMemoryItem]:
        """Keep highest ranked memory items that fit within max_tokens budget.

        PINNED items are given budget priority.
        """
        result: List[AIMemoryItem] = []
        accumulated_tokens = 0

        # Pass 1: Add PINNED items first up to budget
        pinned_items = [i for i in items if i.scope == MemoryScope.PINNED]
        non_pinned_items = [i for i in items if i.scope != MemoryScope.PINNED]

        for item in pinned_items:
            item_tokens = self.token_estimator.estimate_tokens(item.content)
            if accumulated_tokens + item_tokens <= max_tokens or not result:
                result.append(item)
                accumulated_tokens += item_tokens

        # Pass 2: Add non-pinned items in ranked order until budget full
        for item in non_pinned_items:
            item_tokens = self.token_estimator.estimate_tokens(item.content)
            if accumulated_tokens + item_tokens <= max_tokens:
                result.append(item)
                accumulated_tokens += item_tokens
            else:
                logger.debug(
                    f"Memory budget reached ({accumulated_tokens}/{max_tokens} tokens). "
                    f"Trimming item '{item.key}'."
                )

        return result
