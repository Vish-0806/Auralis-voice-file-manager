"""Domain models for the Auralis memory subsystem.

This module defines independent data structures representing memories, queries,
results, and metadata, decoupled from any persistence or ORM layers.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    """Enumeration of standard memory types supported by Auralis."""

    SESSION = "session"
    CONVERSATION = "conversation"
    PREFERENCE = "preference"
    ACTIVITY = "activity"
    WORKFLOW = "workflow"
    PROJECT = "project"
    FILE = "file"
    LONG_TERM = "long_term"


class MemoryMetadata(BaseModel):
    """Metadata container for a memory entry.

    Attributes:
        created_at: Timestamp when the memory was initially created.
        updated_at: Timestamp when the memory was last updated.
        tags: List of descriptive tags for semantic categorization.
        source: Optional identifier for the origin of the memory.
        additional_info: Key-value dictionary for custom attributes.
    """

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tags: List[str] = Field(default_factory=list)
    source: Optional[str] = None
    additional_info: Dict[str, Any] = Field(default_factory=dict)


class MemoryEntry(BaseModel):
    """Domain model representing a single memory unit.

    Attributes:
        id: Unique identifier for the memory entry.
        content: Text content of the memory.
        memory_type: The category type of this memory.
        metadata: Associated metadata including creation and custom fields.
        embedding: Optional vector representation of the memory content.
    """

    id: str
    content: str
    memory_type: MemoryType
    metadata: MemoryMetadata = Field(default_factory=MemoryMetadata)
    embedding: Optional[List[float]] = None


class MemoryQuery(BaseModel):
    """Domain model representing a query to search or retrieve memories.

    Attributes:
        text: Query text to match against memory content.
        memory_type: Optional memory type filter.
        limit: Maximum number of search results to return.
        threshold: Optional minimum similarity threshold for results.
        filters: Optional key-value metadata filters.
    """

    text: str
    memory_type: Optional[MemoryType] = None
    limit: int = 10
    threshold: Optional[float] = None
    filters: Optional[Dict[str, Any]] = None


class MemoryResult(BaseModel):
    """Domain model representing a match from a memory query.

    Attributes:
        entry: The matched MemoryEntry domain model.
        score: Relevance or similarity score (e.g. cosine distance/similarity).
    """

    entry: MemoryEntry
    score: float


class UserDomain(BaseModel):
    """Domain model representing User database entry."""

    id: Optional[int] = None
    username: str
    email: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PreferenceDomain(BaseModel):
    """Domain model representing Preference database entry."""

    id: Optional[int] = None
    user_id: int
    key: str
    value: Any
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class WorkspaceProfileDomain(BaseModel):
    """Domain model representing WorkspaceProfile database entry."""

    id: Optional[int] = None
    user_id: int
    name: str
    path: str
    settings: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ContextDomain(BaseModel):
    """Domain model representing Context database entry."""

    id: Optional[int] = None
    user_id: int
    session_id: str
    active_window: Optional[str] = None
    workspace_path: Optional[str] = None
    metadata_bag: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ConversationHistoryDomain(BaseModel):
    """Domain model representing ConversationHistory database entry."""

    id: Optional[int] = None
    user_id: int
    session_id: str
    role: str
    content: str
    token_count: Optional[int] = None
    created_at: Optional[datetime] = None


class RoutineLearningDomain(BaseModel):
    """Domain model representing RoutineLearning database entry."""

    id: Optional[int] = None
    user_id: int
    trigger_event: str
    action_sequence: Dict[str, Any]
    confidence_score: float = 0.0
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ExecutionHistoryDomain(BaseModel):
    """Domain model representing ExecutionHistory database entry."""

    id: Optional[int] = None
    user_id: int
    action: str
    status: str
    duration_ms: Optional[int] = None
    logs: Optional[str] = None
    input_parameters: Dict[str, Any] = Field(default_factory=dict)
    output_result: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None


class MemoryEventDomain(BaseModel):
    """Domain model representing MemoryEvent database entry."""

    id: Optional[int] = None
    user_id: int
    event_type: str
    payload: Dict[str, Any]
    created_at: Optional[datetime] = None


class AssistantContext(BaseModel):
    """Domain model aggregating context information from the memory subsystem."""

    recent_conversations: List[MemoryEntry] = Field(default_factory=list)
    recent_executions: List[MemoryEntry] = Field(default_factory=list)
    current_context: Optional[MemoryEntry] = None
    preferences: List[MemoryEntry] = Field(default_factory=list)
    workspace_context: Optional[MemoryEntry] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

