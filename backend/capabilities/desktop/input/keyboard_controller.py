"""Low-level keyboard input automation using PyAutoGUI."""

from __future__ import annotations

import logging
import pyautogui


class KeyboardController:
    """Automates keystrokes, string writing, modifier hotkeys, and shortcuts."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes the KeyboardController.

        Args:
            logger: Optional logger for keyboard automation.
        """

        self._logger = logger or logging.getLogger(__name__)
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1

    def type_text(self, text: str) -> None:
        """Types the provided text string character by character.

        Args:
            text: Text to type.
        """

        if len(text) > 1000:
            raise ValueError("Safety limit exceeded: typing text too long (> 1000 characters).")

        self._logger.info("Typing text via keyboard controller")
        pyautogui.write(text, interval=0.01)

    def press_key(self, key: str) -> None:
        """Presses and releases a single key.

        Args:
            key: Name of the key (e.g. 'enter', 'esc', 'tab').
        """

        normalized_key = key.strip().lower()
        self._logger.info("Pressing key", extra={"key": normalized_key})
        pyautogui.press(normalized_key)

    def press_hotkey(self, *keys: str) -> None:
        """Presses multiple keys simultaneously (e.g., ctrl+c).

        Args:
            keys: Key name strings.
        """

        normalized_keys = [k.strip().lower() for k in keys]
        self._logger.info("Pressing hotkey combination", extra={"keys": normalized_keys})
        pyautogui.hotkey(*normalized_keys)
