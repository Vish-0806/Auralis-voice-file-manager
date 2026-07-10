"""OS display settings control implementation using WMI."""

from __future__ import annotations

import logging
import os


class DisplayController:
    """Controls OS screen brightness level and displays settings."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes the DisplayController.

        Args:
            logger: Optional logger for diagnostics.
        """

        self._logger = logger or logging.getLogger(__name__)

    def set_brightness(self, level: int) -> None:
        """Sets the screen brightness.

        Args:
            level: The target brightness (0-100).
        """

        self._logger.info("Setting brightness", extra={"level": level})
        level = max(0, min(100, level))

        if os.name == "nt":
            try:
                import win32com.client
                wmi = win32com.client.GetObject("winmgmts:\\\\.\\root\\wmi")
                methods = wmi.ExecQuery("SELECT * FROM WmiMonitorBrightnessMethods")
                for method in methods:
                    method.WmiSetBrightness(0, level)
            except Exception as exc:
                self._logger.error("WMI SetBrightness call failed", exc_info=exc)
        else:
            self._logger.warning("Brightness control is only supported on Windows")

    def get_brightness(self) -> int:
        """Gets the current screen brightness level (0-100)."""

        if os.name == "nt":
            try:
                import win32com.client
                wmi = win32com.client.GetObject("winmgmts:\\\\.\\root\\wmi")
                monitors = wmi.ExecQuery("SELECT * FROM WmiMonitorBrightness")
                for monitor in monitors:
                    return int(monitor.CurrentBrightness)
            except Exception as exc:
                self._logger.error("WMI GetBrightness query failed", exc_info=exc)
        return 50

    def increase_brightness(self, amount: int = 10) -> None:
        """Increases screen brightness level."""

        current = self.get_brightness()
        self.set_brightness(current + amount)

    def decrease_brightness(self, amount: int = 10) -> None:
        """Decreases screen brightness level."""

        current = self.get_brightness()
        self.set_brightness(current - amount)

    def enable_night_light(self) -> None:
        """Placeholder for enabling Night Light (blue light filter)."""

        self._logger.info("Night Light support placeholder called (Enable)")

    def disable_night_light(self) -> None:
        """Placeholder for disabling Night Light (blue light filter)."""

        self._logger.info("Night Light support placeholder called (Disable)")
