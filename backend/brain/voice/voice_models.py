"""Immutable data models for the Auralis Voice Orchestration Engine (Phase 9.6).

All models use ConfigDict(frozen=True) for thread-safe, immutable snapshots.
No business logic. No OS interaction. No imports from other voice modules.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class VoiceCommandStatus(str, Enum):
    """Lifecycle status of a voice command."""

    RECEIVED = "RECEIVED"
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CLARIFIED = "CLARIFIED"
    DISPATCHED = "DISPATCHED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


class VoiceInteractionType(str, Enum):
    """Type of voice interaction step."""

    COMMAND = "COMMAND"
    CONFIRMATION = "CONFIRMATION"
    CLARIFICATION = "CLARIFICATION"
    FEEDBACK = "FEEDBACK"
    CANCELLATION = "CANCELLATION"


class ConfirmationStatus(str, Enum):
    """Status of a pending confirmation."""

    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    TIMED_OUT = "TIMED_OUT"
    CANCELLED = "CANCELLED"


class ClarificationStatus(str, Enum):
    """Status of a pending clarification."""

    PENDING = "PENDING"
    RECEIVED = "RECEIVED"
    TIMED_OUT = "TIMED_OUT"
    CANCELLED = "CANCELLED"


class VoiceSessionState(str, Enum):
    """Lifecycle state of a voice session."""

    IDLE = "IDLE"
    ACTIVE = "ACTIVE"
    CONFIRMING = "CONFIRMING"
    CLARIFYING = "CLARIFYING"
    PROCESSING = "PROCESSING"
    ENDED = "ENDED"


# ---------------------------------------------------------------------------
# Core Voice Models
# ---------------------------------------------------------------------------


class VoiceCommand(BaseModel):
    """Immutable representation of a processed voice command."""

    model_config = ConfigDict(frozen=True)

    command_id: str = ""
    session_id: str = ""
    raw_text: str = ""
    normalized_text: str = ""
    confidence: float = 1.0
    language: str = "en"
    status: VoiceCommandStatus = VoiceCommandStatus.RECEIVED
    requires_confirmation: bool = False
    requires_clarification: bool = False
    received_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VoiceResponse(BaseModel):
    """Immutable response to return to the Voice Listener layer."""

    model_config = ConfigDict(frozen=True)

    response_id: str = ""
    session_id: str = ""
    text: str = ""
    interaction_type: VoiceInteractionType = VoiceInteractionType.FEEDBACK
    success: bool = True
    command_id: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VoiceConfirmation(BaseModel):
    """Immutable record of a pending or resolved confirmation."""

    model_config = ConfigDict(frozen=True)

    confirmation_id: str = ""
    session_id: str = ""
    command_id: str = ""
    prompt: str = ""
    status: ConfirmationStatus = ConfirmationStatus.PENDING
    response: Optional[bool] = None
    timeout_seconds: float = 30.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VoiceClarification(BaseModel):
    """Immutable record of a pending or resolved clarification."""

    model_config = ConfigDict(frozen=True)

    clarification_id: str = ""
    session_id: str = ""
    command_id: str = ""
    prompt: str = ""
    options: List[str] = Field(default_factory=list)
    status: ClarificationStatus = ClarificationStatus.PENDING
    selected_option: Optional[str] = None
    timeout_seconds: float = 30.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VoiceFeedback(BaseModel):
    """Immutable spoken feedback response."""

    model_config = ConfigDict(frozen=True)

    feedback_id: str = ""
    command_id: str = ""
    session_id: str = ""
    text: str = ""
    success: bool = True
    duration_ms: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VoiceInteractionResult(BaseModel):
    """Immutable result of a complete voice command lifecycle."""

    model_config = ConfigDict(frozen=True)

    command_id: str = ""
    session_id: str = ""
    success: bool = True
    status: VoiceCommandStatus = VoiceCommandStatus.COMPLETED
    feedback: Optional[VoiceFeedback] = None
    pipeline_ms: float = 0.0
    confirmation_required: bool = False
    clarification_required: bool = False
    error: Optional[str] = None
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Runtime / Health Models
# ---------------------------------------------------------------------------


class VoiceRuntimeHealth(BaseModel):
    """Immutable health snapshot for the Voice Orchestration Engine."""

    model_config = ConfigDict(frozen=True)

    healthy: bool = True
    status: str = "READY"
    active_sessions: int = 0
    registered_components: List[str] = Field(default_factory=list)
    uptime_seconds: float = 0.0
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VoiceRuntimeStatistics(BaseModel):
    """Immutable statistics snapshot for the Voice Orchestration Engine."""

    model_config = ConfigDict(frozen=True)

    commands_received: int = 0
    commands_completed: int = 0
    commands_failed: int = 0
    commands_cancelled: int = 0
    confirmations_requested: int = 0
    confirmations_accepted: int = 0
    confirmations_rejected: int = 0
    confirmations_timed_out: int = 0
    clarifications_requested: int = 0
    clarifications_received: int = 0
    clarifications_timed_out: int = 0
    sessions_started: int = 0
    sessions_ended: int = 0
    average_pipeline_ms: float = 0.0
    peak_concurrent_sessions: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)
