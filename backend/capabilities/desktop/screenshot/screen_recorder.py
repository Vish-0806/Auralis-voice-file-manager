"""OS screen recording control API structure."""

from __future__ import annotations

import logging


class ScreenRecorder:
    """Controls screen video recording operations and states."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes the ScreenRecorder.

        Args:
            logger: Optional logger for diagnostics.
        """

        self._logger = logger or logging.getLogger(__name__)
        self._is_recording = False
        self._is_paused = False
        self._output_path = ""

    def start_recording(self, file_path: str) -> bool:
        """Starts recording screen canvas frames to the output file.

        Args:
            file_path: Output video file location.

        Returns:
            True if recording started.
        """

        if self._is_recording:
            self._logger.warning("Screen recording is already active")
            return False

        self._logger.info("Starting screen recording", extra={"destination": file_path})
        self._is_recording = True
        self._is_paused = False
        self._output_path = file_path
        return True

    def pause_recording(self) -> bool:
        """Pauses the active screen recording."""

        if not self._is_recording:
            self._logger.warning("No active recording to pause")
            return False

        self._logger.info("Pausing active screen recording")
        self._is_paused = True
        return True

    def stop_recording(self) -> bool:
        """Stops the active screen recording and finishes video compilation."""

        if not self._is_recording:
            self._logger.warning("No active recording to stop")
            return False

        self._logger.info("Stopping screen recording", extra={"destination": self._output_path})
        self._is_recording = False
        self._is_paused = False
        return True

    @property
    def is_recording(self) -> bool:
        """True if recording is active."""

        return self._is_recording

    @property
    def is_paused(self) -> bool:
        """True if recording is paused."""

        return self._is_paused
