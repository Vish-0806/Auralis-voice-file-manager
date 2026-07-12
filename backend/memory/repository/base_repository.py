"""Repository contracts interface module.

Declares the BaseRepository abstract contract to decouple database storage operations
from high-level memory domain orchestration.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from memory.models.domain_models import MemoryEntry, MemoryQuery, MemoryResult


class BaseRepository(ABC):
    """Abstract contract defining the memory repository pattern."""

    @abstractmethod
    async def add(self, entry: MemoryEntry) -> None:
        """Add a memory entry to the repository.

        Args:
            entry: The MemoryEntry domain model.

        Raises:
            Exception: If storage operation fails.
        """
        pass

    @abstractmethod
    async def get_by_id(self, entry_id: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry by its unique ID.

        Args:
            entry_id: Unique string identifier.

        Returns:
            The MemoryEntry domain model if found, else None.

        Raises:
            Exception: If retrieval operation fails.
        """
        pass

    @abstractmethod
    async def search(self, query: MemoryQuery) -> List[MemoryResult]:
        """Search memory entries based on similarity or metadata filters.

        Args:
            query: The MemoryQuery domain model parameters.

        Returns:
            A list of MemoryResult domain models.

        Raises:
            Exception: If search query fails.
        """
        pass

    @abstractmethod
    async def update(self, entry_id: str, entry: MemoryEntry) -> None:
        """Update an existing memory entry in the repository.

        Args:
            entry_id: Unique string identifier of the memory entry to update.
            entry: The updated MemoryEntry domain model.

        Raises:
            KeyError: If entry does not exist.
            Exception: If update operation fails.
        """
        pass

    @abstractmethod
    async def delete(self, entry_id: str) -> None:
        """Delete a memory entry from the repository by its ID.

        Args:
            entry_id: Unique string identifier of the memory entry.

        Raises:
            Exception: If deletion fails.
        """
        pass

    @abstractmethod
    async def list_all(self, memory_type: Optional[str] = None) -> List[MemoryEntry]:
        """List all memory entries, optionally filtered by memory type.

        Args:
            memory_type: Optional memory type string to filter results.

        Returns:
            A list of MemoryEntry domain models.

        Raises:
            Exception: If listing operation fails.
        """
        pass
