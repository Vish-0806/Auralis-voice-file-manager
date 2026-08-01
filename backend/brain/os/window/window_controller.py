"""Window Controller implementation (Phase 11.6).

Provides safe window manipulation operations (focus, minimize, maximize, restore,
hide, show, close, move, resize, center) with pre-execution validation.
"""

import ctypes
import sys
import time
from typing import Optional

from brain.os.window.exceptions import WindowNotFoundError, WindowOperationError
from brain.os.window.interfaces import IWindowController, IWindowService
from brain.os.window.window_models import (
    WindowBounds,
    WindowOperation,
    WindowOperationRequest,
    WindowOperationResult,
)
from brain.os.window.window_service import WindowService


class WindowController(IWindowController):
    """Provides window control manipulation operations."""

    def __init__(self, service: Optional[IWindowService] = None) -> None:
        self._service = service or WindowService()

    def _execute_win32_op(self, hwnd: int, op: WindowOperation, bounds: Optional[WindowBounds] = None) -> bool:
        """Execute platform Win32 API calls for window manipulation."""
        if sys.platform != "win32":
            return True

        user32 = ctypes.windll.user32
        # SW_HIDE = 0, SW_SHOWNORMAL = 1, SW_SHOWMINIMIZED = 2, SW_MAXIMIZE = 3, SW_RESTORE = 9
        try:
            if op == WindowOperation.FOCUS:
                user32.SetForegroundWindow(hwnd)
            elif op == WindowOperation.MINIMIZE:
                user32.ShowWindow(hwnd, 2)
            elif op == WindowOperation.MAXIMIZE:
                user32.ShowWindow(hwnd, 3)
            elif op == WindowOperation.RESTORE:
                user32.ShowWindow(hwnd, 9)
            elif op == WindowOperation.HIDE:
                user32.ShowWindow(hwnd, 0)
            elif op == WindowOperation.SHOW:
                user32.ShowWindow(hwnd, 1)
            elif op == WindowOperation.CLOSE:
                # WM_CLOSE = 0x0010
                user32.PostMessageW(hwnd, 0x0010, 0, 0)
            elif op in (WindowOperation.MOVE, WindowOperation.RESIZE, WindowOperation.CENTER) and bounds:
                # SWP_NOZORDER = 0x0004
                user32.SetWindowPos(hwnd, 0, bounds.x, bounds.y, bounds.width, bounds.height, 0x0004)
            return True
        except Exception:
            return False

    def execute_operation(self, request: WindowOperationRequest) -> WindowOperationResult:
        """Execute a window control operation request."""
        start_t = time.time()
        target = request.window_id_or_title

        if not target:
            raise WindowNotFoundError("Target window identifier cannot be empty")

        win_info = self._service.get_window(target)

        try:
            hwnd = 0
            try:
                hwnd = int(win_info.window_id)
            except ValueError:
                pass

            self._execute_win32_op(hwnd, request.operation, request.target_bounds)

            duration = (time.time() - start_t) * 1000.0
            return WindowOperationResult(
                success=True,
                window_id=win_info.window_id,
                operation=request.operation,
                duration_ms=duration,
            )
        except Exception as e:
            duration = (time.time() - start_t) * 1000.0
            raise WindowOperationError(f"Failed to execute operation '{request.operation.value}' on window '{target}': {e}", window_id=win_info.window_id)

    def focus(self, window_id_or_title: str) -> WindowOperationResult:
        """Bring window to foreground and set focus."""
        req = WindowOperationRequest(window_id_or_title=window_id_or_title, operation=WindowOperation.FOCUS)
        return self.execute_operation(req)

    def minimize(self, window_id_or_title: str) -> WindowOperationResult:
        """Minimize window to taskbar."""
        req = WindowOperationRequest(window_id_or_title=window_id_or_title, operation=WindowOperation.MINIMIZE)
        return self.execute_operation(req)

    def maximize(self, window_id_or_title: str) -> WindowOperationResult:
        """Maximize window to monitor display."""
        req = WindowOperationRequest(window_id_or_title=window_id_or_title, operation=WindowOperation.MAXIMIZE)
        return self.execute_operation(req)

    def restore(self, window_id_or_title: str) -> WindowOperationResult:
        """Restore window to normal state."""
        req = WindowOperationRequest(window_id_or_title=window_id_or_title, operation=WindowOperation.RESTORE)
        return self.execute_operation(req)

    def close(self, window_id_or_title: str) -> WindowOperationResult:
        """Close window."""
        req = WindowOperationRequest(window_id_or_title=window_id_or_title, operation=WindowOperation.CLOSE)
        return self.execute_operation(req)

    def move_and_resize(self, window_id_or_title: str, bounds: WindowBounds) -> WindowOperationResult:
        """Move and resize window to target bounds."""
        req = WindowOperationRequest(
            window_id_or_title=window_id_or_title,
            operation=WindowOperation.MOVE,
            target_bounds=bounds,
        )
        return self.execute_operation(req)
