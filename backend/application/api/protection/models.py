"""API Protection & Rate Limiting Models (Phase 15.8).

Defines immutable Pydantic v2 domain models and enums for the provider-independent
API Protection & Rate Limiting Runtime, including rules, quota windows, token buckets,
decisions, policies, violation records, capabilities, health, statistics, and diagnostics.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional, Tuple

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


class RateLimitAlgorithm(str, Enum):
    """Algorithms for rate limit enforcement."""

    FIXED_WINDOW = "FIXED_WINDOW"
    SLIDING_WINDOW = "SLIDING_WINDOW"
    TOKEN_BUCKET = "TOKEN_BUCKET"
    LEAKY_BUCKET = "LEAKY_BUCKET"


class ProtectionDecision(str, Enum):
    """Action decision outputs from API policy evaluation."""

    ALLOW = "ALLOW"
    THROTTLE = "THROTTLE"
    REJECT = "REJECT"


class ProtectionRuntimeState(str, Enum):
    """Lifecycle states for the protection runtime."""

    UNINITIALIZED = "UNINITIALIZED"
    INITIALIZING = "INITIALIZING"
    READY = "READY"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"


class ClientIdentity(BaseModel):
    """Immutable client identification details for rate limiting and policy scoping."""

    model_config = ConfigDict(frozen=True)

    client_id: str
    client_ip: Optional[str] = None
    api_key: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RateLimitRule(BaseModel):
    """Immutable rate limiting rule configuration."""

    model_config = ConfigDict(frozen=True)

    rule_id: str
    name: str
    max_requests: int
    window_seconds: int = 60
    algorithm: RateLimitAlgorithm = RateLimitAlgorithm.SLIDING_WINDOW
    burst_capacity: int = 0
    refill_rate: float = 0.0
    description: str = ""


class QuotaWindow(BaseModel):
    """Immutable quota window tracking request counters for a client and rule."""

    model_config = ConfigDict(frozen=True)

    window_id: str
    client_id: str
    rule_id: str
    current_count: int = 0
    reset_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TokenBucket(BaseModel):
    """Immutable token bucket state tracking available tokens for a client."""

    model_config = ConfigDict(frozen=True)

    bucket_id: str
    client_id: str
    capacity: int
    current_tokens: float
    refill_rate: float
    last_refill_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RateLimitDecision(BaseModel):
    """Immutable evaluation result produced by a rate limit check."""

    model_config = ConfigDict(frozen=True)

    decision_id: str
    is_allowed: bool = True
    remaining_tokens: int = 0
    retry_after_seconds: float = 0.0
    reset_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    rule_id: str = ""


class ApiPolicy(BaseModel):
    """Immutable API security and traffic management policy."""

    model_config = ConfigDict(frozen=True)

    policy_id: str
    name: str
    priority: int = 100
    decision: ProtectionDecision = ProtectionDecision.ALLOW
    rules: Tuple[RateLimitRule, ...] = Field(default_factory=tuple)
    is_enabled: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PolicyDecision(BaseModel):
    """Immutable decision record produced by evaluating an ApiPolicy against a request context."""

    model_config = ConfigDict(frozen=True)

    decision_id: str
    client_id: str
    policy_id: Optional[str] = None
    action: ProtectionDecision = ProtectionDecision.ALLOW
    reason: str = "Default allow"
    rate_limit_decision: Optional[RateLimitDecision] = None
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ViolationRecord(BaseModel):
    """Immutable record of an API policy or rate limit violation."""

    model_config = ConfigDict(frozen=True)

    violation_id: str
    client_id: str
    rule_id: str
    reason: str
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    cooldown_until: Optional[datetime] = None


class ProtectionContext(BaseModel):
    """Immutable evaluation context for an incoming client request."""

    model_config = ConfigDict(frozen=True)

    context_id: str
    client: ClientIdentity
    path: str = ""
    method: str = "GET"
    attributes: Dict[str, Any] = Field(default_factory=dict)


class ProtectionCapabilities(BaseModel):
    """Immutable model declaring supported protection runtime capabilities."""

    model_config = ConfigDict(frozen=True)

    supports_rate_limiting: bool = True
    supports_sliding_window: bool = True
    supports_token_bucket: bool = True
    supports_policy_evaluation: bool = True
    supports_violation_tracking: bool = True
    custom_capabilities: Dict[str, bool] = Field(default_factory=dict)


class ProtectionStatistics(BaseModel):
    """Immutable aggregate metrics and statistics for the protection runtime."""

    model_config = ConfigDict(frozen=True)

    total_rules: int = 0
    total_policies: int = 0
    total_evaluations: int = 0
    allowed_requests: int = 0
    throttled_requests: int = 0
    rejected_requests: int = 0
    total_violations: int = 0
    metrics: Dict[str, Any] = Field(default_factory=dict)


class ProtectionHealth(BaseModel):
    """Immutable health status evaluation of the protection runtime."""

    model_config = ConfigDict(frozen=True)

    is_healthy: bool = True
    state: ProtectionRuntimeState = ProtectionRuntimeState.UNINITIALIZED
    details: Dict[str, Any] = Field(default_factory=dict)
    issues: Tuple[str, ...] = Field(default_factory=tuple)
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProtectionDiagnostics(BaseModel):
    """Immutable diagnostic information for troubleshooting and telemetry."""

    model_config = ConfigDict(frozen=True)

    state: ProtectionRuntimeState = ProtectionRuntimeState.UNINITIALIZED
    registered_rules_count: int = 0
    registered_policies_count: int = 0
    active_violations_count: int = 0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    thread_count: int = 0
    diagnostic_messages: Tuple[str, ...] = Field(default_factory=tuple)
    details: Dict[str, Any] = Field(default_factory=dict)
