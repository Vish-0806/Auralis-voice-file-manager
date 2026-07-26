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
        short_term_limit: [DEPRECATED] Limit for short-term executions. Use maximum_execution_history instead.
        long_term_limit: [DEPRECATED] Limit for long-term conversations. Use maximum_conversations instead.
        session_limit: [DEPRECATED] Limit for session conversations. Use maximum_conversations instead.
        token_budget: Total token limit for the context window.
        reserved_response_tokens: Reserved tokens for model reply generation.
        safety_margin_tokens: Safety margin buffer tokens.
        maximum_conversations: Absolute upper limit on conversations.
        maximum_execution_history: Absolute upper limit on executions.
        maximum_preferences: Absolute upper limit on preferences.
        maximum_contexts: Absolute upper limit on session contexts.
        maximum_workspace_entries: Absolute upper limit on workspace context entries.
        maximum_memory_events: Absolute upper limit on general memory events.
        truncation_strategy: Strategy for trimming context when budget is exceeded.
        prioritization_strategy: Strategy for prioritizing elements.
        minimum_recent_conversations: Minimum recent conversation turns to protect from pruning.
    """

    # DEPRECATED fields preserved for backward compatibility
    short_term_limit: int = Field(default=5, description="[DEPRECATED: Use maximum_execution_history instead] Limit for short-term executions")
    long_term_limit: int = Field(default=10, description="[DEPRECATED: Use maximum_conversations instead] Limit for long-term conversations")
    session_limit: int = Field(default=5, description="[DEPRECATED: Use maximum_conversations instead] Limit for session conversations")

    # Production context window parameters
    token_budget: int = Field(default=4096, description="Total token limit for the context window")
    reserved_response_tokens: int = Field(default=1024, description="Reserved tokens for model reply generation")
    safety_margin_tokens: int = Field(default=256, description="Safety margin buffer tokens")

    maximum_conversations: int = Field(default=10, description="Absolute upper limit on conversations")
    maximum_execution_history: int = Field(default=5, description="Absolute upper limit on executions")
    maximum_preferences: int = Field(default=20, description="Absolute upper limit on preferences")
    maximum_contexts: int = Field(default=1, description="Absolute upper limit on session contexts")
    maximum_workspace_entries: int = Field(default=2, description="Absolute upper limit on workspace context entries")
    maximum_memory_events: int = Field(default=10, description="Absolute upper limit on general memory events")

    truncation_strategy: str = Field(default="drop_lowest_ranked", description="Strategy for trimming context")
    prioritization_strategy: str = Field(default="priority_order", description="Strategy for prioritizing elements")
    minimum_recent_conversations: int = Field(default=2, description="Minimum recent conversation turns to protect from pruning")


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
        window_manager: Optional[Any] = None,
        coordinator: Optional[Any] = None,
    ) -> None:
        """Initializes the ContextBuilder.

        Args:
            memory_service: The active MemoryService instance to query.
            ranker_config: Optional MemoryRankerConfig for ranking memories.
            window_config: Optional ContextWindowConfig for context window limits.
            window_manager: Optional custom ContextWindowManager instance.
            coordinator: Optional custom WorkspaceIntelligenceCoordinator instance.
        """
        self.memory_service = memory_service
        self.ranker = MemoryRanker(ranker_config)
        self.window_config = window_config or ContextWindowConfig()

        # Backward compatibility overrides from MemoryRankerConfig
        ranker_max_conv = self.ranker.config.max_conversations
        if ranker_max_conv is not None:
            self.window_config.maximum_conversations = min(self.window_config.maximum_conversations, ranker_max_conv)

        ranker_max_exec = self.ranker.config.max_executions
        if ranker_max_exec is not None:
            self.window_config.maximum_execution_history = min(self.window_config.maximum_execution_history, ranker_max_exec)

        # Local import to prevent circular dependencies
        from memory.manager.context_window_manager import ContextWindowManager
        self.window_manager = window_manager or ContextWindowManager(self.window_config)

        # Initialize Workspace Intelligence Coordinator
        from memory.workspace.workspace_coordinator import WorkspaceIntelligenceCoordinator
        self.coordinator = coordinator or WorkspaceIntelligenceCoordinator()

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

        # Score and rank conversations
        if recent_conversations:
            try:
                recent_conversations = self.ranker.rank_memories(
                    recent_conversations,
                    query_text=query_text,
                    session_id=session_id,
                    workspace_path=workspace_path,
                )
            except Exception:
                logger.warning("Failed to rank recent conversations", exc_info=True)

        # Score and rank executions
        if recent_executions:
            try:
                recent_executions = self.ranker.rank_memories(
                    recent_executions,
                    query_text=query_text,
                    session_id=session_id,
                    workspace_path=workspace_path,
                )
            except Exception:
                logger.warning("Failed to rank recent executions", exc_info=True)

        # 4. Retrieve user preferences
        preferences = []
        resolved_preferences = {}
        if not session_only:
            logger.info("Loading User Preferences")
            try:
                preferences = await self.memory_service.get_user_preferences(user_id)
            except Exception as e:
                logger.warning(
                    "ContextBuilder failed to retrieve user preferences",
                    exc_info=True,
                )
            try:
                resolved_preferences = await self.memory_service.get_resolved_preferences(user_id)
            except Exception as e:
                logger.warning(
                    "ContextBuilder failed to retrieve resolved preferences",
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

        # Workspace Intelligence Integration
        workspace_analysis = None
        if workspace_path:
            try:
                workspace_analysis = await self.coordinator.analyze(workspace_path)
            except Exception as e:
                logger.warning(
                    f"Workspace Intelligence scan failed for path: {workspace_path}",
                    exc_info=True,
                )

        # Assemble the raw aggregated context
        raw_context = AssistantContext(
            recent_conversations=recent_conversations,
            recent_executions=recent_executions,
            current_context=current_context,
            preferences=preferences,
            workspace_context=workspace_context,
            workspace_analysis=workspace_analysis,
            resolved_preferences=resolved_preferences,
            metadata={"user_id": user_id, "session_id": session_id},
        )

        # Optimize context window before passing to AI Brain (single authority)
        optimized_context = self.window_manager.optimize_context_window(
            raw_context, query_text=query_text
        )
        return optimized_context
