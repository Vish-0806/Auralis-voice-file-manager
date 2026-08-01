"""Window Subsystem Domain Models for Auralis (Phase 11.6).

Defines immutable Pydantic v2 models and enums representing window bounds, states,
metadata, operation requests/results, capabilities, health status, and runtime state.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


class WindowVisibility(str, Enum):
    """Visibility state of a desktop window."""

    VISIBLE = "visible"
    HIDDEN = "hidden"
    MINIMIZED = "minimized"
    MAXIMIZED = "maximized"
    UNKNOWN = "unknown"


class WindowOperation(str, Enum):
    """Window control manipulation operations."""

    FOCUS = "focus"
    RESTORE = "restore"
    MINIMIZE = "minimize"
    MAXIMIZE = "maximize"
    HIDE = "hide"
    SHOW = "show"
    CLOSE = "close"
    MOVE = "move"
    RESIZE = "resize"
    CENTER = "center"


class WindowType(str, Enum):
    """Classification of window types."""

    NORMAL = "normal"
    DIALOG = "dialog"
    UTILITY = "utility"
    POPUP = "popup"
    DESKTOP = "desktop"
    UNKNOWN = "unknown"


class WindowFocusState(str, Enum):
    """Focus state of a desktop window."""

    FOCUSED = "focused"
    UNFOCUSED = "unfocused"
    UNKNOWN = "unknown"


class WindowBounds(BaseModel):
    """Immutable window geometry bounding box."""

    model_config = ConfigDict(frozen=True)

    x: int = 0
    y: int = 0
    width: int = 800
    height: int = 600


class WindowState(BaseModel):
    """Immutable current window display and focus state."""

    model_config = ConfigDict(frozen=True)

    visibility: WindowVisibility = WindowVisibility.VISIBLE
    focus_state: WindowFocusState = WindowFocusState.UNFOCUSED
    is_always_on_top: bool = False
    z_order: int = 0


class WindowInfo(BaseModel):
    """Immutable desktop window metadata details."""

    model_config = ConfigDict(frozen=True)

    window_id: str = ""
    title: str = ""
    process_id: int = 0
    executable_path: str = ""
    app_id: str = ""
    bounds: WindowBounds = Field(default_factory=WindowBounds)
    state: WindowState = Field(default_factory=WindowState)
    window_type: WindowType = WindowType.NORMAL
    monitor_id: int = 0


class WindowOperationRequest(BaseModel):
    """Immutable window manipulation operation specification."""

    model_config = ConfigDict(frozen=True)

    window_id_or_title: str = ""
    operation: WindowOperation = WindowOperation.FOCUS
    target_bounds: Optional[WindowBounds] = None
    timeout_seconds: float = 5.0


class WindowOperationResult(BaseModel):
    """Immutable result of a window manipulation operation."""

    model_config = ConfigDict(frozen=True)

    success: bool = True
    window_id: str = ""
    operation: WindowOperation = WindowOperation.FOCUS
    error: Optional[str] = None
    duration_ms: float = 0.0


class WindowCapabilities(BaseModel):
    """Immutable window runtime capabilities report."""

    model_config = ConfigDict(frozen=True)

    supports_window_enumeration: bool = True
    supports_window_manipulation: bool = True
    supports_focus: bool = True
    supports_bounds_adjustment: bool = True


class WindowStatistics(BaseModel):
    """Immutable window subsystem runtime performance statistics."""

    model_config = ConfigDict(frozen=True)

    total_windows_inspected: int = 0
    active_windows_count: int = 0
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0


class WindowHealth(BaseModel):
    """Immutable health status of Window Subsystem services."""

    model_config = ConfigDict(frozen=True)

    healthy: bool = True
    status: str = "READY"
    active_windows: int = 0
    uptime_seconds: float = 0.0
    details: Dict[str, Any] = Field(default_factory=dict)


class WindowRuntimeStatus(BaseModel):
    """Immutable overall Window Runtime status report."""

    model_config = ConfigDict(frozen=True)

    state: str = "Initializing"
    healthy: bool = True
    provider_registered: bool = False
    active_windows: int = 0
    total_operations: int = 0
    uptime_seconds: float = 0.0
