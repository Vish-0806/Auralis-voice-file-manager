"""Desktop Subsystem Domain Models for Auralis (Phase 11.5).

Defines immutable Pydantic v2 models and enums representing desktop environment details,
known folders, clipboard contents, desktop notifications, performance statistics,
capabilities, health status, and runtime state.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


class DesktopEnvironment(str, Enum):
    """Desktop Environment classification."""

    WINDOWS = "windows"
    MACOS = "macos"
    GNOME = "gnome"
    KDE = "kde"
    XFCE = "xfce"
    UNKNOWN = "unknown"


class ClipboardFormat(str, Enum):
    """Supported clipboard data formats."""

    TEXT = "text"
    IMAGE = "image"
    FILES = "files"
    UNKNOWN = "unknown"


class NotificationLevel(str, Enum):
    """Priority and severity level for desktop notifications."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class KnownFolderType(str, Enum):
    """Standard system known directory types."""

    DESKTOP = "desktop"
    DOCUMENTS = "documents"
    DOWNLOADS = "downloads"
    PICTURES = "pictures"
    VIDEOS = "videos"
    MUSIC = "music"
    HOME = "home"
    TEMP = "temp"


class KnownFolder(BaseModel):
    """Immutable representation of a standard system known folder."""

    model_config = ConfigDict(frozen=True)

    folder_type: KnownFolderType = KnownFolderType.HOME
    name: str = ""
    path: str = ""
    exists: bool = True
    is_writable: bool = True


class DesktopInfo(BaseModel):
    """Immutable desktop session and environment details."""

    model_config = ConfigDict(frozen=True)

    environment: DesktopEnvironment = DesktopEnvironment.UNKNOWN
    display_name: str = ""
    session_id: str = ""
    user_name: str = ""
    known_folders: Dict[str, KnownFolder] = Field(default_factory=dict)


class DesktopNotification(BaseModel):
    """Immutable desktop notification specification."""

    model_config = ConfigDict(frozen=True)

    notification_id: str = ""
    title: str = ""
    message: str = ""
    level: NotificationLevel = NotificationLevel.INFO
    duration_seconds: float = 5.0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    category: str = "General"
    action_url: Optional[str] = None


class ClipboardContent(BaseModel):
    """Immutable snapshot of current clipboard data."""

    model_config = ConfigDict(frozen=True)

    format: ClipboardFormat = ClipboardFormat.UNKNOWN
    text_content: Optional[str] = None
    file_paths: List[str] = Field(default_factory=list)
    byte_size: int = 0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DesktopCapabilities(BaseModel):
    """Immutable desktop subsystem capabilities report."""

    model_config = ConfigDict(frozen=True)

    supports_clipboard_text: bool = True
    supports_clipboard_files: bool = True
    supports_notifications: bool = True
    supports_known_folders: bool = True


class DesktopStatistics(BaseModel):
    """Immutable performance statistics for Desktop Subsystem."""

    model_config = ConfigDict(frozen=True)

    total_notifications_sent: int = 0
    total_clipboard_reads: int = 0
    total_clipboard_writes: int = 0
    known_folders_count: int = 0


class DesktopHealth(BaseModel):
    """Immutable health status of Desktop Subsystem services."""

    model_config = ConfigDict(frozen=True)

    healthy: bool = True
    status: str = "READY"
    desktop_env: DesktopEnvironment = DesktopEnvironment.UNKNOWN
    uptime_seconds: float = 0.0
    details: Dict[str, Any] = Field(default_factory=dict)


class DesktopRuntimeStatus(BaseModel):
    """Immutable overall Desktop Runtime status report."""

    model_config = ConfigDict(frozen=True)

    state: str = "Initializing"
    healthy: bool = True
    provider_registered: bool = False
    uptime_seconds: float = 0.0
    total_notifications: int = 0
