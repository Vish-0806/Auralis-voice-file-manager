"""Low-level screen capture routines using mss and Pillow."""

from __future__ import annotations

import logging
import time
import mss
import pygetwindow as pgw
from PIL import Image


class CaptureManager:
    """Manages raw screen frame captures from system monitors and windows."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes the CaptureManager.

        Args:
            logger: Optional logger for diagnostics.
        """

        self._logger = logger or logging.getLogger(__name__)

    def capture_fullscreen(self) -> Image.Image:
        """Captures the entire combined screen canvas.

        Returns:
            A PIL Image of the screenshot.
        """

        self._logger.info("Capturing fullscreen screenshot")
        with mss.mss() as sct:
            sct_img = sct.grab(sct.monitors[0])
            return Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

    def capture_active_window(self) -> Image.Image:
        """Captures the boundaries of the currently focused application window.

        Returns:
            A PIL Image of the window screenshot.
        """

        self._logger.info("Capturing active window screenshot")
        active = pgw.getActiveWindow()
        if not active:
            raise RuntimeError("No active window found to capture.")

        bbox = {
            "left": active.left,
            "top": active.top,
            "width": active.width,
            "height": active.height,
        }
        
        if bbox["width"] <= 0 or bbox["height"] <= 0:
            self._logger.warning("Active window boundaries invalid, falling back to fullscreen")
            return self.capture_fullscreen()

        with mss.mss() as sct:
            sct_img = sct.grab(bbox)
            return Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

    def capture_monitor(self, monitor_num: int) -> Image.Image:
        """Captures a specific system monitor canvas.

        Args:
            monitor_num: Monitor index (1-based).

        Returns:
            A PIL Image of the monitor screenshot.
        """

        self._logger.info("Capturing specific monitor", extra={"monitor": monitor_num})
        with mss.mss() as sct:
            if monitor_num < 1 or monitor_num >= len(sct.monitors):
                raise ValueError(
                    f"Invalid monitor index {monitor_num}. Available monitors: 1 to {len(sct.monitors) - 1}."
                )
            monitor = sct.monitors[monitor_num]
            sct_img = sct.grab(monitor)
            return Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

    def capture_delayed(self, delay: float) -> Image.Image:
        """Waits for a specified duration before executing a fullscreen capture.

        Args:
            delay: Delay in seconds.

        Returns:
            A PIL Image of the delayed screenshot.
        """

        self._logger.info("Starting delayed screen capture", extra={"delay_seconds": delay})
        time.sleep(delay)
        return self.capture_fullscreen()
