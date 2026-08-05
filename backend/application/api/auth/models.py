"""API Authentication & Authorization Models (Phase 15.4).

Defines immutable Pydantic v2 domain models and enums for the provider-independent
API Authentication & Authorization Runtime, including identities, principals,
roles, claims, permissions, sessions, authorization decisions, capabilities,
health metrics, statistics, and diagnostics.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional, Tuple

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


class AuthenticationState(str, Enum):
    """States representing session or identity authentication status."""

    UNAUTHENTICATED = "UNAUTHENTICATED"
    AUTHENTICATED = "AUTHENTICATED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


class AuthorizationResult(str, Enum):
    """Results of authorization evaluation checks."""

    GRANTED = "GRANTED"
    DENIED = "DENIED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class AuthenticationRuntimeState(str, Enum):
    """Lifecycle states for the authentication runtime."""

    UNINITIALIZED = "UNINITIALIZED"
    INITIALIZING = "INITIALIZING"
    READY = "READY"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"


class Claim(BaseModel):
    """Immutable identity claim assertion."""

    model_config = ConfigDict(frozen=True)

    key: str
    value: str
    issuer: str = "local"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Permission(BaseModel):
    """Immutable permission assertion defining resource action authorization."""

    model_config = ConfigDict(frozen=True)

    permission_id: str
    name: str
    resource: str
    action: str
    description: str = ""


class Role(BaseModel):
    """Immutable RBAC role containing a collection of permissions."""

    model_config = ConfigDict(frozen=True)

    role_id: str
    name: str
    permissions: Tuple[Permission, ...] = Field(default_factory=tuple)
    description: str = ""


class Identity(BaseModel):
    """Immutable user or service identity representation."""

    model_config = ConfigDict(frozen=True)

    identity_id: str
    username: str
    display_name: str = ""
    email: Optional[str] = None
    is_active: bool = True
    roles: Tuple[Role, ...] = Field(default_factory=tuple)
    claims: Tuple[Claim, ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Principal(BaseModel):
    """Immutable security principal wrapping an identity for context propagation."""

    model_config = ConfigDict(frozen=True)

    principal_id: str
    identity: Identity
    active_roles: Tuple[str, ...] = Field(default_factory=tuple)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AuthenticationSession(BaseModel):
    """Immutable state snapshot of an active or terminated authentication session."""

    model_config = ConfigDict(frozen=True)

    session_id: str
    identity_id: str
    state: AuthenticationState = AuthenticationState.AUTHENTICATED
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    last_accessed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AuthorizationDecision(BaseModel):
    """Immutable authorization evaluation decision object."""

    model_config = ConfigDict(frozen=True)

    result: AuthorizationResult = AuthorizationResult.DENIED
    identity_id: str = ""
    resource: str = ""
    action: str = ""
    reason: str = ""
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AuthenticationContext(BaseModel):
    """Immutable security context passed across execution stages."""

    model_config = ConfigDict(frozen=True)

    context_id: str
    principal: Optional[Principal] = None
    session: Optional[AuthenticationSession] = None
    is_authenticated: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AuthenticationCapabilities(BaseModel):
    """Immutable model declaring supported authentication & authorization capabilities."""

    model_config = ConfigDict(frozen=True)

    supports_identity_management: bool = True
    supports_session_management: bool = True
    supports_role_based_access: bool = True
    supports_claim_based_access: bool = True
    supports_permission_evaluation: bool = True
    custom_capabilities: Dict[str, bool] = Field(default_factory=dict)


class AuthenticationStatistics(BaseModel):
    """Immutable aggregate metrics and statistics for the auth runtime."""

    model_config = ConfigDict(frozen=True)

    total_identities: int = 0
    active_sessions: int = 0
    expired_sessions: int = 0
    revoked_sessions: int = 0
    granted_authorizations: int = 0
    denied_authorizations: int = 0
    metrics: Dict[str, Any] = Field(default_factory=dict)


class AuthenticationHealth(BaseModel):
    """Immutable health status evaluation of the authentication runtime."""

    model_config = ConfigDict(frozen=True)

    is_healthy: bool = True
    state: AuthenticationRuntimeState = AuthenticationRuntimeState.UNINITIALIZED
    details: Dict[str, Any] = Field(default_factory=dict)
    issues: Tuple[str, ...] = Field(default_factory=tuple)
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AuthenticationDiagnostics(BaseModel):
    """Immutable diagnostic information for troubleshooting and telemetry."""

    model_config = ConfigDict(frozen=True)

    state: AuthenticationRuntimeState = AuthenticationRuntimeState.UNINITIALIZED
    identities_count: int = 0
    active_sessions_count: int = 0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    thread_count: int = 0
    diagnostic_messages: Tuple[str, ...] = Field(default_factory=tuple)
    details: Dict[str, Any] = Field(default_factory=dict)
