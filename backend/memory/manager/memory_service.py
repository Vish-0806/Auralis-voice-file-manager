"""Memory Service public interface module.

Defines the MemoryService, which acts as the sole public gateway/API for all
subsystems interacting with Auralis memory (e.g., the AI Brain).
"""

import logging
from typing import Any, List, Optional
from memory.models.domain_models import MemoryEntry, MemoryQuery, MemoryResult
from memory.manager.memory_manager import MemoryManager
from memory.repository.memory_repository import MemoryRepository
from memory.providers.provider_factory import ProviderFactory

logger = logging.getLogger(__name__)


class MemoryService:
    """Public API service layer for the Auralis memory subsystem.

    This service exposes standard CRUD and search operations, coordinating behind
    the scenes via the MemoryManager, repository and resolved storage provider.
    """

    def __init__(self, manager: Optional[MemoryManager] = None) -> None:
        """Initializes the MemoryService.

        If a custom MemoryManager is injected, it will be utilized. Otherwise,
        resolves the configured storage provider via ProviderFactory, wraps it in
        a MemoryRepository, and initializes a new MemoryManager instance.

        Args:
            manager: Optional custom MemoryManager instance.
        """
        if manager is not None:
            self._manager = manager
            logger.info("MemoryService initialized with injected manager.")
        else:
            try:
                provider = ProviderFactory.get_provider()
                repository = MemoryRepository(provider)
                self._manager = MemoryManager(repository)
                logger.info(
                    "MemoryService initialized with resolved default provider",
                    extra={"provider_name": provider.__class__.__name__},
                )
            except Exception as e:
                logger.critical(
                    "MemoryService failed to resolve default provider",
                    exc_info=True,
                )
                raise e

    async def save(self, entry: MemoryEntry) -> MemoryEntry:
        """Saves a memory entry.

        Args:
            entry: The MemoryEntry domain model to save.

        Returns:
            The saved MemoryEntry domain model.
        """
        logger.info(
            "MemoryService saving memory entry",
            extra={"entry_id": entry.id, "memory_type": entry.memory_type.value},
        )
        return await self._manager.save_memory(entry)

    async def get(self, entry_id: str) -> Optional[MemoryEntry]:
        """Retrieves a memory entry by ID.

        Args:
            entry_id: The ID of the memory entry to retrieve.

        Returns:
            The retrieved MemoryEntry domain model, or None if not found.
        """
        logger.info(
            "MemoryService retrieving memory entry",
            extra={"entry_id": entry_id},
        )
        return await self._manager.get_memory(entry_id)

    async def search(self, query: MemoryQuery) -> List[MemoryResult]:
        """Searches memory entries matching query parameters.

        Args:
            query: The MemoryQuery domain model parameters.

        Returns:
            A list of search results.
        """
        logger.info(
            "MemoryService searching memories",
            extra={"query_text": query.text, "limit": query.limit},
        )
        return await self._manager.search_memories(query)

    async def update(self, entry_id: str, entry: MemoryEntry) -> MemoryEntry:
        """Updates an existing memory entry.

        Args:
            entry_id: Unique identifier of the memory entry.
            entry: The updated MemoryEntry domain model.

        Returns:
            The updated MemoryEntry domain model.
        """
        logger.info(
            "MemoryService updating memory entry",
            extra={"entry_id": entry_id, "memory_type": entry.memory_type.value},
        )
        return await self._manager.update_memory(entry_id, entry)

    async def delete(self, entry_id: str) -> None:
        """Deletes a memory entry.

        Args:
            entry_id: The unique identifier of the memory entry to delete.
        """
        logger.info(
            "MemoryService deleting memory entry",
            extra={"entry_id": entry_id},
        )
        await self._manager.delete_memory(entry_id)

    async def list(self, memory_type: Optional[str] = None) -> List[MemoryEntry]:
        """Lists all memory entries, optionally filtered by type.

        Args:
            memory_type: Optional memory type string to filter results.

        Returns:
            A list of matching MemoryEntry domain models.
        """
        logger.info(
            "MemoryService listing memories",
            extra={"memory_type": memory_type},
        )
        return await self._manager.list_memories(memory_type)

    async def get_recent_conversations(self, limit: int) -> List[MemoryEntry]:
        return await self._manager.get_recent_conversations(limit)

    async def get_conversations_by_session(self, session_id: str, limit: int) -> List[MemoryEntry]:
        return await self._manager.get_conversations_by_session(session_id, limit)

    async def get_conversations_by_user(self, user_id: int, limit: int) -> List[MemoryEntry]:
        return await self._manager.get_conversations_by_user(user_id, limit)

    async def get_recent_executions(self, limit: int) -> List[MemoryEntry]:
        return await self._manager.get_recent_executions(limit)

    async def get_failed_executions(self, limit: int) -> List[MemoryEntry]:
        return await self._manager.get_failed_executions(limit)

    async def get_successful_executions(self, limit: int) -> List[MemoryEntry]:
        return await self._manager.get_successful_executions(limit)

    async def get_latest_context(self, user_id: int) -> Optional[MemoryEntry]:
        return await self._manager.get_latest_context(user_id)

    async def get_context_by_session(self, session_id: str) -> Optional[MemoryEntry]:
        return await self._manager.get_context_by_session(session_id)

    async def get_preference_by_key(self, user_id: int, key: str) -> Optional[MemoryEntry]:
        return await self._manager.get_preference_by_key(user_id, key)

    async def get_recent_events(self, limit: int) -> List[MemoryEntry]:
        return await self._manager.get_recent_events(limit)

    async def get_workspace_context(self, user_id: int, path: str) -> Optional[MemoryEntry]:
        return await self._manager.get_workspace_context(user_id, path)

    async def get_user_preferences(self, user_id: int) -> List[MemoryEntry]:
        return await self._manager.get_user_preferences(user_id)

    async def get_resolved_preferences(self, user_id: int) -> dict:
        return await self._manager.get_resolved_preferences(user_id)

    async def save_resolved_preference(self, resolved_pref: Any) -> None:
        await self._manager.save_resolved_preference(resolved_pref)

    async def get_preference_observations(self, user_id: int, limit: int = 100) -> list:
        return await self._manager.get_preference_observations(user_id, limit)

    async def save_workflow_observation(self, observation: Any) -> None:
        """Saves a workflow observation."""
        await self._manager.save_workflow_observation(observation)

    async def get_workflow_observations(self, user_id: int) -> list:
        """Retrieves all workflow observations for a user."""
        return await self._manager.get_workflow_observations(user_id)

    async def get_workflow_sequences(self, user_id: int) -> list:
        """Retrieves all distinct workflow sequences observed for a user."""
        return await self._manager.get_workflow_sequences(user_id)

    async def record_recommendation_feedback(self, user_id: int, workflow_id: str, feedback_status: str) -> None:
        """Records user feedback (accepted, rejected, ignored) for a recommended workflow."""
        from memory.models.domain_models import MemoryEntry, MemoryType, MemoryMetadata
        from datetime import datetime, timezone
        import uuid
        entry = MemoryEntry(
            id=f"rec_fb_{workflow_id}_{user_id}_{uuid.uuid4().hex[:8]}",
            content=feedback_status,
            memory_type=MemoryType.PREFERENCE,
            metadata=MemoryMetadata(
                additional_info={
                    "user_id": user_id,
                    "workflow_id": workflow_id,
                    "type": "recommendation_feedback",
                    "status": feedback_status,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        )
        await self.save(entry)

    async def record_recommendation_acceptance(self, user_id: int, workflow_id: str) -> None:
        """Records that a workflow recommendation was accepted by the user."""
        await self.record_recommendation_feedback(user_id, workflow_id, "accepted")

    async def record_recommendation_rejection(self, user_id: int, workflow_id: str) -> None:
        """Records that a workflow recommendation was rejected by the user."""
        await self.record_recommendation_feedback(user_id, workflow_id, "rejected")

    async def record_recommendation_ignored(self, user_id: int, workflow_id: str) -> None:
        """Records that a workflow recommendation was ignored by the user."""
        await self.record_recommendation_feedback(user_id, workflow_id, "ignored")
