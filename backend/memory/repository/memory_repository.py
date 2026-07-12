"""MemoryRepository implementation module.

Implements the BaseRepository contract by delegating operations to the active BaseProvider,
ready for a PostgreSQL or other database provider implementation in the future.
"""

import logging
from typing import List, Optional
from memory.models.domain_models import MemoryEntry, MemoryQuery, MemoryResult
from memory.providers.base_provider import BaseProvider
from memory.repository.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class MemoryRepository(BaseRepository):
    """Repository implementation that delegates operations to a storage provider.

    This serves as the main abstraction layer for data access, decoupling
    the repository interface from the specific database client/connection.
    """

    def __init__(self, provider: BaseProvider) -> None:
        """Initializes the MemoryRepository.

        Args:
            provider: The storage provider instance to delegate operations to.
        """
        self._provider = provider
        logger.debug(
            "MemoryRepository initialized with provider",
            extra={"provider_class": provider.__class__.__name__},
        )

    async def add(self, entry: MemoryEntry) -> None:
        """Adds a memory entry via the storage provider.

        Args:
            entry: The MemoryEntry domain model.
        """
        logger.info(
            "Repository adding memory entry",
            extra={"entry_id": entry.id, "memory_type": entry.memory_type.value},
        )
        await self._provider.save(entry)

    async def get_by_id(self, entry_id: str) -> Optional[MemoryEntry]:
        """Retrieves a memory entry by ID via the storage provider.

        Args:
            entry_id: Unique string identifier.

        Returns:
            The MemoryEntry domain model if found, else None.
        """
        logger.info(
            "Repository retrieving memory entry",
            extra={"entry_id": entry_id},
        )
        return await self._provider.get(entry_id)

    async def search(self, query: MemoryQuery) -> List[MemoryResult]:
        """Searches memory entries via the storage provider.

        Args:
            query: The MemoryQuery domain model parameters.

        Returns:
            A list of MemoryResult domain models.
        """
        logger.info(
            "Repository searching memories",
            extra={
                "query_text": query.text,
                "memory_type": query.memory_type.value if query.memory_type else None,
                "limit": query.limit,
            },
        )
        return await self._provider.search(query)

    async def update(self, entry_id: str, entry: MemoryEntry) -> None:
        """Updates a memory entry via the storage provider.

        Args:
            entry_id: Unique string identifier of the memory entry to update.
            entry: The updated MemoryEntry domain model.
        """
        logger.info(
            "Repository updating memory entry",
            extra={"entry_id": entry_id, "memory_type": entry.memory_type.value},
        )
        await self._provider.update(entry_id, entry)

    async def delete(self, entry_id: str) -> None:
        """Deletes a memory entry via the storage provider.

        Args:
            entry_id: Unique string identifier of the memory entry.
        """
        logger.info(
            "Repository deleting memory entry",
            extra={"entry_id": entry_id},
        )
        await self._provider.delete(entry_id)

    async def list_all(self, memory_type: Optional[str] = None) -> List[MemoryEntry]:
        """Lists all memory entries via the storage provider, optionally filtered by type.

        Args:
            memory_type: Optional memory type string to filter results.

        Returns:
            A list of MemoryEntry domain models.
        """
        logger.info(
            "Repository listing memory entries",
            extra={"memory_type": memory_type},
        )
        return await self._provider.list_entries(memory_type)
