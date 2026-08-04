"""Dependency Injection Domain Models (Phase 14.2.3).

Defines immutable Pydantic v2 domain models and enums representing service lifetimes,
container states, descriptors, registrations, dependency graph nodes, capabilities,
health metrics, statistics, diagnostics, configuration, and execution context.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional, Tuple
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


class ServiceLifetime(str, Enum):
    """Lifetime scopes for registered services."""

    SINGLETON = "SINGLETON"
    TRANSIENT = "TRANSIENT"
    SCOPED = "SCOPED"


class ContainerState(str, Enum):
    """Lifecycle states for the dependency container."""

    UNINITIALIZED = "UNINITIALIZED"
    INITIALIZED = "INITIALIZED"
    READY = "READY"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"


class ServiceDescriptorModel(BaseModel):
    """Immutable model representing service descriptor metadata."""

    model_config = ConfigDict(frozen=True)

    descriptor_id: str = ""
    service_type: str
    implementation_type: Optional[str] = None
    lifetime: ServiceLifetime = ServiceLifetime.SINGLETON
    has_factory: bool = False
    has_instance: bool = False
    tags: Tuple[str, ...] = Field(default_factory=tuple)
    aliases: Tuple[str, ...] = Field(default_factory=tuple)
    registered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ServiceRegistration(BaseModel):
    """Immutable metadata record for a service registration."""

    model_config = ConfigDict(frozen=True)

    service_name: str
    descriptor: ServiceDescriptorModel
    registered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DependencyGraphNode(BaseModel):
    """Immutable node representation within the dependency graph."""

    model_config = ConfigDict(frozen=True)

    node_id: str
    service_type: str
    dependencies: Tuple[str, ...] = Field(default_factory=tuple)
    lifetime: ServiceLifetime = ServiceLifetime.SINGLETON


class ContainerCapabilities(BaseModel):
    """Immutable model declaring supported container capabilities."""

    model_config = ConfigDict(frozen=True)

    supports_singleton: bool = True
    supports_transient: bool = True
    supports_scoped: bool = True
    supports_factories: bool = True
    supports_instances: bool = True
    supports_aliases: bool = True
    supports_tags: bool = True
    supports_replacement: bool = True
    custom_capabilities: Dict[str, bool] = Field(default_factory=dict)


class ContainerStatistics(BaseModel):
    """Immutable model containing container statistics and metrics."""

    model_config = ConfigDict(frozen=True)

    registered_services_count: int = 0
    resolved_services_count: int = 0
    active_scopes_count: int = 0
    metrics: Dict[str, float] = Field(default_factory=dict)


class ContainerDiagnostics(BaseModel):
    """Immutable model containing detailed container resolution diagnostics."""

    model_config = ConfigDict(frozen=True)

    registered_services_count: int = 0
    resolved_services_count: int = 0
    cached_singleton_count: int = 0
    active_resolution_stack: Tuple[str, ...] = Field(default_factory=tuple)
    failed_resolutions_count: int = 0
    circular_dependency_count: int = 0
    metrics: Dict[str, float] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ContainerHealth(BaseModel):
    """Immutable health assessment model for the dependency container."""

    model_config = ConfigDict(frozen=True)

    is_healthy: bool = True
    state: ContainerState = ContainerState.UNINITIALIZED
    issues: Tuple[str, ...] = Field(default_factory=tuple)
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ContainerConfiguration(BaseModel):
    """Immutable configuration settings for the dependency container."""

    model_config = ConfigDict(frozen=True)

    container_name: str = "AuralisDIContainer"
    strict_resolution: bool = True
    settings: Dict[str, Any] = Field(default_factory=dict)


class ContainerContext(BaseModel):
    """Immutable execution context snapshot for the container."""

    model_config = ConfigDict(frozen=True)

    container_id: str = ""
    environment: str = "production"
    context_data: Dict[str, Any] = Field(default_factory=dict)
