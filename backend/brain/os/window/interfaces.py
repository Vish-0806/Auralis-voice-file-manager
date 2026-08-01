"""Abstract interfaces for Window Subsystem (Phase 11.6).

Defines canonical interfaces for Window Detector, Service, Controller,
Monitor, Provider, and Runtime.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from brain.os.window.window_models import (
    WindowBounds,
    WindowCapabilities,
    WindowHealth,
    WindowInfo,
    WindowOperationRequest,
    WindowOperationResult,
    WindowRuntimeStatus,
    WindowState,
    WindowStatistics,
)


class IWindowDetector(ABC):
    """Interface for desktop window discovery and lookup."""

    @abstractmethod
    def enumerate_windows(self, include_hidden: bool = False) -> List[WindowInfo]:
        """Enumerate active desktop windows."""
        pass

    @abstractmethod
    def get_by_id(self, window_id: str) -> Optional[WindowInfo]:
        """Lookup window by Window ID / Handle."""
        pass

    @abstractmethod
    def get_by_title(self, title: str) -> List[WindowInfo]:
        """Lookup windows matching title or title substring."""
        pass

    @abstractmethod
    def get_by_pid(self, pid: int) -> List[WindowInfo]:
        """Lookup windows owned by a specific process ID."""
        pass

    @abstractmethod
    def get_by_app(self, app_id: str) -> List[WindowInfo]:
        """Lookup windows belonging to an application ID."""
        pass

    @abstractmethod
    def get_active_window(self) -> Optional[WindowInfo]:
        """Get currently focused active foreground window."""
        pass


class IWindowService(ABC):
    """Interface for detailed window metadata and geometry inspection."""

    @abstractmethod
    def get_window(self, window_id_or_title: str) -> WindowInfo:
        """Get detailed window metadata."""
        pass

    @abstractmethod
    def get_window_bounds(self, window_id: str) -> WindowBounds:
        """Get window geometry bounding box."""
        pass

    @abstractmethod
    def get_window_state(self, window_id: str) -> WindowState:
        """Get window display and focus state."""
        pass


class IWindowController(ABC):
    """Interface for window manipulation operations (focus, minimize, move, etc.)."""

    @abstractmethod
    def execute_operation(self, request: WindowOperationRequest) -> WindowOperationResult:
        """Execute a window control operation request."""
        pass

    @abstractmethod
    def focus(self, window_id_or_title: str) -> WindowOperationResult:
        """Bring window to foreground and set focus."""
        pass

    @abstractmethod
    def minimize(self, window_id_or_title: str) -> WindowOperationResult:
        """Minimize window to taskbar."""
        pass

    @abstractmethod
    def maximize(self, window_id_or_title: str) -> WindowOperationResult:
        """Maximize window to monitor display."""
        pass

    @abstractmethod
    def restore(self, window_id_or_title: str) -> WindowOperationResult:
        """Restore window to normal state."""
        pass

    @abstractmethod
    def close(self, window_id_or_title: str) -> WindowOperationResult:
        """Close window."""
        pass

    @abstractmethod
    def move_and_resize(self, window_id_or_title: str, bounds: WindowBounds) -> WindowOperationResult:
        """Move and resize window to target bounds."""
        pass


class IWindowMonitor(ABC):
    """Interface for window lifecycle and active state monitoring."""

    @abstractmethod
    def start_monitoring(self, window_id: str) -> WindowInfo:
        """Begin tracking a window."""
        pass

    @abstractmethod
    def stop_monitoring(self, window_id: str) -> bool:
        """Stop tracking a window."""
        pass

    @abstractmethod
    def get_monitored_windows(self) -> List[WindowInfo]:
        """List currently monitored windows."""
        pass

    @abstractmethod
    def get_statistics(self) -> WindowStatistics:
        """Get window subsystem performance statistics."""
        pass


class IWindowProvider(ABC):
    """Interface for Window Subsystem Provider."""

    @abstractmethod
    def get_detector(self) -> IWindowDetector:
        """Return window detector."""
        pass

    @abstractmethod
    def get_service(self) -> IWindowService:
        """Return window service."""
        pass

    @abstractmethod
    def get_controller(self) -> IWindowController:
        """Return window controller."""
        pass

    @abstractmethod
    def get_monitor(self) -> IWindowMonitor:
        """Return window monitor."""
        pass

    @abstractmethod
    def get_health(self) -> WindowHealth:
        """Return provider health status."""
        pass

    @abstractmethod
    def get_statistics(self) -> WindowStatistics:
        """Return window statistics."""
        pass

    @abstractmethod
    def get_capabilities(self) -> WindowCapabilities:
        """Return window capabilities."""
        pass

    @abstractmethod
    def get_diagnostics(self) -> Dict[str, Any]:
        """Return diagnostic information."""
        pass


class IWindowRuntime(ABC):
    """Interface for Window Runtime coordinator."""

    @abstractmethod
    def initialize(self) -> None:
        """Initialize window runtime."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown window runtime."""
        pass

    @abstractmethod
    def register_provider(self, provider: IWindowProvider) -> None:
        """Register window provider."""
        pass

    @abstractmethod
    def get_provider(self) -> Optional[IWindowProvider]:
        """Get registered window provider."""
        pass

    @abstractmethod
    def get_statistics(self) -> WindowStatistics:
        """Get window runtime performance statistics."""
        pass

    @abstractmethod
    def get_health(self) -> WindowRuntimeStatus:
        """Get overall runtime health status."""
        pass

    @abstractmethod
    def get_diagnostics(self) -> Dict[str, Any]:
        """Get runtime diagnostics dictionary."""
        pass
