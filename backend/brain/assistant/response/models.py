"""Assistant Response Generation & Streaming Data Models for Auralis (Phase 13.6).

Defines immutable Pydantic v2 domain models and enums representing responses,
chunks, streams, contexts, metadata, formatting templates, statistics, and health reports
using ConfigDict(frozen=True).
"""

from datetime import datetime, timezone
from enum import Enum
import uuid
from typing import Any, Dict, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


class ResponseFormat(str, Enum):
    """Supported formatting output formats for assistant responses."""

    MARKDOWN = "MARKDOWN"
    PLAIN_TEXT = "PLAIN_TEXT"
    JSON = "JSON"


class ResponseState(str, Enum):
    """Lifecycle states of response assembly and streaming."""

    PENDING = "PENDING"
    GENERATING = "GENERATING"
    STREAMING = "STREAMING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class StreamingMode(str, Enum):
    """Modes supported for streaming assistant responses."""

    FULL_RESPONSE = "FULL_RESPONSE"
    CHUNK_STREAM = "CHUNK_STREAM"


class ResponseMetadata(BaseModel):
    """Immutable metadata accompanying an assistant response."""

    model_config = ConfigDict(frozen=True)

    session_id: Optional[str] = None
    conversation_id: Optional[str] = None
    turn_id: Optional[str] = None
    model_name: str = "AuralisAssistantEngine"
    citations: List[str] = Field(default_factory=list)
    execution_summary: Dict[str, Any] = Field(default_factory=dict)
    custom_attributes: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ResponseContext(BaseModel):
    """Immutable context variables supplied during response synthesis."""

    model_config = ConfigDict(frozen=True)

    request_id: str = ""
    prompt: str = ""
    format_type: ResponseFormat = ResponseFormat.MARKDOWN
    streaming_mode: StreamingMode = StreamingMode.FULL_RESPONSE
    variables: Dict[str, Any] = Field(default_factory=dict)
    metadata: ResponseMetadata = Field(default_factory=ResponseMetadata)


class ResponseChunk(BaseModel):
    """Immutable single chunk within a response stream."""

    model_config = ConfigDict(frozen=True)

    chunk_id: str = Field(default_factory=lambda: f"chk-{uuid.uuid4().hex[:8]}")
    response_id: str = ""
    chunk_index: int = 0
    text: str = ""
    is_final: bool = False
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AssistantResponse(BaseModel):
    """Immutable complete assistant response container."""

    model_config = ConfigDict(frozen=True)

    response_id: str = Field(default_factory=lambda: f"resp-{uuid.uuid4().hex[:8]}")
    request_id: str = ""
    content: str = ""
    formatted_content: str = ""
    format_type: ResponseFormat = ResponseFormat.MARKDOWN
    state: ResponseState = ResponseState.COMPLETED
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    tokens_used: int = 0
    latency_ms: float = 0.0
    metadata: ResponseMetadata = Field(default_factory=ResponseMetadata)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ResponseStream(BaseModel):
    """Immutable stream session tracking chunk sequence delivery."""

    model_config = ConfigDict(frozen=True)

    stream_id: str = Field(default_factory=lambda: f"strm-{uuid.uuid4().hex[:8]}")
    response_id: str = ""
    mode: StreamingMode = StreamingMode.CHUNK_STREAM
    chunks: List[ResponseChunk] = Field(default_factory=list)
    total_chunks: int = 0
    is_complete: bool = False
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None


class ResponseTemplate(BaseModel):
    """Immutable structure defining output formatting templates."""

    model_config = ConfigDict(frozen=True)

    template_id: str = "default_template"
    format_type: ResponseFormat = ResponseFormat.MARKDOWN
    include_citations: bool = True
    include_execution_summary: bool = True
    header_text: Optional[str] = None
    footer_text: Optional[str] = None


class ResponseStatistics(BaseModel):
    """Immutable performance and streaming statistics for the response runtime."""

    model_config = ConfigDict(frozen=True)

    total_responses_built: int = 0
    total_streams_generated: int = 0
    total_chunks_emitted: int = 0
    average_response_latency_ms: float = 0.0
    formats_rendered: Dict[str, int] = Field(default_factory=dict)
    uptime_seconds: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ResponseHealth(BaseModel):
    """Immutable diagnostic health status report of the response subsystem."""

    model_config = ConfigDict(frozen=True)

    status: str = "READY"
    healthy: bool = True
    subsystems: Dict[str, bool] = Field(default_factory=dict)
    statistics: Dict[str, Any] = Field(default_factory=dict)
    detected_issues: List[str] = Field(default_factory=list)
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)
