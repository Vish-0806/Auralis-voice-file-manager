"""Data models for Auralis Conversational Intelligence."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


class DialoguePhase(str, Enum):
    """Phases of conversation flow."""

    IDLE = "IDLE"
    WAITING_FOR_CLARIFICATION = "WAITING_FOR_CLARIFICATION"
    PROCESSING_TASK = "PROCESSING_TASK"
    CONFIRMING_ACTION = "CONFIRMING_ACTION"
    COMPLETED = "COMPLETED"


class PendingClarification(BaseModel):
    """Represents a request for clarifying an ambiguous command parameter."""

    clarification_id: str
    parameter_name: str  # e.g., "file", "folder", "project", "application", "workflow"
    original_value: str  # the ambiguous text value supplied by the user
    options: List[str]   # list of candidate resolutions
    prompt: str          # clarification prompt/question to ask the user
    command_to_resume: str  # the original command string to re-run once resolved


class DialogueState(BaseModel):
    """Active conversational state variables for a session."""

    session_id: str
    phase: DialoguePhase = DialoguePhase.IDLE
    active_task: Optional[str] = None
    active_workflow: Optional[str] = None
    current_workspace: Optional[str] = None
    pending_clarification: Optional[PendingClarification] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DialogueTurn(BaseModel):
    """A single turn in the conversation history."""

    turn_id: str
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    entities: Dict[str, Any] = Field(default_factory=dict)
    resolved_objects: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DialogueHistory(BaseModel):
    """The structured history of a conversation session."""

    session_id: str
    turns: List[DialogueTurn] = Field(default_factory=list)
    branches: Dict[str, List[DialogueTurn]] = Field(default_factory=dict)
