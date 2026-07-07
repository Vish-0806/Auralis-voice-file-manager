"""Wake Word Audio Listener.

Continuously captures microphone input and passes audio chunks to the detector.
"""

import threading
import time
from typing import Any, Optional
from utils.logger import get_logger
from voice.wake_word.detector import WakeWordDetector
from voice.wake_word.models import WakeWordConfiguration, WakeWordState

logger = get_logger(__name__)


class WakeWordListener:
    """Manages system microphone capture and continuous streaming to the detector."""

    def __init__(
        self,
        detector: WakeWordDetector,
        config: Optional[WakeWordConfiguration] = None,
    ) -> None:
        """Initializes the WakeWordListener.

        Args:
            detector: The WakeWordDetector instance to receive audio chunks.
            config: Optional configuration settings.
        """
        self.detector = detector
        self.config = config or WakeWordConfiguration()
        self.state = WakeWordState()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    @property
    def is_running(self) -> bool:
        """Checks if the listener is currently running.

        Returns:
            True if the listener loop is active, False otherwise.
        """
        with self._lock:
            return self._running

    def start(self, run_in_thread: bool = True) -> None:
        """Starts the continuous microphone listening loop.

        Args:
            run_in_thread: If True, executes the loop in a background daemon thread.
        """
        with self._lock:
            if self._running:
                logger.warning("WakeWordListener is already running.")
                return
            self._running = True
            self.state.is_listening = True
            self.state.status_message = "running"
            logger.info("WakeWordListener starting.")

        if run_in_thread:
            self._thread = threading.Thread(target=self._listen_loop, daemon=True)
            self._thread.start()
        else:
            self._listen_loop()

    def stop(self) -> None:
        """Stops the continuous listening loop."""
        with self._lock:
            if not self._running:
                logger.warning("WakeWordListener is not running.")
                return
            self._running = False
            self.state.is_listening = False
            self.state.status_message = "stopping"
            logger.info("WakeWordListener stopping.")

        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        
        self.state.status_message = "idle"
        logger.info("WakeWordListener stopped.")

    def _listen_loop(self) -> None:
        """The main continuous listening loop.

        Handles PyAudio stream acquisition and fallback behaviors if device is missing.
        """
        pyaudio_available = False
        p = None
        stream = None

        try:
            import pyaudio
            pyaudio_available = True
        except ImportError:
            logger.warning("PyAudio is not installed. Running WakeWordListener in simulated/silent mode.")

        if pyaudio_available:
            try:
                p = pyaudio.PyAudio()
                # Open input stream
                stream = p.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=self.config.sample_rate,
                    input=True,
                    input_device_index=self.config.device_index,
                    frames_per_buffer=self.config.chunk_size,
                )
                logger.info("Microphone stream opened successfully.")
            except Exception as e:
                logger.error(
                    "Failed to open PyAudio input stream: %s. Falling back to simulated mode.",
                    str(e),
                )
                stream = None

        # Main loop
        while True:
            with self._lock:
                if not self._running:
                    break

            try:
                if stream is not None:
                    # Read block from stream (PCM bytes)
                    # exception_on_overflow=False avoids crash when system is laggy
                    data = stream.read(self.config.chunk_size, exception_on_overflow=False)
                else:
                    # Fallback simulation/silence generator
                    # Read size: chunk_size * 2 (since 16-bit depth is 2 bytes per frame)
                    time.sleep(self.config.chunk_size / self.config.sample_rate)
                    data = b"\x00" * (self.config.chunk_size * 2)

                # Send chunk to detector
                self.detector.process_audio_chunk(data)

            except Exception as e:
                logger.exception("Unexpected error in WakeWordListener loop: %s", str(e))
                time.sleep(0.1)

        # Cleanup
        if stream is not None:
            try:
                stream.stop_stream()
                stream.close()
            except Exception as e:
                logger.error("Error closing stream: %s", str(e))
        if p is not None:
            try:
                p.terminate()
            except Exception as e:
                logger.error("Error terminating PyAudio: %s", str(e))
