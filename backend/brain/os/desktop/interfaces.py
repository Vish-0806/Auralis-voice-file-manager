"""Abstract interfaces for Desktop Subsystem (Phase 11.5).

Defines canonical interfaces for Desktop Service, Clipboard Service,
Notification Service, Desktop Provider, and Desktop Runtime.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from brain.os.desktop.desktop_models import (
    ClipboardContent,
    DesktopCapabilities,
    DesktopHealth,
    DesktopInfo,
    DesktopNotification,
    DesktopRuntimeStatus,
    DesktopStatistics,
    KnownFolder,
    KnownFolderType,
    NotificationLevel,
)


class IDesktopService(ABC):
    """Interface for desktop environment inspection and known folder discovery."""

    @abstractmethod
    def get_desktop_info(self) -> DesktopInfo:
        """Get desktop environment session details and known folders map."""
        pass

    @abstractmethod
    def get_known_folders(self) -> Dict[KnownFolderType, KnownFolder]:
        """Discover all standard system known folders."""
        pass

    @abstractmethod
    def get_known_folder(self, folder_type: KnownFolderType) -> Optional[KnownFolder]:
        """Get details for a specific known folder type."""
        pass


class IClipboardService(ABC):
    """Interface for system clipboard read, write, and format detection."""

    @abstractmethod
    def read_content(self) -> ClipboardContent:
        """Read current data content from system clipboard."""
        pass

    @abstractmethod
    def write_text(self, text: str) -> bool:
        """Write string text to system clipboard."""
        pass

    @abstractmethod
    def write_files(self, files: List[str]) -> bool:
        """Write file paths to system clipboard."""
        pass

    @abstractmethod
    def clear(self) -> bool:
        """Clear all contents from system clipboard."""
        pass


class INotificationService(ABC):
    """Interface for dispatching desktop notifications and tracking history."""

    @abstractmethod
    def send_notification(
        self,
        title: str,
        message: str,
        level: NotificationLevel = NotificationLevel.INFO,
        duration_seconds: float = 5.0,
    ) -> DesktopNotification:
        """Dispatch a desktop notification."""
        pass

    @abstractmethod
    def get_history(self) -> List[DesktopNotification]:
        """Get list of dispatched notification history."""
        pass

    @abstractmethod
    def clear_history(self) -> None:
        """Clear notification history log."""
        pass


class IDesktopProvider(ABC):
    """Interface for Desktop Subsystem Provider."""

    @abstractmethod
    def get_desktop_service(self) -> IDesktopService:
        """Return desktop service."""
        pass

    @abstractmethod
    def get_clipboard_service(self) -> IClipboardService:
        """Return clipboard service."""
        pass

    @abstractmethod
    def get_notification_service(self) -> INotificationService:
        """Return notification service."""
        pass

    @abstractmethod
    def get_health(self) -> DesktopHealth:
        """Return provider health status."""
        pass

    @abstractmethod
    def get_statistics(self) -> DesktopStatistics:
        """Return desktop statistics."""
        pass

    @abstractmethod
    def get_capabilities(self) -> DesktopCapabilities:
        """Return desktop capabilities."""
        pass

    @abstractmethod
    def get_diagnostics(self) -> Dict[str, Any]:
        """Return diagnostic information."""
        pass


class IDesktopRuntime(ABC):
    """Interface for Desktop Runtime coordinator."""

    @abstractmethod
    def initialize(self) -> None:
        """Initialize desktop runtime."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown desktop runtime."""
        pass

    @abstractmethod
    def register_provider(self, provider: IDesktopProvider) -> None:
        """Register desktop provider."""
        pass

    @abstractmethod
    def get_provider(self) -> Optional[IDesktopProvider]:
        """Get registered desktop provider."""
        pass

    @abstractmethod
    def get_statistics(self) -> DesktopStatistics:
        """Get desktop runtime performance statistics."""
        pass

    @abstractmethod
    def get_health(self) -> DesktopRuntimeStatus:
        """Get overall runtime health status."""
        pass

    @abstractmethod
    def get_diagnostics(self) -> Dict[str, Any]:
        """Get runtime diagnostics dictionary."""
        pass
