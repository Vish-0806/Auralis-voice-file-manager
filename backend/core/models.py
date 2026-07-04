"""Core data contracts for Auralis.

This module defines the shared request, plan, result, response, and session
models used by the core orchestration layer. The models are intentionally kept
free of execution logic so they can be reused across planners, dispatchers,
capabilities, and API adapters without introducing circular imports.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from .intents import Intent


class AuralisBaseModel(BaseModel):
    """Base Pydantic model for Auralis core contracts."""

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )


class AssistantRequest(AuralisBaseModel):
    """Represents an incoming user request for the assistant."""

    message: str
    source: str
    timestamp: datetime


class ExecutionPlan(AuralisBaseModel):
    """Represents the planner output for a request."""

    intent: Intent
    target: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0)

    @field_serializer("intent")
    def _serialize_intent(self, intent: Intent) -> str:
        """Serializes the intent as its canonical string value."""

        return intent.value


class ExecutionResult(AuralisBaseModel):
    """Represents the outcome of plan execution."""

    success: bool
    response: str
    data: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    execution_time: float = Field(ge=0.0)


class AssistantResponse(AuralisBaseModel):
    """Represents the assistant response returned to the caller."""

    response: str
    plan: ExecutionPlan
    result: ExecutionResult


class SessionContext(AuralisBaseModel):
    """Represents the active session state shared across core services."""

    session_id: str
    current_project: str | None = None
    current_directory: str | None = None
    active_capability: str | None = None
    conversation_id: str | None = None


__all__ = [
    "AuralisBaseModel",
    "AssistantRequest",
    "ExecutionPlan",
    "ExecutionResult",
    "AssistantResponse",
    "SessionContext",
]