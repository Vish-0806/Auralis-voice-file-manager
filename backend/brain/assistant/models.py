"""Assistant Runtime Data Models for Auralis (Phase 13.1).

Defines immutable Pydantic v2 domain models representing Assistant Runtime states,
statuses, capabilities, statistics, health reports, execution contexts, active sessions,
and configuration settings using ConfigDict(frozen=True).
"""

from datetime import datetime, timezone
from enum import Enum
import uuid
from typing import Any, Dict, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


class AssistantStateEnum(str, Enum):
    """Enumeration representing canonical Assistant Runtime lifecycle states."""

    UNINITIALIZED = "UNINITIALIZED"
    INITIALIZING = "INITIALIZING"
    READY = "READY"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    ERROR = "ERROR"


class AssistantState(BaseModel):
    """Immutable model representing the active state of the Assistant Runtime."""

    model_config = ConfigDict(frozen=True)

    state: AssistantStateEnum = AssistantStateEnum.UNINITIALIZED
    healthy: bool = True
    initialized_at: Optional[datetime] = None
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    details: Dict[str, Any] = Field(default_factory=dict)


class AssistantStatus(BaseModel):
    """Immutable status summary report of the Assistant Runtime."""

    model_config = ConfigDict(frozen=True)

    state: AssistantStateEnum = AssistantStateEnum.UNINITIALIZED
    healthy: bool = True
    provider_count: int = 0
    active_sessions: int = 0
    uptime_seconds: float = 0.0
    version: str = "1.0.0"
    details: Dict[str, Any] = Field(default_factory=dict)


class AssistantCapabilities(BaseModel):
    """Immutable capability specifications supported by the Assistant system."""

    model_config = ConfigDict(frozen=True)

    brain_integration: bool = True
    ai_integration: bool = True
    os_integration: bool = True
    execution_integration: bool = True
    streaming_supported: bool = False
    voice_supported: bool = False
    conversation_supported: bool = False
    supported_providers: List[str] = Field(default_factory=list)
    custom_capabilities: Dict[str, Any] = Field(default_factory=dict)


class AssistantStatistics(BaseModel):
    """Immutable performance and diagnostic statistics for the Assistant Runtime."""

    model_config = ConfigDict(frozen=True)

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    active_sessions: int = 0
    total_sessions_created: int = 0
    average_latency_ms: float = 0.0
    uptime_seconds: float = 0.0
    subsystem_metrics: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AssistantHealth(BaseModel):
    """Immutable health status of the Assistant Runtime and sub-runtimes."""

    model_config = ConfigDict(frozen=True)

    status: str = "READY"
    healthy: bool = True
    subsystems: Dict[str, bool] = Field(default_factory=dict)
    statistics: Dict[str, Any] = Field(default_factory=dict)
    detected_issues: List[str] = Field(default_factory=list)
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AssistantContext(BaseModel):
    """Immutable context variables and environment for an assistant session."""

    model_config = ConfigDict(frozen=True)

    session_id: str = Field(default_factory=lambda: f"sess-{uuid.uuid4().hex[:8]}")
    user_id: Optional[str] = None
    workspace_id: Optional[str] = None
    environment: str = "production"
    variables: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AssistantSession(BaseModel):
    """Immutable representation of an assistant session."""

    model_config = ConfigDict(frozen=True)

    session_id: str = Field(default_factory=lambda: f"sess-{uuid.uuid4().hex[:8]}")
    context: AssistantContext = Field(default_factory=AssistantContext)
    active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_accessed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AssistantConfiguration(BaseModel):
    """Immutable configuration settings for the Assistant Runtime."""

    model_config = ConfigDict(frozen=True)

    name: str = "AuralisAssistant"
    version: str = "1.0.0"
    enable_brain: bool = True
    enable_ai: bool = True
    enable_os: bool = True
    enable_execution: bool = True
    auto_initialize: bool = True
    max_concurrent_sessions: int = 100
    timeout_seconds: float = 30.0
    custom_settings: Dict[str, Any] = Field(default_factory=dict)
