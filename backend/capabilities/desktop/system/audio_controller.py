"""OS audio control implementation using pycaw."""

from __future__ import annotations

import logging
from ctypes import POINTER, cast
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume


class AudioController:
    """Controls OS master volume level and mute status."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes the AudioController.

        Args:
            logger: Optional logger for diagnostics.
        """

        self._logger = logger or logging.getLogger(__name__)

    def _get_volume_interface(self) -> IAudioEndpointVolume:
        """Retrieves the IAudioEndpointVolume COM interface."""

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        return cast(interface, POINTER(IAudioEndpointVolume))

    def set_volume(self, level: int) -> None:
        """Sets the master volume level.

        Args:
            level: The target volume level (0-100).
        """

        self._logger.info("Setting volume", extra={"level": level})
        level = max(0, min(100, level))
        volume = self._get_volume_interface()
        volume.SetMasterVolumeLevelScalar(level / 100.0, None)

    def get_volume(self) -> int:
        """Gets the current master volume level (0-100)."""

        try:
            volume = self._get_volume_interface()
            val = volume.GetMasterVolumeLevelScalar()
            return int(round(val * 100))
        except Exception as exc:
            self._logger.error("Failed to get master volume", exc_info=exc)
            return 50

    def increase_volume(self, amount: int = 10) -> None:
        """Increases master volume level."""

        current = self.get_volume()
        self.set_volume(current + amount)

    def decrease_volume(self, amount: int = 10) -> None:
        """Decreases master volume level."""

        current = self.get_volume()
        self.set_volume(current - amount)

    def mute(self) -> None:
        """Mutes the master volume."""

        self._logger.info("Muting system audio")
        volume = self._get_volume_interface()
        volume.SetMute(1, None)

    def unmute(self) -> None:
        """Unmutes the master volume."""

        self._logger.info("Unmuting system audio")
        volume = self._get_volume_interface()
        volume.SetMute(0, None)

    def is_muted(self) -> bool:
        """Checks if system audio is muted."""

        try:
            volume = self._get_volume_interface()
            return bool(volume.GetMute())
        except Exception:
            return False
