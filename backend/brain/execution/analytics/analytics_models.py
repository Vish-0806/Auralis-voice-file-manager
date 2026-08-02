"""Domain data models and enumerations for the Auralis Execution Analytics & Observability Runtime (Phase 12.7).

Defines immutable Pydantic v2 models representing execution metrics, distributed traces,
audit records, summary reports, statistics, health reports, and analytics context.
"""

from datetime import datetime, timezone
from enum import Enum
import uuid
from typing import Any, Dict, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


class MetricType(str, Enum):
    """Types of metrics collected."""

    COUNTER = "COUNTER"
    GAUGE = "GAUGE"
    HISTOGRAM = "HISTOGRAM"
    TIMER = "TIMER"


class TraceLevel(str, Enum):
    """Severity levels for execution traces."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AuditSeverity(str, Enum):
    """Severity levels for audit records."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ExecutionOutcome(str, Enum):
    """Execution outcome status states for audit tracking."""

    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    ABORTED = "ABORTED"
    CANCELLED = "CANCELLED"
    TIMEOUT = "TIMEOUT"


class AnalyticsStatus(str, Enum):
    """Lifecycle status states for the analytics runtime."""

    INACTIVE = "INACTIVE"
    RECORDING = "RECORDING"
    READY = "READY"
    DEGRADED = "DEGRADED"
    ERROR = "ERROR"


class ExecutionMetric(BaseModel):
    """Immutable model representing a single collected metric point."""

    model_config = ConfigDict(frozen=True)

    metric_id: str = Field(default_factory=lambda: f"met-{uuid.uuid4().hex[:8]}")
    name: str = ""
    metric_type: MetricType = MetricType.COUNTER
    value: float = 0.0
    unit: str = ""
    tags: Dict[str, str] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ExecutionTrace(BaseModel):
    """Immutable model representing a distributed trace span."""

    model_config = ConfigDict(frozen=True)

    trace_id: str = Field(default_factory=lambda: f"trc-{uuid.uuid4().hex[:8]}")
    correlation_id: str = Field(default_factory=lambda: f"corr-{uuid.uuid4().hex[:8]}")
    span_name: str = ""
    parent_span_id: Optional[str] = None
    level: TraceLevel = TraceLevel.INFO
    duration_ms: float = 0.0
    attributes: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ExecutionAuditRecord(BaseModel):
    """Immutable model representing an execution audit trail record."""

    model_config = ConfigDict(frozen=True)

    audit_id: str = Field(default_factory=lambda: f"audit-{uuid.uuid4().hex[:8]}")
    event_type: str = "EXECUTION_EVENT"
    subsystem: str = "EXECUTION"
    action: str = ""
    severity: AuditSeverity = AuditSeverity.MEDIUM
    outcome: ExecutionOutcome = ExecutionOutcome.SUCCESS
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ExecutionSummary(BaseModel):
    """Immutable model representing an aggregated metrics summary for a period."""

    model_config = ConfigDict(frozen=True)

    summary_id: str = Field(default_factory=lambda: f"sum-{uuid.uuid4().hex[:8]}")
    total_executions: int = 0
    successful_count: int = 0
    failed_count: int = 0
    avg_duration_ms: float = 0.0
    period_start: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    period_end: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExecutionStatistics(BaseModel):
    """Immutable model representing overall diagnostic statistics of the Analytics subsystem."""

    model_config = ConfigDict(frozen=True)

    total_metrics_collected: int = 0
    total_traces_recorded: int = 0
    total_audit_records: int = 0
    average_execution_time_ms: float = 0.0
    success_rate_percentage: float = 100.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExecutionHealth(BaseModel):
    """Immutable model representing health status of the Analytics subsystem."""

    model_config = ConfigDict(frozen=True)

    status: str = "READY"
    healthy: bool = True
    components: Dict[str, bool] = Field(default_factory=dict)
    statistics: Dict[str, Any] = Field(default_factory=dict)
    detected_issues: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AnalyticsContext(BaseModel):
    """Immutable context tracking active span stack and correlation IDs."""

    model_config = ConfigDict(frozen=True)

    context_id: str = Field(default_factory=lambda: f"actx-{uuid.uuid4().hex[:8]}")
    correlation_id: str = Field(default_factory=lambda: f"corr-{uuid.uuid4().hex[:8]}")
    active_spans: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
