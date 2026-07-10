"""Module to resolve window targets by title, app name, or active status."""

from __future__ import annotations

import logging
import pygetwindow as pgw
from .window_manager import WindowManager


class WindowResolver:
    """Resolves target queries to matching system Window instances."""

    def __init__(
        self,
        window_manager: WindowManager,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initializes the WindowResolver.

        Args:
            window_manager: Preconfigured WindowManager instance.
            logger: Optional logger for resolution diagnostics.
        """

        self._logger = logger or logging.getLogger(__name__)
        self.wm = window_manager

    def resolve(self, query: str | None) -> list[pgw.Window]:
        """Resolves target queries to matching Window objects.

        Args:
            query: Window title, application name, or 'active'/'current'.

        Returns:
            A list of matching Window objects.
        """

        if not query or not query.strip():
            active = self.wm.get_active_window()
            return [active] if active else []

        normalized = query.strip().lower()

        if normalized in {"active", "current", "active window", "focused window"}:
            active = self.wm.get_active_window()
            return [active] if active else []

        all_windows = self.wm.get_all_windows()
        matches: list[pgw.Window] = []

        for win in all_windows:
            title = getattr(win, "title", "") or ""
            app_name = self.wm.get_app_name(win)
            if normalized in app_name.lower():
                matches.append(win)
                continue

            if normalized in title.lower():
                matches.append(win)
                continue

        if not matches:
            self._logger.warning("Could not resolve window query to any active window", extra={"query": query})

        return matches
