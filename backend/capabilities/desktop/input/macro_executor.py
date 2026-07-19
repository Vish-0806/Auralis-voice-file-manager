"""OS automation macro executor."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # pyrefly: ignore [missing-import]
    from .input_service import InputService


class MacroExecutor:
    """Executes predefined compound input automation sequences (macros)."""

    def __init__(
        self,
        input_service: InputService,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initializes the MacroExecutor.

        Args:
            input_service: Reference to the parent input service.
            logger: Optional logger for macro operations.
        """

        self._logger = logger or logging.getLogger(__name__)
        self._service = input_service

    def run_macro(self, name: str) -> None:
        """Runs the specified macro by name.

        Args:
            name: Predefined macro name identifier.
        """

        normalized_name = name.strip().lower()
        if normalized_name in {"save file", "save_file"}:
            self._logger.info("Executing 'Save File' macro sequence")
            self._service.press_hotkey("ctrl", "s")
            time.sleep(0.5)
            self._service.type_text("saved_file.txt")
            time.sleep(0.5)
            self._service.press_key("enter")
        else:
            raise ValueError(f"Predefined macro '{name}' not found.")
