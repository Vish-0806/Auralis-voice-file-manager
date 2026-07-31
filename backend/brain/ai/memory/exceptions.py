"""Memory-aware AI Subsystem Exception Hierarchy for Auralis (Phase 10.5).

Defines exception types for memory retrieval, ranking, filtering, and provider abstractions.
"""

from brain.ai.exceptions import AIException


class AIMemoryException(AIException):
    """Base exception for all AI memory subsystem errors in Auralis."""

    pass


class MemoryRetrievalError(AIMemoryException):
    """Raised when memory retrieval fails across memory scopes."""

    pass


class MemoryRankingError(AIMemoryException):
    """Raised when scoring or ranking memory items encounters an error."""

    pass


class MemoryFilterError(AIMemoryException):
    """Raised when filtering or token budgeting memory items fails."""

    pass
