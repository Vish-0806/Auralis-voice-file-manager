"""User personalized profile builder."""

import logging
from typing import Any, Optional
from memory.personalization.personalization_models import UserProfile

logger = logging.getLogger(__name__)


class ProfileBuilder:
    """Combines preferences, context parameters, and routine learning lists into a UserProfile."""

    @staticmethod
    def build(
        user_id: int,
        session_id: str,
        preference_service: Any,
        context_service: Any,
        routine_service: Any,
    ) -> UserProfile:
        """Retrieves and consolidates user settings summaries across memory modules.

        Args:
            user_id: Target user ID.
            session_id: Active session ID.
            preference_service: Consolidated PreferenceService.
            context_service: Consolidated ContextService.
            routine_service: Consolidated RoutineLearningService.

        Returns:
            The compiled UserProfile instance.
        """
        logger.info(f"Building consolidated UserProfile summary for user {user_id}.")

        # 1. Pull active workspace from Context
        ctx = context_service.load(user_id, session_id)
        active_path = ctx.get("active_workspace") or ctx.get("current_project")

        # 2. Consolidate Preferences
        prefs = {}
        for category in ["ide", "voice", "desktop", "system"]:
            try:
                # Load all preferences for category
                prefs[category] = preference_service.get(user_id, category)
            except Exception as e:
                logger.debug(f"Failed to fetch preference category '{category}': {e}")

        # 3. Retrieve learned routines count
        routines_count = 0
        try:
            routines = routine_service.list(user_id)
            routines_count = len(routines)
        except Exception as e:
            logger.debug(f"Failed to load learned routines list: {e}")

        # 4. Fetch recent executions directly from routine_service database history
        recent_actions = []
        try:
            if hasattr(routine_service, "_engine") and hasattr(routine_service._engine, "_execution_repository"):
                ex_repo = routine_service._engine._execution_repository
                executions = ex_repo.search({"user_id": user_id})
                sorted_ex = sorted(executions, key=lambda x: x.created_at or 0, reverse=True)
                recent_actions = [ex.action for ex in sorted_ex[:5]]
        except Exception as e:
            logger.debug(f"Failed to fetch recent executions list: {e}")

        return UserProfile(
            user_id=user_id,
            active_workspace_path=active_path,
            preferences=prefs,
            active_routines_count=routines_count,
            recent_actions=recent_actions,
        )
