"""Scoring engine assessing and weight-adjusting proactive suggestions."""

import logging
from typing import Dict, List
from memory.proactive.models import PredictionContext, ProactiveRecommendationDomain

logger = logging.getLogger(__name__)


class RecommendationScoringEngine:
    """Calculates multidimensional confidence scores for proactive suggestions."""

    def score_recommendations(
        self,
        recommendations: List[ProactiveRecommendationDomain],
        context: PredictionContext,
        feedback_weights: Dict[str, float],
    ) -> List[ProactiveRecommendationDomain]:
        """Runs scoring algorithms over suggestions, factoring in history indices and feedback weights."""
        for r in recommendations:
            frequency_score = 0.5
            recency_score = 0.5
            workspace_score = 0.5
            goal_score = 0.5
            preference_score = 0.5
            routine_score = 0.5

            source = r.scoring_details.get("source", "")

            # 1. Frequency / Recency scoring
            if context.executions:
                matching_runs = [e for e in context.executions if getattr(e, "action", "") == r.action_type]
                if matching_runs:
                    frequency_score = min(len(matching_runs) / 10.0, 1.0)
                    recency_score = 0.8
                else:
                    frequency_score = 0.2
                    recency_score = 0.2

            # 2. Workspace similarity
            if source in {"workspace_intelligence", "git_repository", "python_project"}:
                workspace_score = 0.9

            # 3. Preference similarity
            if context.preferences and source == "preference_automation":
                preference_score = 0.9

            # 4. Routine similarity
            if context.routines:
                matching_routines = [
                    ro for ro in context.routines if ro.trigger_condition.get("trigger_event") == r.action_type
                ]
                if matching_routines:
                    routine_score = 0.9

            # 5. Apply dynamic user feedback weights
            feedback_mult = feedback_weights.get(r.action_type, 1.0)

            # Weighted base sum formula
            base_score = (
                frequency_score * 0.15
                + recency_score * 0.15
                + workspace_score * 0.2
                + goal_score * 0.1
                + preference_score * 0.2
                + routine_score * 0.2
            )

            # Apply feedback multipliers and clamp to [0.0, 1.0]
            final_score = min(max(base_score * feedback_mult, 0.0), 1.0)

            r.confidence_score = final_score
            r.scoring_details.update(
                {
                    "frequency_score": frequency_score,
                    "recency_score": recency_score,
                    "workspace_score": workspace_score,
                    "goal_score": goal_score,
                    "preference_score": preference_score,
                    "routine_score": routine_score,
                    "feedback_multiplier": feedback_mult,
                }
            )

        return recommendations
