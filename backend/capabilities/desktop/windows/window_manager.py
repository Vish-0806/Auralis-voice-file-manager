"""Module for OS-specific window management using pygetwindow and win32 APIs."""

from __future__ import annotations

import logging
import os
import pygetwindow as pgw
import win32process
import psutil


class WindowManager:
    """Encapsulates OS-specific window interaction and property querying.

    Provides a clean platform-independent API interface for capabilities.
    """

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes the WindowManager.

        Args:
            logger: Optional logger for diagnostics.
        """

        self._logger = logger or logging.getLogger(__name__)

    def get_all_windows(self) -> list[pgw.Window]:
        """Lists all windows currently open on the OS."""

        try:
            return pgw.getAllWindows()
        except Exception as exc:
            self._logger.exception("Failed to get all windows")
            return []

    def get_active_window(self) -> pgw.Window | None:
        """Retrieves the currently focused active window."""

        try:
            return pgw.getActiveWindow()
        except Exception as exc:
            self._logger.exception("Failed to get active window")
            return None

    def get_app_name(self, win: pgw.Window) -> str:
        """Resolves the owning process name of a window.

        Args:
            win: The pygetwindow Window instance.

        Returns:
            The process executable name (e.g., 'chrome.exe'), or 'Unknown'.
        """

        hwnd = getattr(win, "_hWnd", 0)
        if not hwnd:
            return "Unknown"

        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            proc = psutil.Process(pid)
            return proc.name()
        except Exception:
            return "Unknown"

    def minimize(self, win: pgw.Window) -> None:
        """Minimizes the window."""

        self._logger.info("Minimizing window", extra={"title": win.title})
        win.minimize()

    def maximize(self, win: pgw.Window) -> None:
        """Maximizes the window."""

        self._logger.info("Maximizing window", extra={"title": win.title})
        win.maximize()

    def restore(self, win: pgw.Window) -> None:
        """Restores the window from minimized/maximized state."""

        self._logger.info("Restoring window", extra={"title": win.title})
        win.restore()

    def focus(self, win: pgw.Window) -> None:
        """Focuses/activates the window."""

        self._logger.info("Focusing window", extra={"title": win.title})
        win.activate()

    def close(self, win: pgw.Window) -> None:
        """Closes the window."""

        self._logger.info("Closing window", extra={"title": win.title})
        win.close()

    def show_desktop(self) -> None:
        """Minimizes all visible titled windows except protected ones."""

        self._logger.info("Showing desktop by minimizing all application windows")
        for win in self.get_all_windows():
            title = getattr(win, "title", "")
            if win.visible and not win.isMinimized and title and not self.is_protected(win):
                try:
                    win.minimize()
                except Exception:
                    pass

    def is_protected(self, win: pgw.Window) -> bool:
        """Checks if a window is protected from system manipulation.

        Args:
            win: The pygetwindow Window instance.

        Returns:
            True if the window is protected, otherwise False.
        """

        title = getattr(win, "title", "") or ""
        protected_titles = {
            "Start",
            "Taskbar",
            "Program Manager",
            "Windows Shell Experience Host",
            "Cortana",
            "Action Center",
        }

        if title in protected_titles or not title.strip():
            return True

        # Process check: protect the current process window and parent process window
        hwnd = getattr(win, "_hWnd", 0)
        if hwnd:
            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                if pid == os.getpid():
                    return True
                parent = psutil.Process(os.getpid()).parent()
                if parent and pid == parent.pid:
                    return True
            except Exception:
                pass

        return False
