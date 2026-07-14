"""Memory coordinator module.

Defines the MemoryManager which coordinates and orchestrates operations
across memory tiers, delegating direct persistence actions to repositories
and returning domain models to the service layer.
"""

import logging
from typing import List, Optional
from memory.models.domain_models import MemoryEntry, MemoryQuery, MemoryResult
from memory.repository.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class MemoryManager:
    """Coordinating manager for memory operations.

    Orchestrates business logic for memory retrieval, injection, and updates,
    delegating the low-level data storage operations to repositories.
    """

    def __init__(self, repository: BaseRepository) -> None:
        """Initializes the MemoryManager.

        Args:
            repository: An implementation of BaseRepository.
        """
        self._repository = repository
        logger.debug(
            "MemoryManager initialized with repository",
            extra={"repository_class": repository.__class__.__name__},
        )

    async def save_memory(self, entry: MemoryEntry) -> MemoryEntry:
        """Coordinates saving a memory entry.

        Args:
            entry: The MemoryEntry domain model to save.

        Returns:
            The saved MemoryEntry domain model.
        """
        logger.info(
            "MemoryManager coordinating save",
            extra={"entry_id": entry.id, "memory_type": entry.memory_type.value},
        )
        await self._repository.add(entry)
        return entry

    async def get_memory(self, entry_id: str) -> Optional[MemoryEntry]:
        """Coordinates retrieving a memory entry by ID.

        Args:
            entry_id: Unique string identifier of the memory entry.

        Returns:
            The retrieved MemoryEntry domain model if found, else None.
        """
        logger.info(
            "MemoryManager coordinating get",
            extra={"entry_id": entry_id},
        )
        return await self._repository.get_by_id(entry_id)

    async def search_memories(self, query: MemoryQuery) -> List[MemoryResult]:
        """Coordinates searching memories.

        Args:
            query: The MemoryQuery domain model parameters.

        Returns:
            A list of matching MemoryResult domain models.
        """
        logger.info(
            "MemoryManager coordinating search",
            extra={"query_text": query.text, "limit": query.limit},
        )
        return await self._repository.search(query)

    async def update_memory(self, entry_id: str, entry: MemoryEntry) -> MemoryEntry:
        """Coordinates updating an existing memory entry.

        Args:
            entry_id: Unique string identifier of the memory entry to update.
            entry: The updated MemoryEntry domain model.

        Returns:
            The updated MemoryEntry domain model.
        """
        logger.info(
            "MemoryManager coordinating update",
            extra={"entry_id": entry_id},
        )
        await self._repository.update(entry_id, entry)
        return entry

    async def delete_memory(self, entry_id: str) -> None:
        """Coordinates deleting a memory entry by ID.

        Args:
            entry_id: Unique string identifier of the memory entry.
        """
        logger.info(
            "MemoryManager coordinating delete",
            extra={"entry_id": entry_id},
        )
        await self._repository.delete(entry_id)

    async def list_memories(self, memory_type: Optional[str] = None) -> List[MemoryEntry]:
        """Coordinates listing all memory entries, optionally filtered by type.

        Args:
            memory_type: Optional memory type string to filter results.

        Returns:
            A list of matching MemoryEntry domain models.
        """
        logger.info(
            "MemoryManager coordinating list",
            extra={"memory_type": memory_type},
        )
        return await self._repository.list_all(memory_type)
