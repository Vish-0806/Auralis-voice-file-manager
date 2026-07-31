"""Strongly typed Pydantic data models for Memory-aware AI (Phase 10.5).

Defines MemoryScope, AIMemoryItem, and MemoryQueryResult models.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


class MemoryScope(str, Enum):
    """Supported memory scopes in the Auralis memory integration layer."""

    SESSION = "session"
    RECENT = "recent"
    LONG_TERM = "long_term"
    PINNED = "pinned"


class AIMemoryItem(BaseModel):
    """Immutable model representing an individual memory item snapshot."""

    model_config = ConfigDict(frozen=True)

    memory_id: str
    key: str
    content: str
    scope: MemoryScope = MemoryScope.RECENT
    importance_score: float = 0.5
    relevance_score: float = 0.0
    recency_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MemoryQueryResult(BaseModel):
    """Result model containing retrieved, ranked, and filtered memory items."""

    model_config = ConfigDict(frozen=True)

    query: str = ""
    items: List[AIMemoryItem] = Field(default_factory=list)
    total_found: int = 0
    token_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)
