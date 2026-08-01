"""Desktop Subsystem for Auralis Operating System Abstraction (Phase 11.5).

Exports domain models, enums, exceptions, abstract interfaces, services,
provider, runtime coordinator, and singleton accessors.
"""

from brain.os.desktop.clipboard_service import ClipboardService
from brain.os.desktop.desktop_models import (
    ClipboardContent,
    ClipboardFormat,
    DesktopCapabilities,
    DesktopEnvironment,
    DesktopHealth,
    DesktopInfo,
    DesktopNotification,
    DesktopRuntimeStatus,
    DesktopStatistics,
    KnownFolder,
    KnownFolderType,
    NotificationLevel,
)

from brain.os.desktop.desktop_provider import DesktopProvider
from brain.os.desktop.desktop_runtime import DesktopRuntime
from brain.os.desktop.desktop_service import DesktopService
from brain.os.desktop.exceptions import (
    ClipboardError,
    DesktopException,
    DesktopServiceError,
    NotificationError,
)
from brain.os.desktop.interfaces import (
    IClipboardService,
    IDesktopProvider,
    IDesktopRuntime,
    IDesktopService,
    INotificationService,
)

from brain.os.desktop.notification_service import NotificationService
from brain.os.desktop.runtime import get_desktop_runtime, reset_desktop_runtime

__all__ = [
    # Enums
    "DesktopEnvironment",
    "ClipboardFormat",
    "NotificationLevel",
    "KnownFolderType",
    # Models
    "KnownFolder",
    "DesktopInfo",
    "DesktopNotification",
    "ClipboardContent",
    "DesktopCapabilities",
    "DesktopStatistics",
    "DesktopHealth",
    "DesktopRuntimeStatus",
    # Exceptions
    "DesktopException",
    "ClipboardError",
    "NotificationError",
    "DesktopServiceError",
    # Interfaces
    "IDesktopService",
    "IClipboardService",
    "INotificationService",
    "IDesktopProvider",
    "IDesktopRuntime",
    # Services & Implementations
    "DesktopService",
    "ClipboardService",
    "NotificationService",
    "DesktopProvider",
    "DesktopRuntime",
    # Singleton Accessors
    "get_desktop_runtime",
    "reset_desktop_runtime",
]
