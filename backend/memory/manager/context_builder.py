"""Context builder service for aggregating information from the memory subsystem."""

import logging
from typing import Any, Dict, List, Optional
from memory.models.domain_models import MemoryEntry, AssistantContext
from memory.manager.memory_service import MemoryService
from memory.manager.memory_ranker import MemoryRanker, MemoryRankerConfig

logger = logging.getLogger(__name__)


class ContextBuilder:
    """Service that orchestrates the building of a unified AssistantContext.

    Aggregates recent conversations, executions, latest context state,
    preferences, and workspace context from the underlying memory service.
    """

    def __init__(
        self,
        memory_service: MemoryService,
        ranker_config: Optional[MemoryRankerConfig] = None,
    ) -> None:
        """Initializes the ContextBuilder.

        Args:
            memory_service: The active MemoryService instance to query.
            ranker_config: Optional MemoryRankerConfig for ranking memories.
        """
        self.memory_service = memory_service
        self.ranker = MemoryRanker(ranker_config)

    async def build_context(
        self,
        user_id: int,
        session_id: Optional[str] = None,
        query_text: Optional[str] = None,
        conversation_limit: int = 10,
        execution_limit: int = 5,
    ) -> AssistantContext:
        """Aggregates memory tiers into a single AssistantContext.

        Ensures that any missing data or database exceptions result in
        empty collections or None instead of propagating exceptions.

        Args:
            user_id: The ID of the user request.
            session_id: Optional session ID to filter conversations.
            query_text: Optional current request message text.
            conversation_limit: Maximum number of conversation records to retrieve.
            execution_limit: Maximum number of execution history records to retrieve.

        Returns:
            An AssistantContext domain model.
        """
        # 1. Retrieve recent conversations
        try:
            if session_id:
                recent_conversations = await self.memory_service.get_conversations_by_session(
                    session_id, conversation_limit
                )
            else:
                recent_conversations = await self.memory_service.get_recent_conversations(
                    conversation_limit
                )
        except Exception as e:
            logger.warning(
                "ContextBuilder failed to retrieve recent conversations",
                exc_info=True,
            )
            recent_conversations = []

        # 2. Retrieve recent executions
        try:
            recent_executions = await self.memory_service.get_recent_executions(
                execution_limit
            )
        except Exception as e:
            logger.warning(
                "ContextBuilder failed to retrieve recent executions",
                exc_info=True,
            )
            recent_executions = []

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
                recent_conversations = recent_conversations[:self.ranker.config.max_conversations]
            except Exception:
                logger.warning("Failed to rank recent conversations", exc_info=True)
                recent_conversations = recent_conversations[:conversation_limit]

        # Score and rank executions, then apply limit
        if recent_executions:
            try:
                recent_executions = self.ranker.rank_memories(
                    recent_executions,
                    query_text=query_text,
                    session_id=session_id,
                    workspace_path=workspace_path,
                )
                recent_executions = recent_executions[:self.ranker.config.max_executions]
            except Exception:
                logger.warning("Failed to rank recent executions", exc_info=True)
                recent_executions = recent_executions[:execution_limit]

        # 4. Retrieve user preferences
        try:
            preferences = await self.memory_service.get_user_preferences(user_id)
        except Exception as e:
            logger.warning(
                "ContextBuilder failed to retrieve user preferences",
                exc_info=True,
            )
            preferences = []

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
