"""Microphone interface for capturing raw audio input.

Provides access to the hardware microphone using PyAudio, including opening,
closing, reading streams, and selecting/listing input devices.
"""

import time
from typing import Any, Dict, List, Optional
import pyaudio
from utils.logger import get_logger

logger = get_logger(__name__)


class Microphone:
    """Wrapper for hardware microphone audio capture using PyAudio."""

    def __init__(
        self,
        device_index: Optional[int] = None,
        sample_rate: int = 16000,
        chunk_size: int = 1024,
    ) -> None:
        """Initializes the Microphone instance.

        Args:
            device_index: Index of the input device. None uses the default.
            sample_rate: Recording sample rate in Hz (default 16000).
            chunk_size: Buffer chunk size in frames (default 1024).
        """
        self.device_index = device_index
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self._pyaudio: Optional[pyaudio.PyAudio] = None
        self._stream: Optional[pyaudio.Stream] = None

    def open(self) -> None:
        """Opens the microphone input stream.

        Raises:
            RuntimeError: If the microphone stream fails to open.
        """
        if self._stream is not None:
            logger.warning("Microphone stream is already open.")
            return

        try:
            self._pyaudio = pyaudio.PyAudio()
            if self.device_index is None:
                self.device_index = self.get_default_device_index()

            logger.info(
                "Opening microphone (device index: %s, sample rate: %d Hz)",
                self.device_index,
                self.sample_rate,
            )

            self._stream = self._pyaudio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.chunk_size,
            )
        except Exception as e:
            logger.error("Failed to open microphone: %s", e)
            self.close()
            raise RuntimeError(f"Failed to open microphone stream: {e}") from e

    def read(self) -> bytes:
        """Reads a chunk of raw PCM bytes from the microphone.

        Returns:
            Raw PCM audio bytes.

        Raises:
            RuntimeError: If the microphone stream is not open.
        """
        if self._stream is None:
            raise RuntimeError("Microphone stream is not open. Call open() first.")

        try:
            # exception_on_overflow=False prevents crashes due to buffer overruns
            return self._stream.read(self.chunk_size, exception_on_overflow=False)
        except Exception as e:
            logger.error("Error reading audio from microphone: %s", e)
            raise RuntimeError(f"Microphone read failure: {e}") from e

    def close(self) -> None:
        """Closes the microphone stream and terminates PyAudio."""
        logger.info("Closing microphone stream")
        if self._stream is not None:
            try:
                if self._stream.is_active():
                    self._stream.stop_stream()
                self._stream.close()
            except Exception as e:
                logger.debug("Error closing stream: %s", e)
            self._stream = None

        if self._pyaudio is not None:
            try:
                self._pyaudio.terminate()
            except Exception as e:
                logger.debug("Error terminating PyAudio: %s", e)
            self._pyaudio = None

    def get_default_device_index(self) -> int:
        """Retrieves the default input device index.

        Returns:
            The default input device index.

        Raises:
            RuntimeError: If no default input device is found.
        """
        p = pyaudio.PyAudio()
        try:
            default_device = p.get_default_input_device_info()
            index = default_device.get("index")
            if index is None:
                raise RuntimeError("Default input device index is None.")
            return int(index)
        except Exception as e:
            logger.error("Failed to get default input device: %s", e)
            raise RuntimeError("No default input device found on the system.") from e
        finally:
            p.terminate()

    def list_devices(self) -> List[Dict[str, Any]]:
        """Lists all available audio input devices.

        Returns:
            A list of dictionaries containing device index, name, and channel count.
        """
        p = pyaudio.PyAudio()
        devices = []
        try:
            device_count = p.get_device_count()
            for i in range(device_count):
                try:
                    info = p.get_device_info_by_index(i)
                    # Filter for input devices
                    if info.get("maxInputChannels", 0) > 0:
                        devices.append({
                            "index": info.get("index"),
                            "name": info.get("name"),
                            "max_input_channels": info.get("maxInputChannels"),
                            "default_sample_rate": info.get("defaultSampleRate"),
                        })
                except Exception as e:
                    logger.debug("Failed to query device info for index %d: %s", i, e)
            return devices
        finally:
            p.terminate()
