"""Suggestion History Manager tracking user response lifecycle states."""

import logging
from typing import Any, List, Optional
from memory.proactive.models import ProactiveRecommendationDomain

logger = logging.getLogger(__name__)


class SuggestionHistoryManager:
    """Stores generated suggestions and updates state records when user interacts with them."""

    def __init__(self, repository: Any) -> None:
        """Initializes history manager with a database repository."""
        self.repository = repository

    def save_recommendation(self, recommendation: ProactiveRecommendationDomain) -> ProactiveRecommendationDomain:
        """Persists a new suggestion record to the database."""
        return self.repository.create(recommendation)

    def record_feedback(self, recommendation_id: int, status: str) -> Optional[ProactiveRecommendationDomain]:
        """Modifies a recommendation lifecycle state status ('accepted', 'dismissed', 'ignored')."""
        existing = self.repository.get_by_id(recommendation_id)
        if not existing:
            logger.warning(f"Could not find proactive recommendation with ID {recommendation_id}")
            return None

        # Update status
        existing.status = status
        updated = self.repository.update(recommendation_id, existing)
        logger.info(f"Recorded suggestion ID {recommendation_id} outcome: '{status}'")
        return updated

    def get_history(self, user_id: int) -> List[ProactiveRecommendationDomain]:
        """Retrieves all proactive recommendation log histories for a user."""
        return self.repository.search({"user_id": user_id})
