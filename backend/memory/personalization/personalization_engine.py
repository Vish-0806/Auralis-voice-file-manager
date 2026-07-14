"""Personalization Engine coordinator."""

import logging
from typing import Any, Dict, List, Optional

from memory.personalization.personalization_models import (
    UserProfile,
    PersonalizedContext,
    PersonalizationSuggestion,
)
from memory.personalization.personalization_validator import PersonalizationValidator
from memory.personalization.profile_builder import ProfileBuilder
from memory.personalization.decision_engine import DecisionEngine
from memory.personalization.recommendation_engine import RecommendationEngine

logger = logging.getLogger(__name__)


class PersonalizationEngine:
    """Orchestrates profile summaries, deterministic priority conflict resolution, and recommendation prompts."""

    def __init__(
        self,
        preference_service: Any,
        context_service: Any,
        workspace_service: Any,
        routine_service: Any,
        validator: Optional[PersonalizationValidator] = None,
        builder: Optional[ProfileBuilder] = None,
        decider: Optional[DecisionEngine] = None,
        recommender: Optional[RecommendationEngine] = None,
    ) -> None:
        """Initializes PersonalizationEngine with dependencies.

        Args:
            preference_service: Consolidated PreferenceService.
            context_service: Consolidated ContextService.
            workspace_service: Consolidated WorkspaceService.
            routine_service: Consolidated RoutineLearningService.
            validator: Validator logic.
            builder: Profile aggregator logic.
            decider: Settings resolver logic.
            recommender: Recommendation analyzer logic.
        """
        self._preference_service = preference_service
        self._context_service = context_service
        self._workspace_service = workspace_service
        self._routine_service = routine_service

        self._validator = validator or PersonalizationValidator()
        self._builder = builder or ProfileBuilder()
        self._decider = decider or DecisionEngine()
        self._recommender = recommender or RecommendationEngine()

    def generate_profile(self, user_id: int, session_id: str) -> UserProfile:
        """Combines memory states into a unified UserProfile summary object.

        Args:
            user_id: Target user ID.
            session_id: Active session ID.

        Returns:
            The UserProfile.
        """
        self._validator.validate_inputs(user_id, session_id)
        return self._builder.build(
            user_id=user_id,
            session_id=session_id,
            preference_service=self._preference_service,
            context_service=self._context_service,
            routine_service=self._routine_service,
        )

    def generate_execution_context(
        self,
        user_id: int,
        session_id: str,
        user_overrides: Optional[Dict[str, Any]] = None,
    ) -> PersonalizedContext:
        """Resolves setting key conflicts dynamically and returns a PersonalizedContext.

        Args:
            user_id: Target user ID.
            session_id: Active session ID.
            user_overrides: Optional overrides dict.

        Returns:
            Resolved PersonalizedContext containing settings mappings.
        """
        self._validator.validate_inputs(user_id, session_id)

        # 1. Fetch current context
        context = self._context_service.load(user_id, session_id)

        # 2. Fetch preferences
        preferences = {}
        for category in ["ide", "voice", "desktop", "system"]:
            try:
                preferences[category] = self._preference_service.get(user_id, category)
            except Exception:
                pass

        # 3. Fetch learned routines
        learned_routines = []
        try:
            learned_routines = self._routine_service.list(user_id)
        except Exception:
            pass

        # 4. Fetch active workspace profile settings
        workspace_settings = {}
        try:
            active_path = context.get("active_workspace") or context.get("current_project")
            if active_path:
                workspaces = self._workspace_service.list(user_id)
                active_ws = next((w for w in workspaces if w.path == active_path), None)
                if active_ws:
                    workspace_settings = active_ws.settings
        except Exception:
            pass

        # 5. Resolve conflicts
        return self._decider.generate_context(
            user_id=user_id,
            session_id=session_id,
            user_overrides=user_overrides,
            context=context,
            workspace_settings=workspace_settings,
            preferences=preferences,
            learned_routines=learned_routines,
        )

    def generate_recommendations(self, user_id: int, session_id: str) -> List[PersonalizationSuggestion]:
        """Runs the recommendation engine based on current consolidated user metrics.

        Args:
            user_id: Target user ID.
            session_id: Active session ID.

        Returns:
            List of suggestion options.
        """
        self._validator.validate_inputs(user_id, session_id)

        context = self._context_service.load(user_id, session_id)

        preferences = {}
        for category in ["ide", "voice", "desktop", "system"]:
            try:
                preferences[category] = self._preference_service.get(user_id, category)
            except Exception:
                pass

        learned_routines = []
        try:
            learned_routines = self._routine_service.list(user_id)
        except Exception:
            pass

        workspaces = []
        try:
            workspaces = self._workspace_service.list(user_id)
        except Exception:
            pass

        return self._recommender.generate(
            user_id=user_id,
            session_id=session_id,
            context=context,
            preferences=preferences,
            learned_routines=learned_routines,
            workspaces=workspaces,
        )
