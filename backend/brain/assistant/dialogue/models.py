"""Dialogue Management Data Models for Auralis (Phase 13.3).

Defines immutable Pydantic v2 domain models and enums representing dialogue states,
turns, sessions, context, policies, decisions, statistics, and health reports
using ConfigDict(frozen=True).
"""

from datetime import datetime, timezone
from enum import Enum
import uuid
from typing import Any, Dict, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


class DialogueStatus(str, Enum):
    """Lifecycle statuses of a dialogue flow session."""

    IDLE = "IDLE"
    LISTENING = "LISTENING"
    PROCESSING = "PROCESSING"
    WAITING_FOR_CLARIFICATION = "WAITING_FOR_CLARIFICATION"
    WAITING_FOR_CONFIRMATION = "WAITING_FOR_CONFIRMATION"
    RESPONDING = "RESPONDING"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"


class DialogueAction(str, Enum):
    """Action recommendation determined by dialogue policy evaluation."""

    RESPOND = "RESPOND"
    CLARIFY = "CLARIFY"
    CONFIRM = "CONFIRM"
    EXECUTE = "EXECUTE"
    WAIT = "WAIT"
    TERMINATE = "TERMINATE"
    REJECT = "REJECT"


class DialogueMode(str, Enum):
    """Execution mode governing dialogue interaction styles."""

    DIRECT = "DIRECT"
    INTERACTIVE = "INTERACTIVE"
    GUIDED = "GUIDED"
    AUTONOMOUS = "AUTONOMOUS"
    DEFAULT = "DEFAULT"


class DialogueContext(BaseModel):
    """Immutable context variables and environment attached to a dialogue session."""

    model_config = ConfigDict(frozen=True)

    session_id: str = ""
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None
    workspace_id: Optional[str] = None
    active_intent: Optional[str] = None
    slot_values: Dict[str, Any] = Field(default_factory=dict)
    variables: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DialogueTurn(BaseModel):
    """Immutable representation of a single dialogue turn (user input + system response)."""

    model_config = ConfigDict(frozen=True)

    turn_id: str = Field(default_factory=lambda: f"turn-{uuid.uuid4().hex[:8]}")
    session_id: str = ""
    turn_number: int = 1
    user_input: str = ""
    system_response: Optional[str] = None
    recommended_action: DialogueAction = DialogueAction.RESPOND
    requires_clarification: bool = False
    requires_confirmation: bool = False
    confidence: float = 1.0
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DialogueState(BaseModel):
    """Immutable snapshot of current dialogue state and active turn."""

    model_config = ConfigDict(frozen=True)

    status: DialogueStatus = DialogueStatus.IDLE
    current_turn: Optional[DialogueTurn] = None
    turn_count: int = 0
    pending_clarification: Optional[str] = None
    pending_confirmation: Optional[str] = None
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    details: Dict[str, Any] = Field(default_factory=dict)


class DialoguePolicy(BaseModel):
    """Immutable rules and policies governing dialogue decisions."""

    model_config = ConfigDict(frozen=True)

    policy_id: str = "default_policy"
    require_confirmation_for_destructive: bool = True
    auto_clarify_threshold: float = 0.6
    max_clarification_attempts: int = 3
    default_mode: DialogueMode = DialogueMode.DEFAULT
    rules: Dict[str, Any] = Field(default_factory=dict)


class DialogueDecision(BaseModel):
    """Immutable decision report produced by policy evaluation."""

    model_config = ConfigDict(frozen=True)

    action: DialogueAction = DialogueAction.RESPOND
    mode: DialogueMode = DialogueMode.DEFAULT
    requires_clarification: bool = False
    requires_confirmation: bool = False
    clarification_prompt: Optional[str] = None
    confirmation_prompt: Optional[str] = None
    confidence: float = 1.0
    reason: str = "Standard dialogue flow"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DialogueSession(BaseModel):
    """Immutable representation of a dialogue session."""

    model_config = ConfigDict(frozen=True)

    session_id: str = Field(default_factory=lambda: f"dsess-{uuid.uuid4().hex[:8]}")
    conversation_id: Optional[str] = None
    status: DialogueStatus = DialogueStatus.IDLE
    mode: DialogueMode = DialogueMode.DEFAULT
    turns: List[DialogueTurn] = Field(default_factory=list)
    context: DialogueContext = Field(default_factory=DialogueContext)
    policy: DialoguePolicy = Field(default_factory=DialoguePolicy)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DialogueStatistics(BaseModel):
    """Immutable metrics and statistics for the dialogue management subsystem."""

    model_config = ConfigDict(frozen=True)

    total_sessions_created: int = 0
    active_sessions: int = 0
    total_turns_processed: int = 0
    clarifications_requested: int = 0
    confirmations_requested: int = 0
    average_turns_per_session: float = 0.0
    uptime_seconds: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DialogueHealth(BaseModel):
    """Immutable health status report of the dialogue subsystem."""

    model_config = ConfigDict(frozen=True)

    status: str = "READY"
    healthy: bool = True
    subsystems: Dict[str, bool] = Field(default_factory=dict)
    statistics: Dict[str, Any] = Field(default_factory=dict)
    detected_issues: List[str] = Field(default_factory=list)
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)
