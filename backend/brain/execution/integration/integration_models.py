"""Domain data models and enumerations for the Auralis Execution Runtime Integration (Phase 12.9).

Defines immutable Pydantic v2 models representing capabilities, integration requests,
integration responses, pipeline stage records, statistics, and health reports.
"""

from datetime import datetime, timezone
from enum import Enum
import uuid
from typing import Any, Dict, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


class ExecutionStage(str, Enum):
    """Execution stages in the integrated pipeline."""

    INTENT_RESOLUTION = "INTENT_RESOLUTION"
    SECURITY_CHECK = "SECURITY_CHECK"
    ORCHESTRATION = "ORCHESTRATION"
    WORKFLOW_SCHEDULING = "WORKFLOW_SCHEDULING"
    TASK_DISPATCH = "TASK_DISPATCH"
    AUTOMATION_EVALUATION = "AUTOMATION_EVALUATION"
    RECOVERY_CHECKPOINT = "RECOVERY_CHECKPOINT"
    ANALYTICS_RECORDING = "ANALYTICS_RECORDING"


class ExecutionStatus(str, Enum):
    """Status states for integrated execution requests."""

    RECEIVED = "RECEIVED"
    ROUTED = "ROUTED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    RECOVERED = "RECOVERED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"


class ExecutionTarget(str, Enum):
    """Subsystem targets for routed execution requests."""

    INTENT_ENGINE = "INTENT_ENGINE"
    COMMAND_ORCHESTRATOR = "COMMAND_ORCHESTRATOR"
    WORKFLOW_ENGINE = "WORKFLOW_ENGINE"
    TASK_RUNTIME = "TASK_RUNTIME"
    AUTOMATION_RUNTIME = "AUTOMATION_RUNTIME"


class ExecutionPriority(str, Enum):
    """Priority levels for integrated execution requests."""

    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ExecutionCapability(BaseModel):
    """Immutable model representing a registered execution capability."""

    model_config = ConfigDict(frozen=True)

    capability_id: str = Field(default_factory=lambda: f"cap-{uuid.uuid4().hex[:8]}")
    name: str = ""
    target: ExecutionTarget = ExecutionTarget.COMMAND_ORCHESTRATOR
    enabled: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IntegrationRequest(BaseModel):
    """Immutable model representing an incoming integrated execution request."""

    model_config = ConfigDict(frozen=True)

    request_id: str = Field(default_factory=lambda: f"req-{uuid.uuid4().hex[:8]}")
    user_input: str = ""
    context_data: Dict[str, Any] = Field(default_factory=dict)
    priority: ExecutionPriority = ExecutionPriority.NORMAL
    correlation_id: str = Field(default_factory=lambda: f"corr-{uuid.uuid4().hex[:8]}")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class IntegrationResponse(BaseModel):
    """Immutable model representing the final outcome of an integrated execution request."""

    model_config = ConfigDict(frozen=True)

    request_id: str = ""
    execution_id: str = Field(default_factory=lambda: f"exec-{uuid.uuid4().hex[:8]}")
    status: ExecutionStatus = ExecutionStatus.COMPLETED
    target: ExecutionTarget = ExecutionTarget.COMMAND_ORCHESTRATOR
    result_data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PipelineStageRecord(BaseModel):
    """Immutable model representing a completed stage in the execution pipeline."""

    model_config = ConfigDict(frozen=True)

    stage_id: str = Field(default_factory=lambda: f"stg-{uuid.uuid4().hex[:8]}")
    stage_name: ExecutionStage = ExecutionStage.ORCHESTRATION
    status: str = "COMPLETED"
    duration_ms: float = 0.0
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class IntegrationStatistics(BaseModel):
    """Immutable model representing aggregate diagnostic statistics for the Integration Runtime."""

    model_config = ConfigDict(frozen=True)

    total_requests: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    recovered_executions: int = 0
    average_latency_ms: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IntegrationHealth(BaseModel):
    """Immutable model representing health status of the Integration Runtime."""

    model_config = ConfigDict(frozen=True)

    status: str = "READY"
    healthy: bool = True
    subsystems: Dict[str, bool] = Field(default_factory=dict)
    statistics: Dict[str, Any] = Field(default_factory=dict)
    detected_issues: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
