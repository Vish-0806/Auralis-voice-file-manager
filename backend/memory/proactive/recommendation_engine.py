"""Proactive Recommendation Engine generating suggestion models from predictions."""

import logging
from typing import List
from memory.proactive.models import PredictionContext, ProactiveRecommendationDomain

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Generates user suggestions based on predicted actions and historical workspace parameters."""

    def generate_recommendations(
        self, user_id: int, predicted_actions: List[str], context: PredictionContext
    ) -> List[ProactiveRecommendationDomain]:
        """Maps predicted action intents to structured proactive recommendation suggestions."""
        recommendations: List[ProactiveRecommendationDomain] = []

        for action in predicted_actions:
            if action == "OPEN_APPLICATION":
                recommendations.append(
                    ProactiveRecommendationDomain(
                        user_id=user_id,
                        suggestion_text="Open VS Code?",
                        action_type="OPEN_APPLICATION",
                        scoring_details={"source": "preference_automation"}
                    )
                )
            elif action == "RUN_COMMAND":
                recommendations.append(
                    ProactiveRecommendationDomain(
                        user_id=user_id,
                        suggestion_text="Run Git Pull?",
                        action_type="RUN_COMMAND",
                        scoring_details={"source": "git_repository"}
                    )
                )
            elif action == "COMPILE_PROJECT":
                recommendations.append(
                    ProactiveRecommendationDomain(
                        user_id=user_id,
                        suggestion_text="Compile project?",
                        action_type="COMPILE_PROJECT",
                        scoring_details={"source": "python_project"}
                    )
                )

        # Workspace resume suggestion
        if context.workspace_info.get("workspace_path"):
            recommendations.append(
                ProactiveRecommendationDomain(
                    user_id=user_id,
                    suggestion_text="Resume previous workspace?",
                    action_type="OPEN_WORKSPACE",
                    scoring_details={"source": "workspace_intelligence"}
                )
            )

        # Continue activity suggestion
        if context.executions:
            recommendations.append(
                ProactiveRecommendationDomain(
                    user_id=user_id,
                    suggestion_text="Continue yesterday's work?",
                    action_type="RESUME_ACTIVITY",
                    scoring_details={"source": "execution_history"}
                )
            )

        logger.info(f"Generated {len(recommendations)} candidate recommendations.")
        return recommendations
