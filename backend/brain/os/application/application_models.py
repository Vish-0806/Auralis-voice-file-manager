"""Application Runtime Domain Models for Auralis (Phase 11.3).

Defines immutable Pydantic v2 models and enums representing desktop applications,
installed apps, running processes, launch requests/results, registry entries,
performance statistics, capabilities, health status, and runtime state.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


class ApplicationState(str, Enum):
    """Lifecycle state of an application."""

    INSTALLED = "installed"
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    UNKNOWN = "unknown"


class LaunchMode(str, Enum):
    """Launch display modes for application startup."""

    NORMAL = "normal"
    MINIMIZED = "minimized"
    MAXIMIZED = "maximized"
    BACKGROUND = "background"


class VisibilityMode(str, Enum):
    """Visibility classification for application execution."""

    VISIBLE = "visible"
    HIDDEN = "hidden"
    SYSTEM = "system"


class ApplicationInfo(BaseModel):
    """Immutable application metadata."""

    model_config = ConfigDict(frozen=True)

    app_id: str = ""
    name: str = ""
    display_name: str = ""
    executable_path: str = ""
    version: str = "1.0.0"
    publisher: str = ""
    category: str = "General"
    aliases: List[str] = Field(default_factory=list)
    description: str = ""


class InstalledApplication(BaseModel):
    """Immutable metadata for an application installed on host system."""

    model_config = ConfigDict(frozen=True)

    info: ApplicationInfo = Field(default_factory=ApplicationInfo)
    install_path: str = ""
    is_system_app: bool = False
    icon_path: Optional[str] = None
    categories: List[str] = Field(default_factory=list)


class RunningApplication(BaseModel):
    """Immutable record of an actively running application process."""

    model_config = ConfigDict(frozen=True)

    process_id: int = 0
    app_id: str = ""
    name: str = ""
    executable_path: str = ""
    state: ApplicationState = ApplicationState.RUNNING
    launch_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    window_title: str = ""


class ApplicationLaunchRequest(BaseModel):
    """Immutable application launch specification."""

    model_config = ConfigDict(frozen=True)

    app_id_or_name: str = ""
    arguments: List[str] = Field(default_factory=list)
    working_directory: Optional[str] = None
    env_vars: Dict[str, str] = Field(default_factory=dict)
    launch_mode: LaunchMode = LaunchMode.NORMAL
    visibility: VisibilityMode = VisibilityMode.VISIBLE
    timeout_seconds: float = 30.0


class ApplicationLaunchResult(BaseModel):
    """Immutable result of an application launch attempt."""

    model_config = ConfigDict(frozen=True)

    success: bool = True
    process_id: Optional[int] = None
    app_id: str = ""
    executable_path: str = ""
    launch_time_ms: float = 0.0
    error: Optional[str] = None
    exit_code: Optional[int] = None


class ApplicationStatistics(BaseModel):
    """Immutable performance and launch statistics for Application Runtime."""

    model_config = ConfigDict(frozen=True)

    total_launches: int = 0
    successful_launches: int = 0
    failed_launches: int = 0
    active_applications_count: int = 0
    average_launch_time_ms: float = 0.0


class ApplicationCapabilities(BaseModel):
    """Immutable application runtime capabilities report."""

    model_config = ConfigDict(frozen=True)

    supports_background_launch: bool = True
    supports_window_modes: bool = True
    supports_alias_launch: bool = True
    supports_discovery: bool = True


class ApplicationHealth(BaseModel):
    """Immutable health summary of Application Runtime services."""

    model_config = ConfigDict(frozen=True)

    healthy: bool = True
    status: str = "READY"
    registered_count: int = 0
    active_count: int = 0
    uptime_seconds: float = 0.0
    details: Dict[str, Any] = Field(default_factory=dict)


class ApplicationRuntimeStatus(BaseModel):
    """Immutable status report of Application Runtime coordinator."""

    model_config = ConfigDict(frozen=True)

    state: str = "Initializing"
    healthy: bool = True
    provider_registered: bool = False
    total_launches: int = 0
    active_apps: int = 0
    uptime_seconds: float = 0.0


class ApplicationRegistryEntry(BaseModel):
    """Immutable application registry entry."""

    model_config = ConfigDict(frozen=True)

    app_id: str = ""
    name: str = ""
    executable_path: str = ""
    aliases: List[str] = Field(default_factory=list)
    category: str = "General"
    registered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
