"""API Request Routing Models (Phase 15.2).

Defines immutable Pydantic v2 domain models and enums for the provider-independent
API Request Routing Runtime, including routes, route groups, route contexts,
metadata, capabilities, health, statistics, and diagnostics.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional, Tuple

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


class RouteMethod(str, Enum):
    """HTTP methods supported for route registration."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    OPTIONS = "OPTIONS"
    HEAD = "HEAD"


class RouteState(str, Enum):
    """Operational states for an individual API route."""

    UNREGISTERED = "UNREGISTERED"
    REGISTERED = "REGISTERED"
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"


class RoutingRuntimeState(str, Enum):
    """Lifecycle states for the routing runtime."""

    UNINITIALIZED = "UNINITIALIZED"
    INITIALIZING = "INITIALIZING"
    READY = "READY"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"


class RouteMetadata(BaseModel):
    """Immutable metadata record attached to an API route."""

    model_config = ConfigDict(frozen=True)

    name: str = ""
    summary: str = ""
    description: str = ""
    tags: Tuple[str, ...] = Field(default_factory=tuple)
    deprecated: bool = False
    version: str = "1.0.0"
    attributes: Dict[str, Any] = Field(default_factory=dict)


class ApiRoute(BaseModel):
    """Immutable representation of an API route registration."""

    model_config = ConfigDict(frozen=True)

    route_id: str
    path: str
    method: RouteMethod = RouteMethod.GET
    group_name: str = "default"
    state: RouteState = RouteState.ACTIVE
    alias: Optional[str] = None
    metadata: RouteMetadata = Field(default_factory=RouteMetadata)
    handler_name: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RouteGroup(BaseModel):
    """Immutable logical grouping of API routes."""

    model_config = ConfigDict(frozen=True)

    group_id: str
    prefix: str = ""
    name: str = ""
    routes: Tuple[ApiRoute, ...] = Field(default_factory=tuple)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RouteContext(BaseModel):
    """Immutable execution context created during request dispatch preparation."""

    model_config = ConfigDict(frozen=True)

    context_id: str
    route: ApiRoute
    path_params: Dict[str, Any] = Field(default_factory=dict)
    query_params: Dict[str, Any] = Field(default_factory=dict)
    headers: Dict[str, str] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DispatchResult(BaseModel):
    """Immutable result object returned by the request dispatcher."""

    model_config = ConfigDict(frozen=True)

    is_success: bool = True
    route_id: str = ""
    path: str = ""
    method: RouteMethod = RouteMethod.GET
    context: Optional[RouteContext] = None
    error_message: Optional[str] = None
    dispatched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RouteCapabilities(BaseModel):
    """Immutable model declaring supported routing runtime capabilities."""

    model_config = ConfigDict(frozen=True)

    supports_alias: bool = True
    supports_groups: bool = True
    supports_dynamic_lookup: bool = True
    supports_metadata: bool = True
    supports_state_toggle: bool = True
    custom_capabilities: Dict[str, bool] = Field(default_factory=dict)


class RouteStatistics(BaseModel):
    """Immutable aggregate statistics and metrics for the routing runtime."""

    model_config = ConfigDict(frozen=True)

    total_routes: int = 0
    active_routes: int = 0
    disabled_routes: int = 0
    total_groups: int = 0
    total_dispatches: int = 0
    failed_dispatches: int = 0
    metrics: Dict[str, Any] = Field(default_factory=dict)


class RouteHealth(BaseModel):
    """Immutable health status evaluation of the routing runtime."""

    model_config = ConfigDict(frozen=True)

    is_healthy: bool = True
    state: RoutingRuntimeState = RoutingRuntimeState.UNINITIALIZED
    details: Dict[str, Any] = Field(default_factory=dict)
    issues: Tuple[str, ...] = Field(default_factory=tuple)
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RouteDiagnostics(BaseModel):
    """Immutable diagnostic information for troubleshooting and telemetry."""

    model_config = ConfigDict(frozen=True)

    state: RoutingRuntimeState = RoutingRuntimeState.UNINITIALIZED
    registered_routes_count: int = 0
    groups_count: int = 0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    thread_count: int = 0
    diagnostic_messages: Tuple[str, ...] = Field(default_factory=tuple)
    details: Dict[str, Any] = Field(default_factory=dict)
