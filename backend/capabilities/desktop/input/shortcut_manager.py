"""OS shortcut configuration mapping and manager."""

from __future__ import annotations

import logging
from .keyboard_controller import KeyboardController


class ShortcutManager:
    """Registers and executes mapped operating system hotkeys and actions."""

    _SHORTCUTS = {
        "copy": ["ctrl", "c"],
        "paste": ["ctrl", "v"],
        "undo": ["ctrl", "z"],
        "redo": ["ctrl", "y"],
        "save": ["ctrl", "s"],
        "save as": ["ctrl", "shift", "s"],
        "desktop": ["win", "d"],
        "task view": ["win", "tab"],
    }

    def __init__(
        self,
        keyboard_controller: KeyboardController,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initializes the ShortcutManager.

        Args:
            keyboard_controller: Controller for executing keystrokes.
            logger: Optional logger for shortcut actions.
        """

        self._logger = logger or logging.getLogger(__name__)
        self._keyboard = keyboard_controller

    def execute_shortcut(self, name: str) -> None:
        """Looks up shortcut name mapping and executes hotkey sequence.

        Args:
            name: Label of the shortcut.
        """

        normalized_name = name.strip().lower().replace("+", " ")
        target_shortcut = None
        if normalized_name in self._SHORTCUTS:
            target_shortcut = self._SHORTCUTS[normalized_name]
        elif normalized_name in {"ctrl s", "ctrl+s"}:
            target_shortcut = ["ctrl", "s"]
        elif normalized_name in {"ctrl c", "ctrl+c"}:
            target_shortcut = ["ctrl", "c"]
        elif normalized_name in {"ctrl v", "ctrl+v"}:
            target_shortcut = ["ctrl", "v"]
        elif normalized_name in {"ctrl z", "ctrl+z"}:
            target_shortcut = ["ctrl", "z"]
        elif normalized_name in {"ctrl y", "ctrl+y"}:
            target_shortcut = ["ctrl", "y"]
        elif normalized_name in {"ctrl shift s", "ctrl+shift+s"}:
            target_shortcut = ["ctrl", "shift", "s"]
        elif normalized_name in {"win d", "win+d"}:
            target_shortcut = ["win", "d"]
        elif normalized_name in {"win tab", "win+tab"}:
            target_shortcut = ["win", "tab"]

        if not target_shortcut:
            raise ValueError(f"Unsupported shortcut requested: {name}.")

        self._logger.info("Executing mapped system shortcut", extra={"name": name})
        self._keyboard.press_hotkey(*target_shortcut)
