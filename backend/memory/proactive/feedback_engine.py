"""User Feedback Engine recalculating suggestion score weights from history outcomes."""

import logging
from typing import Dict, List
from memory.proactive.models import ProactiveRecommendationDomain

logger = logging.getLogger(__name__)


class UserFeedbackEngine:
    """Derives dynamic multiplier parameters for actions from user accept/dismiss histories."""

    def compute_feedback_weights(self, history: List[ProactiveRecommendationDomain]) -> Dict[str, float]:
        """Calculates dynamic weight boosts/penalties per command action class."""
        weights: Dict[str, float] = {}

        for r in history:
            action = r.action_type
            if action not in weights:
                weights[action] = 1.0

            status = r.status.lower()
            # Apply shifts based on recorded interaction outcomes
            if status == "accepted":
                weights[action] += 0.15
            elif status in {"dismissed", "rejected"}:
                weights[action] -= 0.25
            elif status == "ignored":
                weights[action] -= 0.05

            # Clamp weights to safe multipliers bounds
            weights[action] = min(max(weights[action], 0.1), 2.5)

        logger.info(f"Derived feedback engine weight mappings: {weights}")
        return weights
