"""
Module: backend.memory.interfaces

Responsibility:
    Defines abstract contracts for the Auralis memory sub-layers.
    Enforces decoupling between memory coordinators and underlying databases.

This module SHOULD:
    - Declare abstract classes (abc.ABC) representing memory stores, semantic vector engines, and coordinators.
    - Standardize parameters and retrieval filters.
    - Support asynchronous signatures for database queries.

This module should NEVER:
    - Include specific SQLite connection calls, file writes, or vector engine client code.
    - Reference specific SQL query scripts or table variables.
    - Import database drivers (e.g. sqlite3, qdrant_client, chromadb).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from backend.memory.models import MemoryEntry, SemanticVector, UserPreference


class IMemoryStore(ABC):
    """Abstract contract for key-value or relational local persistence (e.g., SQLite)."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[MemoryEntry]:
        """Retrieves a memory entry by its key."""
        pass

    @abstractmethod
    def put(self, key: str, entry: MemoryEntry) -> None:
        """Saves or updates a memory entry."""
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """Deletes a memory entry."""
        pass


class ISemanticStorage(ABC):
    """Abstract contract for vector database engines handling semantic embeddings."""
    
    @abstractmethod
    def store_vector(self, vector: SemanticVector) -> None:
        """Stores a semantic vector and its associated metadata."""
        pass

    @abstractmethod
    def query_similarity(self, query_embeddings: List[float], limit: int) -> List[SemanticVector]:
        """Retrieves vector objects matching similarity boundaries."""
        pass


class ICacheStore(ABC):
    """Abstract contract for fast, volatile, in-memory caches."""
    
    @abstractmethod
    def get_cached(self, key: str) -> Optional[Any]:
        """Gets a cached object."""
        pass

    @abstractmethod
    def set_cached(self, key: str, value: Any, ttl_seconds: int) -> None:
        """Sets a cached object with a Time-To-Live (TTL) constraint."""
        pass

    @abstractmethod
    def invalidate(self, key: str) -> None:
        """Invalidates a cached object."""
        pass


class IMemoryManager(ABC):
    """Abstract contract for the main memory orchestrator coordinating tiers."""
    
    @abstractmethod
    def get_active_context(self, session_id: str, query: str) -> Dict[str, Any]:
        """Assembles a compiled context map for a given user query."""
        pass

    @abstractmethod
    def commit_interaction(self, session_id: str, prompt: str, response: str) -> None:
        """Commits a conversation turn to short-term, long-term, and preference systems."""
        pass
