"""Low-level mouse input automation using PyAutoGUI."""

from __future__ import annotations

import logging
import pyautogui


class MouseController:
    """Automates pointer movements, click options, scrolls, and drag-drops."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes the MouseController.

        Args:
            logger: Optional logger for mouse automation.
        """

        self._logger = logger or logging.getLogger(__name__)

    def _validate_coordinates(self, x: int, y: int) -> None:
        """Validates that coordinates are within current display bounds."""

        width, height = pyautogui.size()
        if not (0 <= x <= width and 0 <= y <= height):
            raise ValueError(
                f"Coordinates ({x}, {y}) out of screen bounds. Resolution is {width}x{height}."
            )

    def move_mouse(self, x: int, y: int) -> None:
        """Moves the pointer to absolute coordinates.

        Args:
            x: Horizontal pixel coordinate.
            y: Vertical pixel coordinate.
        """

        self._validate_coordinates(x, y)
        self._logger.info("Moving mouse pointer", extra={"x": x, "y": y})
        pyautogui.moveTo(x, y, duration=0.25)

    def click(self, button: str = "left") -> None:
        """Clicks the specified mouse button.

        Args:
            button: Button name ('left', 'right', 'middle').
        """

        normalized_btn = button.strip().lower()
        self._logger.info("Performing mouse click", extra={"button": normalized_btn})
        pyautogui.click(button=normalized_btn)

    def double_click(self, button: str = "left") -> None:
        """Double-clicks the specified mouse button.

        Args:
            button: Button name.
        """

        normalized_btn = button.strip().lower()
        self._logger.info("Performing double click", extra={"button": normalized_btn})
        pyautogui.doubleClick(button=normalized_btn)

    def right_click(self) -> None:
        """Performs a right mouse click."""

        self._logger.info("Performing right click")
        pyautogui.rightClick()

    def scroll(self, clicks: int) -> None:
        """Scrolls the active window vertically.

        Args:
            clicks: Scroll clicks. Positive up, negative down.
        """

        self._logger.info("Scrolling page", extra={"clicks": clicks})
        pyautogui.scroll(clicks)

    def drag_and_drop(self, x1: int, y1: int, x2: int, y2: int) -> None:
        """Drags from initial coordinates and drops at destination.

        Args:
            x1: Source horizontal coordinate.
            y1: Source vertical coordinate.
            x2: Destination horizontal coordinate.
            y2: Destination vertical coordinate.
        """

        self._validate_coordinates(x1, y1)
        self._validate_coordinates(x2, y2)
        self._logger.info(
            "Performing drag and drop",
            extra={"from": (x1, y1), "to": (x2, y2)},
        )
        pyautogui.moveTo(x1, y1)
        pyautogui.dragTo(x2, y2, duration=0.5)
