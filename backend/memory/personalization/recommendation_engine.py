"""User Personalized Recommendation Engine."""

import logging
import datetime
from typing import Any, Dict, List
from memory.personalization.personalization_models import PersonalizationSuggestion

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Generates personalized workspace switches, routine prompts, and preference corrections."""

    @staticmethod
    def generate(
        user_id: int,
        session_id: str,
        context: Dict[str, Any],
        preferences: Dict[str, Any],
        learned_routines: List[Any],
        workspaces: List[Any],
    ) -> List[PersonalizationSuggestion]:
        """Analyzes active state indicators and returns suggestions for the user.

        Args:
            user_id: Target user ID.
            session_id: Active session ID.
            context: Active Context dictionary.
            preferences: Flat preference settings.
            learned_routines: Learned user routines.
            workspaces: User workspace profiles.

        Returns:
            List of suggestion containers.
        """
        logger.info(f"Analyzing behavior indicators to generate recommendations for user {user_id}.")
        suggestions: List[PersonalizationSuggestion] = []

        # 1. Path cues: Recommend coding workspace switches
        active_path = context.get("active_workspace") or context.get("current_project") or ""
        if active_path:
            path_lower = active_path.lower()
            if any(term in path_lower for term in ["code", "dev", "project", "git"]):
                # Look for workspace profiles matching coding cues
                coding_ws = next((w for w in workspaces if "code" in w.name.lower() or "coding" in w.name.lower()), None)
                if coding_ws:
                    suggestions.append(
                        PersonalizationSuggestion(
                            type="workspace_restore",
                            message=f"Based on your active directory '{active_path}', switch to your '{coding_ws.name}' workspace profile?",
                            payload={"profile_id": coding_ws.id, "profile_name": coding_ws.name},
                        )
                    )

        # 2. Time cues: Recommend switching theme to dark at night
        current_hour = datetime.datetime.now().hour
        if current_hour >= 18 or current_hour < 6:
            # Check theme setting
            theme = "light"
            for category_settings in preferences.values():
                if isinstance(category_settings, dict) and "theme" in category_settings:
                    theme = category_settings["theme"]

            if theme == "light":
                suggestions.append(
                    PersonalizationSuggestion(
                        type="preference_update",
                        message="It is late evening. Would you like to switch to Dark Mode theme to reduce eye strain?",
                        payload={"category": "ide", "key": "theme", "value": "dark"},
                    )
                )

        # 3. Frequency cues: Suggest high confidence routine prompts
        for routine in learned_routines:
            score = getattr(routine, "confidence_score", 0.0)
            if score >= 0.8:
                trigger = getattr(routine, "trigger_event", "")
                suggestions.append(
                    PersonalizationSuggestion(
                        type="routine_trigger",
                        message=f"Would you like to trigger your learned routine for '{trigger}'?",
                        payload={
                            "routine_id": routine.id,
                            "trigger_event": trigger,
                            "action_sequence": getattr(routine, "action_sequence", {}),
                        },
                    )
                )

        return suggestions
