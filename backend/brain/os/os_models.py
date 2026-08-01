"""Operating System Abstraction Layer Models (Phase 11.1).

Defines immutable Pydantic v2 domain models and enums representing operating system
metadata, platform architecture, environment snapshots, path information, runtime statistics,
and health/configuration models.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


class OperatingSystem(str, Enum):
    """Supported operating systems."""

    WINDOWS = "Windows"
    LINUX = "Linux"
    MACOS = "macOS"
    UNKNOWN = "Unknown"


class Architecture(str, Enum):
    """Processor architectures."""

    X86 = "x86"
    X64 = "x64"
    ARM = "ARM"
    ARM64 = "ARM64"
    UNKNOWN = "Unknown"


class RuntimeState(str, Enum):
    """Runtime lifecycle states."""

    INITIALIZING = "Initializing"
    RUNNING = "Running"
    STOPPING = "Stopping"
    STOPPED = "Stopped"
    FAILED = "Failed"


class OperatingSystemInfo(BaseModel):
    """Immutable representation of operating system details."""

    model_config = ConfigDict(frozen=True)

    operating_system: OperatingSystem = OperatingSystem.UNKNOWN
    architecture: Architecture = Architecture.UNKNOWN
    hostname: str = ""
    python_version: str = ""
    processor: str = ""
    machine: str = ""
    platform_release: str = ""
    platform_version: str = ""


class PlatformArchitecture(BaseModel):
    """Immutable platform architecture specifications."""

    model_config = ConfigDict(frozen=True)

    architecture: Architecture = Architecture.UNKNOWN
    pointer_bitness: int = 64
    is_64bit: bool = True
    endianness: str = "little"


class EnvironmentSnapshot(BaseModel):
    """Immutable snapshot of process environment state."""

    model_config = ConfigDict(frozen=True)

    home_directory: str = ""
    current_working_directory: str = ""
    temp_directory: str = ""
    environment_variables: Dict[str, str] = Field(default_factory=dict)
    username: str = ""
    timezone: str = ""
    locale: str = ""
    python_executable: str = ""
    process_id: int = 0
    captured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PathInformation(BaseModel):
    """Immutable detailed information about a path."""

    model_config = ConfigDict(frozen=True)

    original_path: str = ""
    normalized_path: str = ""
    absolute_path: str = ""
    is_absolute: bool = False
    is_safe: bool = True
    exists: bool = False
    is_file: bool = False
    is_directory: bool = False
    extension: str = ""
    parent_path: str = ""
    path_separator: str = "/"


class RuntimeStatistics(BaseModel):
    """Immutable operating system runtime performance and request statistics."""

    model_config = ConfigDict(frozen=True)

    total_requests: int = 0
    platform_checks: int = 0
    environment_snapshots: int = 0
    path_resolutions: int = 0
    errors_encountered: int = 0
    uptime_seconds: float = 0.0
    last_snapshot_at: Optional[datetime] = None


class ProviderHealth(BaseModel):
    """Immutable provider health status."""

    model_config = ConfigDict(frozen=True)

    healthy: bool = True
    status: str = "HEALTHY"
    registered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_health_check: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    details: Dict[str, Any] = Field(default_factory=dict)


class OSRuntimeStatus(BaseModel):
    """Immutable overall OS runtime status report."""

    model_config = ConfigDict(frozen=True)

    state: RuntimeState = RuntimeState.INITIALIZING
    healthy: bool = True
    provider_count: int = 0
    uptime_seconds: float = 0.0
    details: Dict[str, Any] = Field(default_factory=dict)


class ProviderConfiguration(BaseModel):
    """Immutable configuration for OperatingSystemProvider."""

    model_config = ConfigDict(frozen=True)

    enable_cache: bool = True
    cache_ttl_seconds: float = 60.0
    custom_env_overrides: Dict[str, str] = Field(default_factory=dict)
    strict_path_validation: bool = True
