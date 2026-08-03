"""Assistant Memory & Context Integration Data Models for Auralis (Phase 13.5).

Defines immutable Pydantic v2 domain models and enums representing memory contexts,
snapshots, references, preferences, conversation summaries, working contexts,
statistics, and health reports using ConfigDict(frozen=True).
"""

from datetime import datetime, timezone
from enum import Enum
import uuid
from typing import Any, Dict, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


class AssistantMemoryScope(str, Enum):
    """Scope boundaries for memory context variables."""

    SESSION = "SESSION"
    CONVERSATION = "CONVERSATION"
    USER = "USER"
    GLOBAL = "GLOBAL"
    EPHEMERAL = "EPHEMERAL"


class AssistantContextPriority(str, Enum):
    """Priority weights assigned during context merge and token budgeting."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    MANDATORY = "MANDATORY"


class AssistantMemorySource(str, Enum):
    """Subsystem sources contributing to aggregated assistant memory context."""

    CONVERSATION_RUNTIME = "CONVERSATION_RUNTIME"
    DIALOGUE_RUNTIME = "DIALOGUE_RUNTIME"
    DECISION_RUNTIME = "DECISION_RUNTIME"
    EXECUTION_RUNTIME = "EXECUTION_RUNTIME"
    AI_MEMORY_RUNTIME = "AI_MEMORY_RUNTIME"
    PREFERENCE_MANAGER = "PREFERENCE_MANAGER"
    SYSTEM = "SYSTEM"


class AssistantMemoryReference(BaseModel):
    """Immutable reference pointing to a source memory item."""

    model_config = ConfigDict(frozen=True)

    reference_id: str = Field(default_factory=lambda: f"ref-{uuid.uuid4().hex[:8]}")
    source: AssistantMemorySource = AssistantMemorySource.SYSTEM
    source_key: str = ""
    priority: AssistantContextPriority = AssistantContextPriority.MEDIUM
    tokens_estimate: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AssistantConversationSummary(BaseModel):
    """Immutable summary snapshot of a conversation thread."""

    model_config = ConfigDict(frozen=True)

    conversation_id: str = ""
    title: str = ""
    message_count: int = 0
    current_topic: Optional[str] = None
    last_activity: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AssistantPreference(BaseModel):
    """Immutable user, assistant, or runtime preference setting."""

    model_config = ConfigDict(frozen=True)

    key: str = ""
    value: Any = None
    scope: AssistantMemoryScope = AssistantMemoryScope.USER
    overridable: bool = True
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AssistantMemoryContext(BaseModel):
    """Immutable scoped context unit merged into the assistant working context."""

    model_config = ConfigDict(frozen=True)

    context_id: str = Field(default_factory=lambda: f"mctx-{uuid.uuid4().hex[:8]}")
    source: AssistantMemorySource = AssistantMemorySource.SYSTEM
    scope: AssistantMemoryScope = AssistantMemoryScope.SESSION
    priority: AssistantContextPriority = AssistantContextPriority.MEDIUM
    payload: Dict[str, Any] = Field(default_factory=dict)
    tokens_estimate: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AssistantWorkingContext(BaseModel):
    """Immutable merged working context bound to a token budget."""

    model_config = ConfigDict(frozen=True)

    working_context_id: str = Field(default_factory=lambda: f"wctx-{uuid.uuid4().hex[:8]}")
    session_id: Optional[str] = None
    merged_variables: Dict[str, Any] = Field(default_factory=dict)
    active_preferences: Dict[str, Any] = Field(default_factory=dict)
    prioritized_contexts: List[AssistantMemoryContext] = Field(default_factory=list)
    total_tokens_estimate: int = 0
    token_budget: int = 4096
    trimmed: bool = False
    merged_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AssistantMemorySnapshot(BaseModel):
    """Immutable snapshot coordinating all subsystem contexts into a unified view."""

    model_config = ConfigDict(frozen=True)

    snapshot_id: str = Field(default_factory=lambda: f"snap-{uuid.uuid4().hex[:8]}")
    session_id: Optional[str] = None
    conversation_summary: Optional[AssistantConversationSummary] = None
    dialogue_status: Optional[str] = None
    last_decision_action: Optional[str] = None
    working_context: AssistantWorkingContext = Field(default_factory=AssistantWorkingContext)
    references: List[AssistantMemoryReference] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AssistantMemoryStatistics(BaseModel):
    """Immutable statistics metrics of the assistant memory & context integration subsystem."""

    model_config = ConfigDict(frozen=True)

    total_context_merges: int = 0
    total_snapshots_generated: int = 0
    preferences_merged: int = 0
    duplicates_removed: int = 0
    token_budget_trims: int = 0
    average_merge_latency_ms: float = 0.0
    uptime_seconds: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AssistantMemoryHealth(BaseModel):
    """Immutable health status report of the assistant memory integration subsystem."""

    model_config = ConfigDict(frozen=True)

    status: str = "READY"
    healthy: bool = True
    subsystems: Dict[str, bool] = Field(default_factory=dict)
    statistics: Dict[str, Any] = Field(default_factory=dict)
    detected_issues: List[str] = Field(default_factory=list)
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)
