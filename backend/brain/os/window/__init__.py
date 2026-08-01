"""Window Subsystem for Auralis Operating System Abstraction (Phase 11.6).

Exports domain models, enums, exceptions, abstract interfaces, services,
provider, runtime coordinator, and singleton accessors.
"""

from brain.os.window.exceptions import (
    WindowException,
    WindowNotFoundError,
    WindowOperationError,
    WindowPermissionError,
)
from brain.os.window.interfaces import (
    IWindowController,
    IWindowDetector,
    IWindowMonitor,
    IWindowProvider,
    IWindowRuntime,
    IWindowService,
)
from brain.os.window.runtime import get_window_runtime, reset_window_runtime
from brain.os.window.window_controller import WindowController
from brain.os.window.window_detector import WindowDetector
from brain.os.window.window_models import (
    WindowBounds,
    WindowCapabilities,
    WindowFocusState,
    WindowHealth,
    WindowInfo,
    WindowOperation,
    WindowOperationRequest,
    WindowOperationResult,
    WindowRuntimeStatus,
    WindowState,
    WindowStatistics,
    WindowType,
    WindowVisibility,
)
from brain.os.window.window_monitor import WindowMonitor
from brain.os.window.window_provider import WindowProvider
from brain.os.window.window_runtime import WindowRuntime
from brain.os.window.window_service import WindowService

__all__ = [
    # Enums
    "WindowVisibility",
    "WindowOperation",
    "WindowType",
    "WindowFocusState",
    # Models
    "WindowBounds",
    "WindowState",
    "WindowInfo",
    "WindowCapabilities",
    "WindowStatistics",
    "WindowHealth",
    "WindowRuntimeStatus",
    "WindowOperationRequest",
    "WindowOperationResult",
    # Exceptions
    "WindowException",
    "WindowNotFoundError",
    "WindowOperationError",
    "WindowPermissionError",
    # Interfaces
    "IWindowDetector",
    "IWindowService",
    "IWindowController",
    "IWindowMonitor",
    "IWindowProvider",
    "IWindowRuntime",
    # Services & Implementations
    "WindowDetector",
    "WindowService",
    "WindowController",
    "WindowMonitor",
    "WindowProvider",
    "WindowRuntime",
    # Singleton Accessors
    "get_window_runtime",
    "reset_window_runtime",
]
