"""Conversation Runtime Data Models for Auralis (Phase 13.2).

Defines immutable Pydantic v2 domain models and enums representing conversation
states, message roles, conversation types, messages, history, context, statistics,
health status, and metadata using ConfigDict(frozen=True).
"""

from datetime import datetime, timezone
from enum import Enum
import uuid
from typing import Any, Dict, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


class ConversationState(str, Enum):
    """Lifecycle states of a conversation session."""

    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    CLOSED = "CLOSED"
    ARCHIVED = "ARCHIVED"
    EXPIRED = "EXPIRED"
    ERROR = "ERROR"


class MessageRole(str, Enum):
    """Role associated with a conversation message author."""

    SYSTEM = "SYSTEM"
    USER = "USER"
    ASSISTANT = "ASSISTANT"
    TOOL = "TOOL"
    SYSTEM_NOTIFICATION = "SYSTEM_NOTIFICATION"


class ConversationType(str, Enum):
    """Classification type of conversation interaction."""

    DIRECT = "DIRECT"
    VOICE = "VOICE"
    MULTI_TURN = "MULTI_TURN"
    TASK = "TASK"
    GENERAL = "GENERAL"


class ConversationMetadata(BaseModel):
    """Immutable metadata associated with a conversation or message."""

    model_config = ConfigDict(frozen=True)

    title: str = "New Conversation"
    tags: List[str] = Field(default_factory=list)
    custom_attributes: Dict[str, Any] = Field(default_factory=dict)
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ConversationParticipant(BaseModel):
    """Immutable representation of a conversation participant."""

    model_config = ConfigDict(frozen=True)

    participant_id: str = Field(default_factory=lambda: f"part-{uuid.uuid4().hex[:8]}")
    name: str = "User"
    role: MessageRole = MessageRole.USER
    joined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationMessage(BaseModel):
    """Immutable representation of a single message within a conversation."""

    model_config = ConfigDict(frozen=True)

    message_id: str = Field(default_factory=lambda: f"msg-{uuid.uuid4().hex[:8]}")
    conversation_id: str = ""
    role: MessageRole = MessageRole.USER
    content: str = ""
    sender_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tokens_estimate: int = 0


class ConversationContext(BaseModel):
    """Immutable execution and scope context for a conversation."""

    model_config = ConfigDict(frozen=True)

    conversation_id: str = ""
    current_topic: Optional[str] = None
    user_id: Optional[str] = None
    workspace_id: Optional[str] = None
    assistant_context: Dict[str, Any] = Field(default_factory=dict)
    execution_context: Dict[str, Any] = Field(default_factory=dict)
    variables: Dict[str, Any] = Field(default_factory=dict)
    metadata: ConversationMetadata = Field(default_factory=ConversationMetadata)


class ConversationHistory(BaseModel):
    """Immutable message history container for a conversation."""

    model_config = ConfigDict(frozen=True)

    conversation_id: str = ""
    messages: List[ConversationMessage] = Field(default_factory=list)
    total_messages: int = 0
    total_tokens_estimate: int = 0
    trimmed: bool = False
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ConversationStatistics(BaseModel):
    """Immutable diagnostic and request metrics for the conversation runtime."""

    model_config = ConfigDict(frozen=True)

    total_conversations_created: int = 0
    active_conversations: int = 0
    closed_conversations: int = 0
    archived_conversations: int = 0
    total_messages_processed: int = 0
    average_messages_per_conversation: float = 0.0
    uptime_seconds: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationHealth(BaseModel):
    """Immutable health status of the conversation runtime and storage providers."""

    model_config = ConfigDict(frozen=True)

    status: str = "READY"
    healthy: bool = True
    subsystems: Dict[str, bool] = Field(default_factory=dict)
    statistics: Dict[str, Any] = Field(default_factory=dict)
    detected_issues: List[str] = Field(default_factory=list)
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Conversation(BaseModel):
    """Immutable top-level conversation model encapsulating state and participants."""

    model_config = ConfigDict(frozen=True)

    conversation_id: str = Field(default_factory=lambda: f"conv-{uuid.uuid4().hex[:8]}")
    conversation_type: ConversationType = ConversationType.GENERAL
    state: ConversationState = ConversationState.ACTIVE
    participants: List[ConversationParticipant] = Field(default_factory=list)
    context: ConversationContext = Field(default_factory=ConversationContext)
    metadata: ConversationMetadata = Field(default_factory=ConversationMetadata)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    closed_at: Optional[datetime] = None
