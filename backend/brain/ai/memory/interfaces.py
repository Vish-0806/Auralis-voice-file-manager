"""Abstract interfaces for Memory-aware AI (Phase 10.5).

Defines ABCs for:
- AIMemoryProviderInterface
- MemoryRetrieverInterface
- MemoryRankerInterface
- MemoryFilterInterface
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from brain.ai.ai_models import AIContext
from brain.ai.memory.memory_models import AIMemoryItem, MemoryQueryResult, MemoryScope


class AIMemoryProviderInterface(ABC):
    """Abstract interface for accessing underlying memory subsystem items without storage duplication."""

    @abstractmethod
    def fetch_memories(
        self,
        context: AIContext,
        scopes: Optional[List[MemoryScope]] = None,
    ) -> List[AIMemoryItem]:
        """Fetch raw AIMemoryItem objects from memory context or backing storage."""
        pass

    @abstractmethod
    def query_memories(
        self,
        context: AIContext,
        query: str,
        max_results: int = 10,
    ) -> MemoryQueryResult:
        """Query, rank, filter, and return structured MemoryQueryResult for AI prompt ingestion."""
        pass


class MemoryRetrieverInterface(ABC):
    """Abstract interface for scope-aware memory retrieval."""

    @abstractmethod
    def retrieve(
        self,
        context: AIContext,
        scopes: Optional[List[MemoryScope]] = None,
    ) -> List[AIMemoryItem]:
        """Retrieve memory items across specified memory scopes (session, recent, long_term, pinned)."""
        pass


class MemoryRankerInterface(ABC):
    """Abstract interface for scoring and ranking memory items."""

    @abstractmethod
    def rank(
        self,
        items: List[AIMemoryItem],
        query: str = "",
    ) -> List[AIMemoryItem]:
        """Score and sort memory items in descending order of calculated relevance."""
        pass


class MemoryFilterInterface(ABC):
    """Abstract interface for deduplicating and budgeting memory items."""

    @abstractmethod
    def filter_and_budget(
        self,
        items: List[AIMemoryItem],
        max_tokens: Optional[int] = None,
        deduplicate: bool = True,
    ) -> List[AIMemoryItem]:
        """Deduplicate items and trim to stay within token budget while preserving rank order."""
        pass
