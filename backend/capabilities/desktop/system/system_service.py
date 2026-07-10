"""System Service coordinating system controllers."""

from __future__ import annotations

import logging
from .audio_controller import AudioController
from .display_controller import DisplayController
from .power_controller import PowerController
from .network_controller import NetworkController
from .models import SystemStatus


class SystemService:
    """Orchestrates system audio, display, power, and network operations."""

    def __init__(
        self,
        audio_controller: AudioController | None = None,
        display_controller: DisplayController | None = None,
        power_controller: PowerController | None = None,
        network_controller: NetworkController | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initializes the SystemService.

        Args:
            audio_controller: Custom audio controller.
            display_controller: Custom display controller.
            power_controller: Custom power controller.
            network_controller: Custom network controller.
            logger: Optional logger for service operations.
        """

        self._logger = logger or logging.getLogger(__name__)
        self._audio = audio_controller or AudioController(logger=self._logger)
        self._display = display_controller or DisplayController(logger=self._logger)
        self._power = power_controller or PowerController(logger=self._logger)
        self._network = network_controller or NetworkController(logger=self._logger)

    def set_volume(self, level: int) -> None:
        """Sets the system master volume level (0-100)."""

        self._audio.set_volume(level)

    def get_volume(self) -> int:
        """Gets the current master volume level (0-100)."""

        return self._audio.get_volume()

    def increase_volume(self, amount: int = 10) -> None:
        """Increases master volume level."""

        self._audio.increase_volume(amount)

    def decrease_volume(self, amount: int = 10) -> None:
        """Decreases master volume level."""

        self._audio.decrease_volume(amount)

    def mute(self) -> None:
        """Mutes system audio."""

        self._audio.mute()

    def unmute(self) -> None:
        """Unmutes system audio."""

        self._audio.unmute()

    def set_brightness(self, level: int) -> None:
        """Sets the display brightness level (0-100)."""

        self._display.set_brightness(level)

    def get_brightness(self) -> int:
        """Gets the display brightness level (0-100)."""

        return self._display.get_brightness()

    def increase_brightness(self, amount: int = 10) -> None:
        """Increases screen brightness level."""

        self._display.increase_brightness(amount)

    def decrease_brightness(self, amount: int = 10) -> None:
        """Decreases screen brightness level."""

        self._display.decrease_brightness(amount)

    def lock_pc(self) -> None:
        """Locks the workstation."""

        self._power.lock_pc()

    def sleep_pc(self) -> None:
        """Puts the computer to sleep."""

        self._power.sleep_pc()

    def shutdown_pc(self, confirm: bool = False) -> bool:
        """Shutdown the PC (supports future confirmations)."""

        return self._power.shutdown_pc(confirm)

    def restart_pc(self, confirm: bool = False) -> bool:
        """Restart the PC (supports future confirmations)."""

        return self._power.restart_pc(confirm)

    def hibernate_pc(self, confirm: bool = False) -> bool:
        """Hibernate the PC (supports future confirmations)."""

        return self._power.hibernate_pc(confirm)

    def enable_wifi(self) -> bool:
        """Enables the Wi-Fi network interface."""

        return self._network.enable_wifi()

    def disable_wifi(self) -> bool:
        """Disables the Wi-Fi network interface."""

        return self._network.disable_wifi()

    def enable_bluetooth(self) -> bool:
        """Enables the Bluetooth radio device."""

        return self._network.enable_bluetooth()

    def disable_bluetooth(self) -> bool:
        """Disables the Bluetooth radio device."""

        return self._network.disable_bluetooth()

    def get_system_status(self) -> SystemStatus:
        """Gathers system settings status metadata."""

        net_info = self._network.network_status()
        return SystemStatus(
            volume=self._audio.get_volume(),
            is_muted=self._audio.is_muted(),
            brightness=self._display.get_brightness(),
            wifi_enabled=net_info.get("wifi_enabled", False),
            bluetooth_enabled=net_info.get("bluetooth_enabled", False),
        )
