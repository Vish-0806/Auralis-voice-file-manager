"""Strongly typed Pydantic models for the Auralis AI Architecture Foundation (Phase 10.1).

Defines data models for providers, contexts, prompts, requests, responses, tool calls, and tool results.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class ToolCategory(str, Enum):
    """Supported categories for AI tools."""

    FILESYSTEM = "filesystem"
    MEMORY = "memory"
    AUTOMATION = "automation"
    VOICE = "voice"
    PLANNER = "planner"
    EXECUTION = "execution"


class FinishReason(str, Enum):
    """Reason for completion of an AI provider request."""

    STOP = "stop"
    LENGTH = "length"
    TOOL_CALLS = "tool_calls"
    CONTENT_FILTER = "content_filter"
    ERROR = "error"
    UNKNOWN = "unknown"


class PromptRole(str, Enum):
    """Roles in structured prompt messages."""

    SYSTEM = "system"
    DEVELOPER = "developer"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    MEMORY = "memory"


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------


class ProviderInfo(BaseModel):
    """Metadata describing an AI Provider capabilities and health status."""

    model_config = ConfigDict(frozen=True)

    provider_id: str
    name: str
    version: str = "1.0.0"
    is_available: bool = True
    supported_features: List[str] = Field(default_factory=list)
    max_context_window: int = 128000
    default_model_name: str = "stub-model"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ToolCall(BaseModel):
    """Model representing a tool execution request emitted by an AI model."""

    model_config = ConfigDict(frozen=True)

    call_id: str
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    category: ToolCategory = ToolCategory.FILESYSTEM
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ToolResult(BaseModel):
    """Model representing the outcome of an executed tool call."""

    model_config = ConfigDict(frozen=True)

    call_id: str
    tool_name: str
    success: bool
    output: Optional[Any] = None
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AIContext(BaseModel):
    """Structured context constructed for an incoming request before prompt generation."""

    model_config = ConfigDict(frozen=True)

    request_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None
    raw_query: str = ""
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    memory_context: Dict[str, Any] = Field(default_factory=dict)
    workspace_context: Dict[str, Any] = Field(default_factory=dict)
    execution_context: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PromptMessage(BaseModel):
    """Individual message in a structured prompt."""

    model_config = ConfigDict(frozen=True)

    role: PromptRole
    content: str
    name: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Prompt(BaseModel):
    """Structured prompt object containing all prompt layers ready for provider consumption."""

    model_config = ConfigDict(frozen=True)

    system_prompt: str = ""
    developer_prompt: str = ""
    user_prompt: str = ""
    tool_prompt: str = ""
    memory_prompt: str = ""
    formatted_messages: List[PromptMessage] = Field(default_factory=list)
    token_estimate: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AIRequest(BaseModel):
    """Payload sent to an AIProvider for completion generation."""

    model_config = ConfigDict(frozen=True)

    request_id: str
    prompt: Prompt
    tools: List[Dict[str, Any]] = Field(default_factory=list)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    provider_name: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AIResponse(BaseModel):
    """Structured output returned from an AIProvider completion generation."""

    model_config = ConfigDict(frozen=True)

    response_id: str
    request_id: str
    text: str = ""
    tool_calls: List[ToolCall] = Field(default_factory=list)
    finish_reason: FinishReason = FinishReason.STOP
    usage_stats: Dict[str, int] = Field(default_factory=dict)
    raw_response: Dict[str, Any] = Field(default_factory=dict)
    provider_name: str = "stub-provider"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
