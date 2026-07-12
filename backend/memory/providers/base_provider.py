"""Abstract base provider and default in-memory provider.

Declares the storage provider contract for memory persistence layers
and implements a transient, in-memory provider for testing and bootstrapping.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import List, Optional
from memory.models.domain_models import MemoryEntry, MemoryQuery, MemoryResult


class BaseProvider(ABC):
    """Abstract storage provider interface for memory persistence layers."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initializes the storage provider client or connection.

        Raises:
            Exception: If initialization fails.
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Closes any open storage provider connections.

        Raises:
            Exception: If closing fails.
        """
        pass

    @abstractmethod
    async def save(self, entry: MemoryEntry) -> None:
        """Saves a memory entry.

        Args:
            entry: The MemoryEntry domain model to persist.

        Raises:
            Exception: If storage operation fails.
        """
        pass

    @abstractmethod
    async def get(self, entry_id: str) -> Optional[MemoryEntry]:
        """Retrieves a memory entry by its unique ID.

        Args:
            entry_id: The unique string identifier.

        Returns:
            The MemoryEntry domain model if found, else None.

        Raises:
            Exception: If retrieval operation fails.
        """
        pass

    @abstractmethod
    async def search(self, query: MemoryQuery) -> List[MemoryResult]:
        """Searches memory entries using similarity or metadata filters.

        Args:
            query: The MemoryQuery domain model.

        Returns:
            A list of matching MemoryResult domain models.

        Raises:
            Exception: If query operation fails.
        """
        pass

    @abstractmethod
    async def update(self, entry_id: str, entry: MemoryEntry) -> None:
        """Updates an existing memory entry.

        Args:
            entry_id: Unique string identifier of the memory.
            entry: The updated MemoryEntry domain model.

        Raises:
            KeyError: If entry does not exist.
            Exception: If update operation fails.
        """
        pass

    @abstractmethod
    async def delete(self, entry_id: str) -> None:
        """Deletes a memory entry by ID.

        Args:
            entry_id: Unique string identifier.

        Raises:
            Exception: If deletion operation fails.
        """
        pass

    @abstractmethod
    async def list_entries(self, memory_type: Optional[str] = None) -> List[MemoryEntry]:
        """Lists all memory entries, optionally filtered by type.

        Args:
            memory_type: Optional memory type string to filter results.

        Returns:
            A list of matching MemoryEntry domain models.

        Raises:
            Exception: If listing operation fails.
        """
        pass


class InMemoryProvider(BaseProvider):
    """A transient, thread-safe, in-memory storage provider for testing and bootstrapping.

    Stores all entries in memory; data is lost when the application terminates.
    """

    def __init__(self) -> None:
        """Initializes the InMemoryProvider with an empty store and a lock."""
        self._store: dict[str, MemoryEntry] = {}
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """No-op initialization for in-memory store."""
        pass

    async def close(self) -> None:
        """No-op cleanup for in-memory store."""
        pass

    async def save(self, entry: MemoryEntry) -> None:
        """Saves a memory entry to the transient dictionary.

        Args:
            entry: The MemoryEntry domain model to save.
        """
        async with self._lock:
            self._store[entry.id] = entry.model_copy(deep=True)

    async def get(self, entry_id: str) -> Optional[MemoryEntry]:
        """Retrieves a memory entry by ID.

        Args:
            entry_id: The ID of the memory entry to retrieve.

        Returns:
            The MemoryEntry if found, else None.
        """
        async with self._lock:
            entry = self._store.get(entry_id)
            if entry:
                return entry.model_copy(deep=True)
            return None

    async def search(self, query: MemoryQuery) -> List[MemoryResult]:
        """Searches memories based on memory type and simple keyword inclusion.

        Args:
            query: The search query parameters.

        Returns:
            A list of search results sorted by match score.
        """
        async with self._lock:
            results = []
            for entry in self._store.values():
                # Filter by memory type if specified
                if query.memory_type and entry.memory_type != query.memory_type:
                    continue

                # Filter by query text if specified
                score = 1.0
                if query.text:
                    if query.text.lower() in entry.content.lower():
                        score = 1.0
                    else:
                        score = 0.0

                # Filter by metadata fields if specified
                if query.filters:
                    matches_filters = True
                    for k, v in query.filters.items():
                        # Check additional_info first, then fallback to metadata attributes
                        info = entry.metadata.additional_info
                        if info.get(k) != v and getattr(entry.metadata, k, None) != v:
                            matches_filters = False
                            break
                    if not matches_filters:
                        score = 0.0

                if score > 0.0:
                    results.append(
                        MemoryResult(
                            entry=entry.model_copy(deep=True),
                            score=score
                        )
                    )

            # Sort results by score (descending)
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:query.limit]

    async def update(self, entry_id: str, entry: MemoryEntry) -> None:
        """Updates a memory entry in the transient dictionary.

        Args:
            entry_id: The ID of the memory entry to update.
            entry: The updated MemoryEntry domain model.

        Raises:
            KeyError: If the memory entry is not found.
        """
        async with self._lock:
            if entry_id not in self._store:
                raise KeyError(f"Memory entry with ID {entry_id} not found in in-memory store.")
            self._store[entry_id] = entry.model_copy(deep=True)

    async def delete(self, entry_id: str) -> None:
        """Deletes a memory entry from the transient dictionary.

        Args:
            entry_id: The ID of the memory entry to delete.
        """
        async with self._lock:
            if entry_id in self._store:
                del self._store[entry_id]

    async def list_entries(self, memory_type: Optional[str] = None) -> List[MemoryEntry]:
        """Lists all memory entries, optionally filtered by type.

        Args:
            memory_type: Optional memory type string to filter results.

        Returns:
            A list of matching MemoryEntry domain models.
        """
        async with self._lock:
            entries = []
            for entry in self._store.values():
                if memory_type and entry.memory_type.value != memory_type:
                    continue
                entries.append(entry.model_copy(deep=True))
            return entries
