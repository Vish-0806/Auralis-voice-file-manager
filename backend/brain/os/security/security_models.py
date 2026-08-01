"""Security Subsystem Domain Models for Auralis (Phase 11.8).

Defines immutable Pydantic v2 models and enums representing security requests,
permission validation results, risk assessments, confirmation requests, security decisions,
audit log events, performance statistics, capabilities, health status, and runtime state.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


class PermissionLevel(str, Enum):
    """Permission access levels."""

    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"
    DENIED = "denied"


class SecurityDecisionType(str, Enum):
    """Canonical security decision classifications."""

    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_CONFIRMATION = "require_confirmation"
    READ_ONLY = "read_only"
    SANDBOX_ONLY = "sandbox_only"


class RiskLevel(str, Enum):
    """Risk severity classifications."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ConfirmationPolicy(str, Enum):
    """User confirmation enforcement policies."""

    ALWAYS = "always"
    NEVER = "never"
    DANGEROUS_ONLY = "dangerous_only"
    ADMIN_ONLY = "admin_only"
    DESTRUCTIVE_ONLY = "destructive_only"


class AuditSeverity(str, Enum):
    """Audit event log severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class OperationCategory(str, Enum):
    """OS subsystem operation categories."""

    FILESYSTEM = "filesystem"
    PROCESS = "process"
    APPLICATION = "application"
    DESKTOP = "desktop"
    WINDOW = "window"
    DEVICE = "device"
    SYSTEM = "system"


class SecurityContext(BaseModel):
    """Immutable execution context details."""

    model_config = ConfigDict(frozen=True)

    user_id: str = "current_user"
    is_admin: bool = False
    session_id: str = "console"
    client_ip: str = "127.0.0.1"
    environment: str = "production"


class SecurityRequest(BaseModel):
    """Immutable security decision request specification."""

    model_config = ConfigDict(frozen=True)

    request_id: str = ""
    category: OperationCategory = OperationCategory.SYSTEM
    operation: str = ""
    target_resource: str = ""
    requested_permission: PermissionLevel = PermissionLevel.READ
    context: SecurityContext = Field(default_factory=SecurityContext)
    parameters: Dict[str, Any] = Field(default_factory=dict)


class PermissionResult(BaseModel):
    """Immutable result of permission validation."""

    model_config = ConfigDict(frozen=True)

    granted: bool = True
    permission: PermissionLevel = PermissionLevel.READ
    required_privilege: str = ""
    is_admin_required: bool = False
    reason: str = "Permission granted"


class RiskAssessment(BaseModel):
    """Immutable risk score and factor classification."""

    model_config = ConfigDict(frozen=True)

    risk_level: RiskLevel = RiskLevel.LOW
    risk_score: float = 0.1
    factors: List[str] = Field(default_factory=list)
    is_dangerous: bool = False
    is_destructive: bool = False


class ConfirmationRequest(BaseModel):
    """Immutable user confirmation specification."""

    model_config = ConfigDict(frozen=True)

    confirmation_id: str = ""
    request_id: str = ""
    prompt_message: str = ""
    policy: ConfirmationPolicy = ConfirmationPolicy.DANGEROUS_ONLY
    risk_level: RiskLevel = RiskLevel.LOW
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SecurityDecision(BaseModel):
    """Immutable security evaluation decision result."""

    model_config = ConfigDict(frozen=True)

    request_id: str = ""
    decision_type: SecurityDecisionType = SecurityDecisionType.ALLOW
    permission_result: PermissionResult = Field(default_factory=PermissionResult)
    risk_assessment: RiskAssessment = Field(default_factory=RiskAssessment)
    confirmation_request: Optional[ConfirmationRequest] = None
    reason: str = "Operation permitted"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AuditEvent(BaseModel):
    """Immutable audit trail log record."""

    model_config = ConfigDict(frozen=True)

    event_id: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    request_id: str = ""
    category: OperationCategory = OperationCategory.SYSTEM
    operation: str = ""
    target_resource: str = ""
    decision_type: SecurityDecisionType = SecurityDecisionType.ALLOW
    risk_level: RiskLevel = RiskLevel.LOW
    severity: AuditSeverity = AuditSeverity.INFO
    reason: str = ""


class SecurityCapabilities(BaseModel):
    """Immutable security subsystem capabilities report."""

    model_config = ConfigDict(frozen=True)

    supports_risk_analysis: bool = True
    supports_audit_logging: bool = True
    supports_policy_evaluation: bool = True
    supports_confirmation: bool = True


class SecurityStatistics(BaseModel):
    """Immutable performance statistics for Security Subsystem."""

    model_config = ConfigDict(frozen=True)

    total_requests_evaluated: int = 0
    allowed_requests: int = 0
    denied_requests: int = 0
    confirmation_requests: int = 0
    audit_events_count: int = 0


class SecurityHealth(BaseModel):
    """Immutable health status of Security Subsystem services."""

    model_config = ConfigDict(frozen=True)

    healthy: bool = True
    status: str = "READY"
    audit_log_size: int = 0
    total_evaluations: int = 0
    uptime_seconds: float = 0.0
    details: Dict[str, Any] = Field(default_factory=dict)


class SecurityRuntimeStatus(BaseModel):
    """Immutable overall Security Runtime status report."""

    model_config = ConfigDict(frozen=True)

    state: str = "Initializing"
    healthy: bool = True
    provider_registered: bool = False
    total_evaluations: int = 0
    denied_evaluations: int = 0
    uptime_seconds: float = 0.0
