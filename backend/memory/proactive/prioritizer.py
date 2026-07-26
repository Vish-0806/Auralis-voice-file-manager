"""Recommendation Prioritizer sorting and deduplicating suggestions."""

import logging
from typing import List
from memory.proactive.models import ProactiveRecommendationDomain

logger = logging.getLogger(__name__)


class RecommendationPrioritizer:
    """Handles sorting, duplicate mitigation, and limits for proactive suggestions."""

    def prioritize(
        self, recommendations: List[ProactiveRecommendationDomain], limit: int = 3
    ) -> List[ProactiveRecommendationDomain]:
        """Deduplicates, orders by confidence and name, and slices list to capacity limit."""
        seen = set()
        deduplicated: List[ProactiveRecommendationDomain] = []

        # 1. De-duplication check
        for r in recommendations:
            key = (r.suggestion_text.lower(), r.action_type.lower())
            if key not in seen:
                seen.add(key)
                deduplicated.append(r)

        # 2. Sort by confidence score (descending), then alphabetically by text (ascending)
        deduplicated.sort(key=lambda r: (-r.confidence_score, r.suggestion_text))

        # 3. Apply capacity limit
        result = deduplicated[:limit]
        logger.info(f"Prioritizer matched {len(result)} recommendations out of {len(recommendations)}")
        return result
