"""Memory-aware AI Subsystem package for Auralis (Phase 10.5).

Exports all memory models, exceptions, interfaces, retrievers, rankers, filters, and providers.
"""

from brain.ai.memory.exceptions import (
    AIMemoryException,
    MemoryFilterError,
    MemoryRankingError,
    MemoryRetrievalError,
)
from brain.ai.memory.memory_models import (
    AIMemoryItem,
    MemoryQueryResult,
    MemoryScope,
)
from brain.ai.memory.interfaces import (
    AIMemoryProviderInterface,
    MemoryFilterInterface,
    MemoryRankerInterface,
    MemoryRetrieverInterface,
)
from brain.ai.memory.memory_retriever import DefaultMemoryRetriever
from brain.ai.memory.memory_ranker import DefaultMemoryRanker, SCOPE_WEIGHTS
from brain.ai.memory.memory_filter import DefaultMemoryFilter
from brain.ai.memory.memory_provider import AIMemoryProvider

__all__ = [
    # Exceptions
    "AIMemoryException",
    "MemoryRetrievalError",
    "MemoryRankingError",
    "MemoryFilterError",
    # Models
    "MemoryScope",
    "AIMemoryItem",
    "MemoryQueryResult",
    # Interfaces
    "AIMemoryProviderInterface",
    "MemoryRetrieverInterface",
    "MemoryRankerInterface",
    "MemoryFilterInterface",
    # Concrete Implementations
    "DefaultMemoryRetriever",
    "DefaultMemoryRanker",
    "SCOPE_WEIGHTS",
    "DefaultMemoryFilter",
    "AIMemoryProvider",
]
