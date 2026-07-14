"""User Personalization Service public interface module."""

import logging
from typing import Any, Dict, List, Optional

from memory.personalization.personalization_models import (
    UserProfile,
    PersonalizedContext,
    PersonalizationSuggestion,
)
from memory.personalization.personalization_engine import PersonalizationEngine

logger = logging.getLogger(__name__)


class PersonalizationService:
    """Sole public gateway/API for all Personalization and Profile Resolution operations in Auralis."""

    def __init__(
        self,
        preference_service: Optional[Any] = None,
        context_service: Optional[Any] = None,
        workspace_service: Optional[Any] = None,
        routine_service: Optional[Any] = None,
        engine: Optional[PersonalizationEngine] = None,
    ) -> None:
        """Initializes the PersonalizationService.

        If dependencies are not passed, resolves them dynamically from unified public namespaces.

        Args:
            preference_service: Optional custom PreferenceService.
            context_service: Optional custom ContextService.
            workspace_service: Optional custom WorkspaceService.
            routine_service: Optional custom RoutineLearningService.
            engine: Optional custom PersonalizationEngine.
        """
        if engine is not None:
            self._engine = engine
        else:
            from memory.preferences.preference_service import PreferenceService
            from memory.context.context_service import ContextService
            from memory.workspace.workspace_service import WorkspaceService
            from memory.learning.routine_learning_service import RoutineLearningService

            p_service = preference_service or PreferenceService()
            c_service = context_service or ContextService()
            w_service = workspace_service or WorkspaceService()
            r_service = routine_service or RoutineLearningService()

            self._engine = PersonalizationEngine(
                preference_service=p_service,
                context_service=c_service,
                workspace_service=w_service,
                routine_service=r_service,
            )

    def profile(self, user_id: int, session_id: str) -> UserProfile:
        """Generates a consolidated UserProfile summary.

        Args:
            user_id: Target user ID.
            session_id: Active session ID.

        Returns:
            The UserProfile.
        """
        return self._engine.generate_profile(user_id, session_id)

    def context(
        self,
        user_id: int,
        session_id: str,
        user_overrides: Optional[Dict[str, Any]] = None,
    ) -> PersonalizedContext:
        """Generates a PersonalizedContext resolving key configuration parameters.

        Args:
            user_id: Target user ID.
            session_id: Active session ID.
            user_overrides: Optional command overrides.

        Returns:
            The PersonalizedContext.
        """
        return self._engine.generate_execution_context(
            user_id=user_id,
            session_id=session_id,
            user_overrides=user_overrides,
        )

    def recommendations(self, user_id: int, session_id: str) -> List[PersonalizationSuggestion]:
        """Runs diagnostics checks and outputs suggestions.

        Args:
            user_id: Target user ID.
            session_id: Active session ID.

        Returns:
            List of suggestion options.
        """
        return self._engine.generate_recommendations(user_id, session_id)
