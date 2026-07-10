"""Input Service coordinating keyboard, mouse, shortcuts, and macros."""

from __future__ import annotations

import logging
from .keyboard_controller import KeyboardController
from .mouse_controller import MouseController
from .shortcut_manager import ShortcutManager
from .macro_executor import MacroExecutor


class InputService:
    """Coordinates input devices, registered system hotkeys, and custom macro sequences."""

    def __init__(
        self,
        keyboard_controller: KeyboardController | None = None,
        mouse_controller: MouseController | None = None,
        shortcut_manager: ShortcutManager | None = None,
        macro_executor: MacroExecutor | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initializes the InputService.

        Args:
            keyboard_controller: Custom keyboard controller.
            mouse_controller: Custom mouse controller.
            shortcut_manager: Custom shortcut manager.
            macro_executor: Custom macro executor.
            logger: Optional logger for service operations.
        """

        self._logger = logger or logging.getLogger(__name__)
        self._keyboard = keyboard_controller or KeyboardController(logger=self._logger)
        self._mouse = mouse_controller or MouseController(logger=self._logger)
        self._shortcut = shortcut_manager or ShortcutManager(
            keyboard_controller=self._keyboard,
            logger=self._logger,
        )
        self._macro = macro_executor or MacroExecutor(
            input_service=self,
            logger=self._logger,
        )

    def type_text(self, text: str) -> None:
        """Types string text character-by-character."""

        self._keyboard.type_text(text)

    def press_key(self, key: str) -> None:
        """Presses and releases a single key."""

        self._keyboard.press_key(key)

    def press_hotkey(self, *keys: str) -> None:
        """Presses combination hotkey."""

        self._keyboard.press_hotkey(*keys)

    def press_shortcut(self, name: str) -> None:
        """Performs a registered system shortcut."""

        self._shortcut.execute_shortcut(name)

    def move_mouse(self, x: int, y: int) -> None:
        """Moves cursor to screen coordinate x, y."""

        self._mouse.move_mouse(x, y)

    def click(self, button: str = "left") -> None:
        """Performs a single click."""

        self._mouse.click(button)

    def double_click(self, button: str = "left") -> None:
        """Performs a double click."""

        self._mouse.double_click(button)

    def right_click(self) -> None:
        """Performs a right click."""

        self._mouse.right_click()

    def scroll(self, direction_or_clicks: str | int) -> None:
        """Scrolls vertically.

        Args:
            direction_or_clicks: Clicks count or directions 'up'/'down'.
        """

        clicks = 0
        if isinstance(direction_or_clicks, int):
            clicks = direction_or_clicks
        else:
            val = str(direction_or_clicks).strip().lower()
            if val == "up":
                clicks = 100
            elif val == "down":
                clicks = -100
            else:
                try:
                    clicks = int(val)
                except ValueError:
                    clicks = 0

        self._mouse.scroll(clicks)

    def drag_and_drop(self, x1: int, y1: int, x2: int, y2: int) -> None:
        """Performs drag-and-drop movement."""

        self._mouse.drag_and_drop(x1, y1, x2, y2)

    def run_macro(self, name: str) -> None:
        """Executes a compound automation sequence."""

        self._macro.run_macro(name)
