"""Strongly typed Pydantic models for Runtime Validation & Resilience (Phase 10.7).

Defines enums and models for retry policies, timeout states, cancellation requests,
failure classification, recovery decisions, circuit breaker states, and runtime events.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


class FailureType(str, Enum):
    """Category classification of runtime failures."""

    TRANSIENT = "transient"
    PERMANENT = "permanent"
    VALIDATION = "validation"
    PROVIDER = "provider"
    TOOL = "tool"
    TIMEOUT = "timeout"
    CANCELLATION = "cancellation"
    UNKNOWN = "unknown"


class RecoveryAction(str, Enum):
    """Determined recovery action following a failure."""

    RETRY = "retry"
    CONTINUE = "continue"
    SKIP = "skip"
    ABORT = "abort"
    ESCALATE = "escalate"


class CircuitState(str, Enum):
    """Operational state of a CircuitBreaker."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class EventType(str, Enum):
    """Structured runtime event types for observability."""

    PLAN_STARTED = "plan_started"
    PLAN_COMPLETED = "plan_completed"
    STEP_STARTED = "step_started"
    STEP_COMPLETED = "step_completed"
    STEP_FAILED = "step_failed"
    RETRY_SCHEDULED = "retry_scheduled"
    TIMEOUT_OCCURRED = "timeout_occurred"
    CANCELLATION_REQUESTED = "cancellation_requested"
    CIRCUIT_OPENED = "circuit_opened"
    CIRCUIT_CLOSED = "circuit_closed"


class RetryStrategy(str, Enum):
    """Strategy algorithm for retry delay calculation."""

    FIXED = "fixed"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR = "linear"


class TimeoutStatus(str, Enum):
    """Status of tracked timeout states."""

    ACTIVE = "active"
    WARNING = "warning"
    EXPIRED = "expired"


class CancellationReason(str, Enum):
    """Reason for cancelling an operation."""

    MANUAL = "manual"
    TIMEOUT = "timeout"
    DEPENDENCY_FAILURE = "dependency_failure"
    SYSTEM_SHUTDOWN = "system_shutdown"


class RetryPolicy(BaseModel):
    """Configurable policy for retry calculations."""

    model_config = ConfigDict(frozen=True)

    max_retries: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 30.0
    backoff_multiplier: float = 2.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    jitter: bool = False


class RetryAttempt(BaseModel):
    """Record of an individual retry attempt calculation."""

    model_config = ConfigDict(frozen=True)

    attempt_number: int
    delay_seconds: float
    reason: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TimeoutPolicy(BaseModel):
    """Configurable timeout limits across execution scopes."""

    model_config = ConfigDict(frozen=True)

    execution_timeout_seconds: float = 300.0
    plan_timeout_seconds: float = 120.0
    step_timeout_seconds: float = 30.0


class TimeoutState(BaseModel):
    """Snapshot of a tracked timeout target."""

    model_config = ConfigDict(frozen=True)

    target_id: str
    start_time: float
    timeout_seconds: float
    elapsed_seconds: float
    remaining_seconds: float
    status: TimeoutStatus


class CancellationRequest(BaseModel):
    """Record of a cancellation request."""

    model_config = ConfigDict(frozen=True)

    request_id: str
    target_id: str
    requested_by: str
    reason: CancellationReason
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    details: Dict[str, Any] = Field(default_factory=dict)


class FailureInfo(BaseModel):
    """Structured failure classification details."""

    model_config = ConfigDict(frozen=True)

    failure_id: str
    failure_type: FailureType
    message: str
    exception_class: Optional[str] = None
    is_transient: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RecoveryDecision(BaseModel):
    """Decision output produced by RecoveryManager."""

    model_config = ConfigDict(frozen=True)

    decision_id: str
    action: RecoveryAction
    failure_info: FailureInfo
    retry_delay_seconds: float = 0.0
    reason: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CircuitBreakerState(BaseModel):
    """Snapshot state of a CircuitBreaker."""

    model_config = ConfigDict(frozen=True)

    circuit_id: str
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_timestamp: Optional[float] = None
    last_state_change: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RuntimeEvent(BaseModel):
    """Structured runtime event payload."""

    model_config = ConfigDict(frozen=True)

    event_id: str
    event_type: EventType
    source: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ResilienceContext(BaseModel):
    """Container context for resilience configurations."""

    model_config = ConfigDict(frozen=True)

    context_id: str
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy)
    timeout_policy: TimeoutPolicy = Field(default_factory=TimeoutPolicy)
    metadata: Dict[str, Any] = Field(default_factory=dict)
