"""Context builder service for aggregating information from the memory subsystem."""

import logging
from typing import Any, Dict, List, Optional
from memory.models.domain_models import MemoryEntry, AssistantContext
from memory.manager.memory_service import MemoryService
from memory.manager.memory_ranker import MemoryRanker, MemoryRankerConfig
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ContextWindowConfig(BaseModel):
    """Configuration for context windows.

    Attributes:
        short_term_limit: Limit for short-term activity/executions.
        long_term_limit: Limit for long-term conversations.
        session_limit: Limit for session conversations.
    """

    short_term_limit: int = Field(default=5, description="Limit for short-term executions")
    long_term_limit: int = Field(default=10, description="Limit for long-term conversations")
    session_limit: int = Field(default=5, description="Limit for session conversations")


class ContextBuilder:
    """Service that orchestrates the building of a unified AssistantContext.

    Aggregates recent conversations, executions, latest context state,
    preferences, and workspace context from the underlying memory service.
    """

    def __init__(
        self,
        memory_service: MemoryService,
        ranker_config: Optional[MemoryRankerConfig] = None,
        window_config: Optional[ContextWindowConfig] = None,
    ) -> None:
        """Initializes the ContextBuilder.

        Args:
            memory_service: The active MemoryService instance to query.
            ranker_config: Optional MemoryRankerConfig for ranking memories.
            window_config: Optional ContextWindowConfig for context window limits.
        """
        self.memory_service = memory_service
        self.ranker = MemoryRanker(ranker_config)
        self.window_config = window_config or ContextWindowConfig()

    async def build_context(
        self,
        user_id: int,
        session_id: Optional[str] = None,
        query_text: Optional[str] = None,
        session_only: bool = False,
    ) -> AssistantContext:
        """Aggregates memory tiers into a single AssistantContext.

        Ensures that any missing data or database exceptions result in
        empty collections or None instead of propagating exceptions.

        Args:
            user_id: The ID of the user request.
            session_id: Optional session ID to filter conversations.
            query_text: Optional current request message text.
            session_only: If True, skips loading general conversations,
                          recent executions, and preferences.

        Returns:
            An AssistantContext domain model.
        """
        # 1. Retrieve recent conversations
        recent_conversations = []
        if session_id:
            try:
                recent_conversations = await self.memory_service.get_conversations_by_session(
                    session_id, self.window_config.session_limit
                )
            except Exception as e:
                logger.warning(
                    "ContextBuilder failed to retrieve session conversations",
                    exc_info=True,
                )
        elif not session_only:
            try:
                recent_conversations = await self.memory_service.get_recent_conversations(
                    self.window_config.long_term_limit
                )
            except Exception as e:
                logger.warning(
                    "ContextBuilder failed to retrieve general conversations",
                    exc_info=True,
                )

        # 2. Retrieve recent executions
        recent_executions = []
        if not session_only:
            try:
                recent_executions = await self.memory_service.get_recent_executions(
                    self.window_config.short_term_limit
                )
            except Exception as e:
                logger.warning(
                    "ContextBuilder failed to retrieve recent executions",
                    exc_info=True,
                )

        # 3. Retrieve latest context state
        try:
            current_context = await self.memory_service.get_latest_context(user_id)
        except Exception as e:
            logger.warning(
                "ContextBuilder failed to retrieve latest context state",
                exc_info=True,
            )
            current_context = None

        # Resolve workspace_path and perform ranking
        workspace_path = None
        if current_context:
            workspace_path = current_context.metadata.additional_info.get("workspace_path") or current_context.content

        # Score and rank conversations, then apply limit
        if recent_conversations:
            try:
                recent_conversations = self.ranker.rank_memories(
                    recent_conversations,
                    query_text=query_text,
                    session_id=session_id,
                    workspace_path=workspace_path,
                )
                limit = self.window_config.session_limit if session_id else self.window_config.long_term_limit
                if self.ranker.config.max_conversations is not None:
                    limit = min(limit, self.ranker.config.max_conversations)
                recent_conversations = recent_conversations[:limit]
            except Exception:
                logger.warning("Failed to rank recent conversations", exc_info=True)
                limit = self.window_config.session_limit if session_id else self.window_config.long_term_limit
                recent_conversations = recent_conversations[:limit]

        # Score and rank executions, then apply limit
        if recent_executions:
            try:
                recent_executions = self.ranker.rank_memories(
                    recent_executions,
                    query_text=query_text,
                    session_id=session_id,
                    workspace_path=workspace_path,
                )
                limit = self.window_config.short_term_limit
                if self.ranker.config.max_executions is not None:
                    limit = min(limit, self.ranker.config.max_executions)
                recent_executions = recent_executions[:limit]
            except Exception:
                logger.warning("Failed to rank recent executions", exc_info=True)
                limit = self.window_config.short_term_limit
                recent_executions = recent_executions[:limit]

        # 4. Retrieve user preferences
        preferences = []
        if not session_only:
            try:
                preferences = await self.memory_service.get_user_preferences(user_id)
            except Exception as e:
                logger.warning(
                    "ContextBuilder failed to retrieve user preferences",
                    exc_info=True,
                )

        # 5. Retrieve workspace context (when current context path is available)
        workspace_context = None
        if current_context and current_context.content:
            try:
                workspace_context = await self.memory_service.get_workspace_context(
                    user_id, current_context.content
                )
            except Exception as e:
                logger.warning(
                    "ContextBuilder failed to retrieve workspace context profile",
                    exc_info=True,
                )
                workspace_context = None

        return AssistantContext(
            recent_conversations=recent_conversations,
            recent_executions=recent_executions,
            current_context=current_context,
            preferences=preferences,
            workspace_context=workspace_context,
            metadata={"user_id": user_id, "session_id": session_id},
        )
