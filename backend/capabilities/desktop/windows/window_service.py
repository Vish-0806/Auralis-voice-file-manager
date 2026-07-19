"""Window service coordinating window resolution and manager controls."""

from __future__ import annotations

import logging
# pyrefly: ignore [missing-import]
import pygetwindow as pgw
from .window_manager import WindowManager
from .window_resolver import WindowResolver
from .models import WindowDetails


class WindowService:
    """Service layer managing application window states on the host OS."""

    def __init__(
        self,
        resolver: WindowResolver | None = None,
        window_manager: WindowManager | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initializes the WindowService.

        Args:
            resolver: Custom window resolver.
            window_manager: Custom window manager.
            logger: Optional logger for service operations.
        """

        self._logger = logger or logging.getLogger(__name__)
        self._window_manager = window_manager or WindowManager(logger=self._logger)
        self._resolver = resolver or WindowResolver(self._window_manager, logger=self._logger)

    def minimize_window(self, query: str | None) -> bool:
        """Minimizes matching windows.

        Args:
            query: Window target query.

        Returns:
            True if one or more windows were minimized.
        """

        wins = self._resolve_and_verify(query)
        actioned = False
        for win in wins:
            if self._window_manager.is_protected(win):
                self._logger.warning("Skip minimizing protected window", extra={"title": win.title})
                continue
            self._window_manager.minimize(win)
            actioned = True
        return actioned

    def maximize_window(self, query: str | None) -> bool:
        """Maximizes matching windows.

        Args:
            query: Window target query.

        Returns:
            True if one or more windows were maximized.
        """

        wins = self._resolve_and_verify(query)
        actioned = False
        for win in wins:
            if self._window_manager.is_protected(win):
                self._logger.warning("Skip maximizing protected window", extra={"title": win.title})
                continue
            self._window_manager.maximize(win)
            actioned = True
        return actioned

    def restore_window(self, query: str | None) -> bool:
        """Restores matching windows.

        Args:
            query: Window target query.

        Returns:
            True if one or more windows were restored.
        """

        wins = self._resolve_and_verify(query)
        actioned = False
        for win in wins:
            if self._window_manager.is_protected(win):
                self._logger.warning("Skip restoring protected window", extra={"title": win.title})
                continue
            self._window_manager.restore(win)
            actioned = True
        return actioned

    def focus_window(self, query: str | None) -> bool:
        """Focuses the first matching window.

        Args:
            query: Window target query.

        Returns:
            True if a window was focused.
        """

        wins = self._resolve_and_verify(query)
        for win in wins:
            if self._window_manager.is_protected(win):
                self._logger.warning("Skip focusing protected window", extra={"title": win.title})
                continue
            self._window_manager.focus(win)
            return True
        return False

    def close_window(self, query: str | None) -> bool:
        """Closes matching windows.

        Args:
            query: Window target query.

        Returns:
            True if one or more windows were closed.
        """

        wins = self._resolve_and_verify(query)
        actioned = False
        for win in wins:
            if self._window_manager.is_protected(win):
                self._logger.warning("Skip closing protected window", extra={"title": win.title})
                raise PermissionError(f"Closing system window '{win.title}' is blocked.")
            self._window_manager.close(win)
            actioned = True
        return actioned

    def list_windows(self) -> list[WindowDetails]:
        """Lists metadata details for all visible open windows.

        Returns:
            A list of WindowDetails.
        """

        all_windows = self._window_manager.get_all_windows()
        active = self._window_manager.get_active_window()
        active_hwnd = getattr(active, "_hWnd", 0) if active else 0

        results = []
        for win in all_windows:
            title = getattr(win, "title", "")
            if win.visible and title:
                hwnd = getattr(win, "_hWnd", 0)
                app_name = self._window_manager.get_app_name(win)
                results.append(
                    WindowDetails(
                        handle=hwnd,
                        title=title,
                        app_name=app_name,
                        is_active=(hwnd == active_hwnd),
                        is_minimized=win.isMinimized,
                        is_maximized=win.isMaximized,
                    )
                )
        return results

    def show_desktop(self) -> None:
        """Minimizes all visible titled windows except protected ones."""

        self._window_manager.show_desktop()

    def _resolve_and_verify(self, query: str | None) -> list[pgw.Window]:
        """Resolves target query and verifies that matching windows exist.

        Raises:
            ValueError: If no matching window is found.
        """

        wins = self._resolver.resolve(query)
        wins = [w for w in wins if w is not None]
        if not wins:
            raise ValueError(f"Target window not found for query: '{query or 'active'}'")
        return wins
