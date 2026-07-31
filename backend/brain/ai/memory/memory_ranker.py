"""DefaultMemoryRanker for scoring and ranking AIMemoryItem objects (Phase 10.5).

Computes composite relevance scores using term matching, importance weights, and scope precedence
without external embedding models or vector databases.
"""

import re
import logging
from typing import Dict, List, Set

from brain.ai.memory.exceptions import MemoryRankingError
from brain.ai.memory.interfaces import MemoryRankerInterface
from brain.ai.memory.memory_models import AIMemoryItem, MemoryScope

logger = logging.getLogger(__name__)


SCOPE_WEIGHTS: Dict[MemoryScope, float] = {
    MemoryScope.PINNED: 1.0,
    MemoryScope.SESSION: 0.85,
    MemoryScope.RECENT: 0.7,
    MemoryScope.LONG_TERM: 0.5,
}


class DefaultMemoryRanker(MemoryRankerInterface):
    """Scoring and ranking engine for memory items."""

    def __init__(
        self,
        keyword_weight: float = 0.5,
        importance_weight: float = 0.35,
        scope_weight: float = 0.15,
    ) -> None:
        self.keyword_weight = keyword_weight
        self.importance_weight = importance_weight
        self.scope_weight = scope_weight

    def rank(
        self,
        items: List[AIMemoryItem],
        query: str = "",
    ) -> List[AIMemoryItem]:
        """Calculate composite relevance scores and sort items in descending score order.

        Args:
            items: List of raw AIMemoryItem objects.
            query: Query text string for keyword relevance scoring.

        Returns:
            List of AIMemoryItem objects with populated relevance_score fields, sorted by score.

        Raises:
            MemoryRankingError: If ranking computation fails.
        """
        if not items:
            return []

        try:
            query_terms = self._tokenize(query)
            ranked_items: List[AIMemoryItem] = []

            for item in items:
                text_content = f"{item.key} {item.content}".lower()
                kw_score = self._compute_keyword_overlap(text_content, query_terms) if query_terms else 0.5
                sc_weight = SCOPE_WEIGHTS.get(item.scope, 0.5)

                composite_score = round(
                    (kw_score * self.keyword_weight)
                    + (item.importance_score * self.importance_weight)
                    + (sc_weight * self.scope_weight),
                    4,
                )

                # Construct new item with calculated relevance score (AIMemoryItem is immutable)
                ranked_items.append(
                    AIMemoryItem(
                        memory_id=item.memory_id,
                        key=item.key,
                        content=item.content,
                        scope=item.scope,
                        importance_score=item.importance_score,
                        relevance_score=composite_score,
                        recency_timestamp=item.recency_timestamp,
                        metadata=item.metadata,
                    )
                )

            # Sort descending by relevance_score
            ranked_items.sort(key=lambda x: x.relevance_score, reverse=True)
            return ranked_items

        except Exception as exc:
            raise MemoryRankingError(f"Failed to rank memory items: {exc}") from exc

    def _tokenize(self, text: str) -> Set[str]:
        """Extract unique lowercase alpha-numeric terms from query text."""
        if not text:
            return set()
        words = re.findall(r"\w+", text.lower())
        # Filter common stopwords
        stopwords = {"a", "an", "the", "in", "on", "at", "to", "for", "of", "and", "or", "is", "it", "my", "me", "you"}
        return {w for w in words if len(w) > 1 and w not in stopwords}

    def _compute_keyword_overlap(self, content_text: str, query_terms: Set[str]) -> float:
        """Compute proportion of query terms matching content text."""
        if not query_terms:
            return 0.0

        matched = sum(1 for term in query_terms if term in content_text)
        return min(1.0, matched / len(query_terms))
