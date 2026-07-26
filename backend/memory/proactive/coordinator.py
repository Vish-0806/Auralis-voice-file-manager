"""Proactive Assistant Coordinator facade mapping all sub-engine calls."""

import logging
from typing import List
from memory.proactive.models import PredictionContext, ProactiveRecommendationDomain
from memory.proactive.activity_predictor import ActivityPredictor
from memory.proactive.recommendation_engine import RecommendationEngine
from memory.proactive.scoring_engine import RecommendationScoringEngine
from memory.proactive.prioritizer import RecommendationPrioritizer
from memory.proactive.history_manager import SuggestionHistoryManager
from memory.proactive.feedback_engine import UserFeedbackEngine

logger = logging.getLogger(__name__)


class ProactiveAssistantCoordinator:
    """Coordinates behavior predictions, suggestion creation, rank prioritization, and history management."""

    def __init__(
        self,
        predictor: ActivityPredictor,
        engine: RecommendationEngine,
        scorer: RecommendationScoringEngine,
        prioritizer: RecommendationPrioritizer,
        history_manager: SuggestionHistoryManager,
        feedback_engine: UserFeedbackEngine,
    ) -> None:
        """Initializes the proactive assistant engine facade."""
        self.predictor = predictor
        self.engine = engine
        self.scorer = scorer
        self.prioritizer = prioritizer
        self.history_manager = history_manager
        self.feedback_engine = feedback_engine

    def generate_proactive_recommendations(
        self, user_id: int, context: PredictionContext
    ) -> List[ProactiveRecommendationDomain]:
        """Runs the proactive suggestion generation loop: predict, compile, score, rank, and log."""
        # 1. Fetch user feedback score weights
        history = self.history_manager.get_history(user_id)
        weights = self.feedback_engine.compute_feedback_weights(history)

        # 2. Extract action target predictions
        predicted_actions = self.predictor.predict_next_actions(context)

        # 3. Generate candidate suggestions
        candidates = self.engine.generate_recommendations(user_id, predicted_actions, context)

        # 4. Score suggestions
        scored = self.scorer.score_recommendations(candidates, context, weights)

        # 5. Deduplicate and select top candidates
        prioritized = self.prioritizer.prioritize(scored)

        # 6. Persist suggestions to history database catalog
        for r in prioritized:
            self.history_manager.save_recommendation(r)

        return prioritized
