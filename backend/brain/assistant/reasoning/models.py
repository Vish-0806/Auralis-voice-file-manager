"""Decision & Reasoning Coordinator Data Models for Auralis (Phase 13.4).

Defines immutable Pydantic v2 domain models and enums representing decision actions,
priorities, outcomes, candidates, contexts, requests, results, policies, metadata,
statistics, and health status using ConfigDict(frozen=True).
"""

from datetime import datetime, timezone
from enum import Enum
import uuid
from typing import Any, Dict, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


class DecisionAction(str, Enum):
    """Routing actions decided by the Reasoning Coordinator."""

    DIRECT_EXECUTION = "DIRECT_EXECUTION"
    PLANNER_REQUIRED = "PLANNER_REQUIRED"
    AI_REQUIRED = "AI_REQUIRED"
    CLARIFICATION_REQUIRED = "CLARIFICATION_REQUIRED"
    CONFIRMATION_REQUIRED = "CONFIRMATION_REQUIRED"
    DELEGATE = "DELEGATE"
    NO_ACTION = "NO_ACTION"
    REJECT = "REJECT"


class DecisionPriority(str, Enum):
    """Priority levels assigned to decision evaluations."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    IMMEDIATE = "IMMEDIATE"


class DecisionOutcome(str, Enum):
    """Execution status or resolution outcome of a decision decision."""

    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    MODIFIED = "MODIFIED"
    REJECTED = "REJECTED"
    OVERRIDDEN = "OVERRIDDEN"


class DecisionMetadata(BaseModel):
    """Immutable metadata accompanying decision evaluations."""

    model_config = ConfigDict(frozen=True)

    source: str = "AssistantReasoningCoordinator"
    tags: List[str] = Field(default_factory=list)
    custom_attributes: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DecisionPolicy(BaseModel):
    """Immutable policy configuration for deterministic decision routing."""

    model_config = ConfigDict(frozen=True)

    policy_id: str = "default_routing_policy"
    strict_execution_checks: bool = True
    auto_ai_fallback: bool = True
    min_execution_readiness_score: float = 0.7
    default_priority: DecisionPriority = DecisionPriority.MEDIUM
    rules: Dict[str, Any] = Field(default_factory=dict)


class DecisionContext(BaseModel):
    """Immutable snapshot of environmental and runtime context provided to the decision engine."""

    model_config = ConfigDict(frozen=True)

    session_id: Optional[str] = None
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None
    dialogue_status: Optional[str] = None
    execution_ready: bool = False
    ai_required: bool = False
    active_intent: Optional[str] = None
    context_variables: Dict[str, Any] = Field(default_factory=dict)
    metadata: DecisionMetadata = Field(default_factory=DecisionMetadata)


class DecisionRequest(BaseModel):
    """Immutable request structure supplied to the Reasoning Coordinator."""

    model_config = ConfigDict(frozen=True)

    request_id: str = Field(default_factory=lambda: f"dreq-{uuid.uuid4().hex[:8]}")
    user_prompt: str = ""
    session_id: Optional[str] = None
    context: DecisionContext = Field(default_factory=DecisionContext)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DecisionCandidate(BaseModel):
    """Immutable candidate action option evaluated during conflict resolution."""

    model_config = ConfigDict(frozen=True)

    candidate_id: str = Field(default_factory=lambda: f"cand-{uuid.uuid4().hex[:6]}")
    action: DecisionAction = DecisionAction.NO_ACTION
    score: float = Field(default=1.0, ge=0.0, le=1.0)
    priority: DecisionPriority = DecisionPriority.MEDIUM
    reason: str = "Candidate generated"
    requires_ai: bool = False
    requires_confirmation: bool = False
    requires_clarification: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DecisionResult(BaseModel):
    """Immutable final decision report output by the Reasoning Coordinator."""

    model_config = ConfigDict(frozen=True)

    decision_id: str = Field(default_factory=lambda: f"dec-{uuid.uuid4().hex[:8]}")
    request_id: str = ""
    recommended_action: DecisionAction = DecisionAction.NO_ACTION
    priority: DecisionPriority = DecisionPriority.MEDIUM
    outcome: DecisionOutcome = DecisionOutcome.ACCEPTED
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    selected_candidate: Optional[DecisionCandidate] = None
    evaluated_candidates: List[DecisionCandidate] = Field(default_factory=list)
    requires_ai: bool = False
    requires_planner: bool = False
    requires_clarification: bool = False
    requires_confirmation: bool = False
    clarification_prompt: Optional[str] = None
    confirmation_prompt: Optional[str] = None
    reason: str = "Decision completed"
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DecisionStatistics(BaseModel):
    """Immutable metrics and statistics of the Reasoning Coordinator."""

    model_config = ConfigDict(frozen=True)

    total_requests_evaluated: int = 0
    direct_executions_routed: int = 0
    ai_required_routed: int = 0
    planner_required_routed: int = 0
    clarifications_routed: int = 0
    confirmations_routed: int = 0
    rejections_routed: int = 0
    average_evaluation_latency_ms: float = 0.0
    uptime_seconds: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DecisionHealth(BaseModel):
    """Immutable diagnostic health status of the Reasoning Coordinator."""

    model_config = ConfigDict(frozen=True)

    status: str = "READY"
    healthy: bool = True
    subsystems: Dict[str, bool] = Field(default_factory=dict)
    statistics: Dict[str, Any] = Field(default_factory=dict)
    detected_issues: List[str] = Field(default_factory=list)
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)
