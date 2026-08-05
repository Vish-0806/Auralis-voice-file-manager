"""API Versioning & Documentation Models (Phase 15.6).

Defines immutable Pydantic v2 domain models and enums for the provider-independent
API Versioning & Documentation Runtime, including versions, releases, endpoint versions,
compatibility reports, deprecation notices, documentation pages/sections/exports,
capabilities, health metrics, statistics, and diagnostics.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional, Tuple

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


class ReleaseChannel(str, Enum):
    """Distribution channels for API releases."""

    ALPHA = "ALPHA"
    BETA = "BETA"
    RC = "RC"
    STABLE = "STABLE"
    LTS = "LTS"


class DeprecationState(str, Enum):
    """Lifecycle deprecation states for versions and endpoints."""

    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"
    REMOVED = "REMOVED"


class VersionRuntimeState(str, Enum):
    """Lifecycle states for the versioning runtime."""

    UNINITIALIZED = "UNINITIALIZED"
    INITIALIZING = "INITIALIZING"
    READY = "READY"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"


class DeprecationNotice(BaseModel):
    """Immutable deprecation warning notice."""

    model_config = ConfigDict(frozen=True)

    notice_id: str
    deprecated_version: str
    sunset_date: Optional[str] = None
    replacement: Optional[str] = None
    reason: str = ""
    state: DeprecationState = DeprecationState.DEPRECATED


class EndpointVersion(BaseModel):
    """Immutable version definition for an individual API endpoint."""

    model_config = ConfigDict(frozen=True)

    endpoint_id: str
    path: str
    version: str
    state: DeprecationState = DeprecationState.ACTIVE
    deprecation_notice: Optional[DeprecationNotice] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ApiRelease(BaseModel):
    """Immutable release metadata for an API version."""

    model_config = ConfigDict(frozen=True)

    release_id: str
    version: str
    channel: ReleaseChannel = ReleaseChannel.STABLE
    release_notes: str = ""
    released_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ApiVersion(BaseModel):
    """Immutable representation of a top-level API version definition."""

    model_config = ConfigDict(frozen=True)

    version_id: str
    version_number: str
    channel: ReleaseChannel = ReleaseChannel.STABLE
    state: DeprecationState = DeprecationState.ACTIVE
    endpoints: Tuple[EndpointVersion, ...] = Field(default_factory=tuple)
    release_info: Optional[ApiRelease] = None
    deprecation_notice: Optional[DeprecationNotice] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CompatibilityReport(BaseModel):
    """Immutable compatibility evaluation report between two API versions."""

    model_config = ConfigDict(frozen=True)

    is_compatible: bool = True
    base_version: str = ""
    target_version: str = ""
    breaking_changes: Tuple[str, ...] = Field(default_factory=tuple)
    warnings: Tuple[str, ...] = Field(default_factory=tuple)
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DocumentationSection(BaseModel):
    """Immutable section of a documentation page."""

    model_config = ConfigDict(frozen=True)

    section_id: str
    title: str
    content: str = ""
    subsections: Tuple["DocumentationSection", ...] = Field(default_factory=tuple)


class DocumentationPage(BaseModel):
    """Immutable documentation page record."""

    model_config = ConfigDict(frozen=True)

    page_id: str
    title: str
    version: str = "1.0.0"
    sections: Tuple[DocumentationSection, ...] = Field(default_factory=tuple)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentationExport(BaseModel):
    """Immutable export result of generated documentation."""

    model_config = ConfigDict(frozen=True)

    export_id: str
    format: str = "markdown"
    content: str = ""
    exported_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class VersionCapabilities(BaseModel):
    """Immutable model declaring supported versioning runtime capabilities."""

    model_config = ConfigDict(frozen=True)

    supports_version_registration: bool = True
    supports_release_channels: bool = True
    supports_compatibility_evaluation: bool = True
    supports_deprecation_notices: bool = True
    supports_documentation_export: bool = True
    custom_capabilities: Dict[str, bool] = Field(default_factory=dict)


class VersionStatistics(BaseModel):
    """Immutable aggregate metrics and statistics for the versioning runtime."""

    model_config = ConfigDict(frozen=True)

    total_versions: int = 0
    stable_versions: int = 0
    deprecated_versions: int = 0
    total_documentation_pages: int = 0
    total_compatibility_checks: int = 0
    metrics: Dict[str, Any] = Field(default_factory=dict)


class VersionHealth(BaseModel):
    """Immutable health status evaluation of the versioning runtime."""

    model_config = ConfigDict(frozen=True)

    is_healthy: bool = True
    state: VersionRuntimeState = VersionRuntimeState.UNINITIALIZED
    details: Dict[str, Any] = Field(default_factory=dict)
    issues: Tuple[str, ...] = Field(default_factory=tuple)
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class VersionDiagnostics(BaseModel):
    """Immutable diagnostic information for troubleshooting and telemetry."""

    model_config = ConfigDict(frozen=True)

    state: VersionRuntimeState = VersionRuntimeState.UNINITIALIZED
    registered_versions_count: int = 0
    documentation_pages_count: int = 0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    thread_count: int = 0
    diagnostic_messages: Tuple[str, ...] = Field(default_factory=tuple)
    details: Dict[str, Any] = Field(default_factory=dict)
