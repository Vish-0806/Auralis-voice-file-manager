"""Window Service implementation (Phase 11.6).

Provides detailed window inspection, metadata retrieval, geometry bounds extraction,
and state querying.
"""

from typing import Optional

from brain.os.window.exceptions import WindowNotFoundError
from brain.os.window.interfaces import IWindowDetector, IWindowService
from brain.os.window.window_detector import WindowDetector
from brain.os.window.window_models import WindowBounds, WindowInfo, WindowState


class WindowService(IWindowService):
    """Provides window metadata and geometry inspection."""

    def __init__(self, detector: Optional[IWindowDetector] = None) -> None:
        self._detector = detector or WindowDetector()

    def get_window(self, window_id_or_title: str) -> WindowInfo:
        """Get detailed window metadata by ID or title lookup."""
        win = self._detector.get_by_id(window_id_or_title)
        if not win:
            matches = self._detector.get_by_title(window_id_or_title)
            if matches:
                win = matches[0]

        if not win:
            raise WindowNotFoundError(f"Window '{window_id_or_title}' not found", window_id=window_id_or_title)
        return win

    def get_window_bounds(self, window_id: str) -> WindowBounds:
        """Get window geometry bounding box."""
        win = self.get_window(window_id)
        return win.bounds

    def get_window_state(self, window_id: str) -> WindowState:
        """Get window display and focus state."""
        win = self.get_window(window_id)
        return win.state
