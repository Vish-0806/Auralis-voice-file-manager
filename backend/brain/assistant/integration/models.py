"""Assistant Runtime Integration Layer Data Models for Auralis (Phase 13.9).

Defines immutable Pydantic v2 domain models and enums representing integration requests,
responses, contexts, states, capabilities, statistics, health reports, sessions, runtime snapshots,
and execution summaries using ConfigDict(frozen=True).
"""

from datetime import datetime, timezone
from enum import Enum
import uuid
from typing import Any, Dict, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


class IntegrationState(str, Enum):
    """Overall operational state of the Assistant Integration Runtime."""

    UNINITIALIZED = "UNINITIALIZED"
    READY = "READY"
    RUNNING = "RUNNING"
    DEGRADED = "DEGRADED"
    SHUTDOWN = "SHUTDOWN"
    ERROR = "ERROR"


class IntegrationStage(str, Enum):
    """Pipeline stages executed by the PipelineCoordinator."""

    INITIALIZATION = "INITIALIZATION"
    CONVERSATION = "CONVERSATION"
    DIALOGUE = "DIALOGUE"
    DECISION = "DECISION"
    MEMORY = "MEMORY"
    EXECUTION = "EXECUTION"
    RESPONSE = "RESPONSE"
    VOICE = "VOICE"
    PROACTIVE = "PROACTIVE"
    COMPLETED = "COMPLETED"


class IntegrationStatus(str, Enum):
    """Outcome status of an integration request execution."""

    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"


class PipelineState(str, Enum):
    """State of the assistant execution pipeline."""

    IDLE = "IDLE"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AssistantMode(str, Enum):
    """Operating modes supported by the unified assistant architecture."""

    STANDARD = "STANDARD"
    VOICE = "VOICE"
    PROACTIVE = "PROACTIVE"
    HEADLESS = "HEADLESS"
    AUTONOMOUS = "AUTONOMOUS"


class AssistantExecutionSummary(BaseModel):
    """Immutable summary of stage execution across sub-runtimes."""

    model_config = ConfigDict(frozen=True)

    stage: IntegrationStage = IntegrationStage.COMPLETED
    duration_ms: float = 0.0
    success: bool = True
    summary_data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AssistantRuntimeSnapshot(BaseModel):
    """Immutable snapshot of registered runtime instances and metadata."""

    model_config = ConfigDict(frozen=True)

    runtime_name: str = ""
    version: str = "1.0.0"
    is_available: bool = True
    status: str = "READY"
    capabilities: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AssistantIntegrationContext(BaseModel):
    """Immutable environmental context passed through the integration pipeline."""

    model_config = ConfigDict(frozen=True)

    session_id: Optional[str] = None
    user_id: Optional[str] = None
    assistant_mode: AssistantMode = AssistantMode.STANDARD
    active_stage: IntegrationStage = IntegrationStage.INITIALIZATION
    global_variables: Dict[str, Any] = Field(default_factory=dict)
    runtime_snapshots: List[AssistantRuntimeSnapshot] = Field(default_factory=list)


class AssistantIntegrationRequest(BaseModel):
    """Immutable request structure supplied to the Assistant Integration Gateway."""

    model_config = ConfigDict(frozen=True)

    request_id: str = Field(default_factory=lambda: f"ireq-{uuid.uuid4().hex[:8]}")
    user_prompt: str = ""
    mode: AssistantMode = AssistantMode.STANDARD
    context: AssistantIntegrationContext = Field(default_factory=AssistantIntegrationContext)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AssistantIntegrationResponse(BaseModel):
    """Immutable unified integration response output by the Assistant Gateway."""

    model_config = ConfigDict(frozen=True)

    response_id: str = Field(default_factory=lambda: f"iresp-{uuid.uuid4().hex[:8]}")
    request_id: str = ""
    status: IntegrationStatus = IntegrationStatus.SUCCESS
    assistant_reply: str = ""
    formatted_reply: str = ""
    current_stage: IntegrationStage = IntegrationStage.COMPLETED
    execution_summaries: List[AssistantExecutionSummary] = Field(default_factory=list)
    total_latency_ms: float = 0.0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AssistantIntegrationState(BaseModel):
    """Immutable state container tracking pipeline and subsystem status."""

    model_config = ConfigDict(frozen=True)

    state: IntegrationState = IntegrationState.READY
    pipeline_state: PipelineState = PipelineState.IDLE
    active_mode: AssistantMode = AssistantMode.STANDARD
    active_requests_count: int = 0
    registered_runtimes_count: int = 0
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AssistantIntegrationSession(BaseModel):
    """Immutable integration session container."""

    model_config = ConfigDict(frozen=True)

    session_id: str = Field(default_factory=lambda: f"isess-{uuid.uuid4().hex[:8]}")
    user_id: Optional[str] = None
    mode: AssistantMode = AssistantMode.STANDARD
    requests_processed: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_active_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AssistantIntegrationCapabilities(BaseModel):
    """Immutable specification of aggregated capabilities across all assistant runtimes."""

    model_config = ConfigDict(frozen=True)

    supports_full_pipeline: bool = True
    supports_voice: bool = True
    supports_proactive: bool = True
    supports_multi_mode: bool = True
    available_runtimes: List[str] = Field(default_factory=list)
    max_concurrent_requests: int = 100


class AssistantIntegrationStatistics(BaseModel):
    """Immutable statistics metrics for the Assistant Integration Gateway."""

    model_config = ConfigDict(frozen=True)

    total_requests_handled: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    pipeline_executions: int = 0
    average_pipeline_latency_ms: float = 0.0
    registered_runtimes_count: int = 0
    uptime_seconds: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AssistantIntegrationHealth(BaseModel):
    """Immutable unified health report aggregating diagnostic metrics across all 12 runtimes."""

    model_config = ConfigDict(frozen=True)

    status: str = "READY"
    healthy: bool = True
    availability_percentage: float = 100.0
    subsystem_health: Dict[str, bool] = Field(default_factory=dict)
    detected_issues: List[str] = Field(default_factory=list)
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)
