"""Memory Pipeline for generating unified personalized contexts."""

import logging
from typing import Any, Dict, Optional
from memory.personalization.personalization_models import PersonalizedContext

logger = logging.getLogger(__name__)


class MemoryPipeline:
    """Consolidates preferences, contexts, workspaces, and routines into a PersonalizedContext."""

    def __init__(self, personalization_service: Any) -> None:
        """Initializes the MemoryPipeline.

        Args:
            personalization_service: Injected PersonalizationService instance.
        """
        self._personalization_service = personalization_service

    def process(
        self,
        user_id: int,
        session_id: str,
        user_overrides: Optional[Dict[str, Any]] = None,
    ) -> PersonalizedContext:
        """Loads memory layers sequentially and runs conflict resolution to produce resolved contexts.

        Args:
            user_id: Target user ID.
            session_id: Active session ID.
            user_overrides: Command overrides.

        Returns:
            Resolved PersonalizedContext object.
        """
        logger.info(f"Running MemoryPipeline for user {user_id} (session: {session_id}).")
        return self._personalization_service.context(
            user_id=user_id,
            session_id=session_id,
            user_overrides=user_overrides,
        )
