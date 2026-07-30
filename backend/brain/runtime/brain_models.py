"""Immutable data models for the Auralis Brain Runtime Integration Layer (Phase 9.7).

All models use ConfigDict(frozen=True) for thread-safe, immutable snapshots across runtime boundaries.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class RuntimeComponent(str, Enum):
    """Supported subsystem components in the Auralis Brain architecture."""

    VOICE = "VOICE"
    CONVERSATION = "CONVERSATION"
    REASONING = "REASONING"
    PLANNING = "PLANNING"
    EXECUTION = "EXECUTION"
    FILESYSTEM = "FILESYSTEM"
    BRAIN = "BRAIN"


class PipelineStatus(str, Enum):
    """Lifecycle status of an end-to-end integration pipeline execution."""

    INITIALIZING = "INITIALIZING"
    PENDING = "PENDING"
    VOICE_PROCESSING = "VOICE_PROCESSING"
    CONVERSATION_PROCESSING = "CONVERSATION_PROCESSING"
    REASONING_PROCESSING = "REASONING_PROCESSING"
    PLANNING_PROCESSING = "PLANNING_PROCESSING"
    EXECUTION_PROCESSING = "EXECUTION_PROCESSING"
    FILESYSTEM_PROCESSING = "FILESYSTEM_PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


# ---------------------------------------------------------------------------
# Request & Response Models
# ---------------------------------------------------------------------------


class BrainRequest(BaseModel):
    """Immutable incoming request to the Auralis Brain Runtime."""

    model_config = ConfigDict(frozen=True)

    request_id: str = ""
    raw_text: str = ""
    session_id: str = ""
    conversation_id: Optional[str] = None
    language: str = "en"
    confidence: float = 1.0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BrainResponse(BaseModel):
    """Immutable response returned by the Auralis Brain Runtime."""

    model_config = ConfigDict(frozen=True)

    request_id: str = ""
    session_id: str = ""
    conversation_id: Optional[str] = None
    success: bool = True
    text: str = ""
    voice_response: Optional[Dict[str, Any]] = None
    execution_summary: Optional[Dict[str, Any]] = None
    pipeline_status: PipelineStatus = PipelineStatus.COMPLETED
    duration_ms: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Health & Statistics Models
# ---------------------------------------------------------------------------


class SubsystemHealth(BaseModel):
    """Immutable health snapshot for a single subsystem runtime."""

    model_config = ConfigDict(frozen=True)

    subsystem_name: str = ""
    healthy: bool = True
    status: str = "READY"
    components: Dict[str, bool] = Field(default_factory=dict)
    issues: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SubsystemStatistics(BaseModel):
    """Immutable statistics snapshot for a single subsystem runtime."""

    model_config = ConfigDict(frozen=True)

    subsystem_name: str = ""
    stats: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BrainRuntimeHealth(BaseModel):
    """Immutable overall health snapshot for the Auralis Brain Runtime."""

    model_config = ConfigDict(frozen=True)

    healthy: bool = True
    status: str = "READY"
    subsystems: Dict[str, SubsystemHealth] = Field(default_factory=dict)
    active_requests: int = 0
    uptime_seconds: float = 0.0
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BrainRuntimeStatistics(BaseModel):
    """Immutable overall diagnostic statistics for the Auralis Brain Runtime."""

    model_config = ConfigDict(frozen=True)

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_pipeline_ms: float = 0.0
    subsystem_stats: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    peak_concurrent_requests: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Pipeline Output Models
# ---------------------------------------------------------------------------


class PipelineResult(BaseModel):
    """Immutable detailed result of executing the full Brain Integration Pipeline."""

    model_config = ConfigDict(frozen=True)

    request_id: str = ""
    status: PipelineStatus = PipelineStatus.COMPLETED
    success: bool = True
    voice_result: Optional[Dict[str, Any]] = None
    conversation_result: Optional[Dict[str, Any]] = None
    reasoning_result: Optional[Dict[str, Any]] = None
    planning_result: Optional[Dict[str, Any]] = None
    execution_result: Optional[Dict[str, Any]] = None
    filesystem_result: Optional[Dict[str, Any]] = None
    pipeline_ms: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
