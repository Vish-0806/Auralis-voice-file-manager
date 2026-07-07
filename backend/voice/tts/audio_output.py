"""Thread-safe audio output manager with speech queue and interruption controls."""

import ctypes
import os
import queue
import tempfile
import threading
import time
from typing import Any, Callable, Optional
import winsound
from utils.logger import get_logger

logger = get_logger(__name__)


class AudioOutput:
    """Manages audio playback, queueing, and immediate playback interruption.

    Uses Windows Multimedia DLL (winmm) for native MP3 playing and winsound
    for in-memory WAV playing, avoiding heavy decoding libraries.
    """

    def __init__(self) -> None:
        """Initializes the AudioOutput manager and starts the background worker."""
        self._queue: queue.Queue = queue.Queue()
        self._lock = threading.Lock()
        self._interrupted = False
        self._active_pyttsx3_engine: Any = None
        self._worker_thread = threading.Thread(target=self._run_queue, daemon=True)
        self._worker_thread.start()

    def set_active_pyttsx3_engine(self, engine: Any) -> None:
        """Sets the current active pyttsx3 engine for interruption tracking."""
        with self._lock:
            self._active_pyttsx3_engine = engine

    def clear_active_pyttsx3_engine(self) -> None:
        """Clears the active pyttsx3 engine reference."""
        with self._lock:
            self._active_pyttsx3_engine = None

    def queue_speech(self, play_task: Callable[[], None]) -> None:
        """Queues a speech task for background playback.

        Args:
            play_task: A callable function that plays audio or synthesizes text.
        """
        with self._lock:
            # Reset interrupted state when new audio is queued
            self._interrupted = False
        logger.debug("Speech task added to queue")
        self._queue.put(play_task)

    def stop(self) -> None:
        """Interrupts current speech playback and flushes the queue."""
        logger.info("Interrupting speech playback and flushing queue")
        with self._lock:
            self._interrupted = True

            # Clear queue
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                    self._queue.task_done()
                except Exception:
                    pass

            # 1. Stop winsound (WAV playback)
            try:
                winsound.PlaySound(None, winsound.SND_PURGE)
            except Exception as e:
                logger.debug("Failed to purge winsound: %s", e)

            # 2. Stop MCI (MP3 playback)
            try:
                winmm = ctypes.windll.winmm
                winmm.mciSendStringW("stop auralis_tts", None, 0, 0)
                winmm.mciSendStringW("close auralis_tts", None, 0, 0)
            except Exception as e:
                logger.debug("Failed to stop MCI: %s", e)

            # 3. Stop pyttsx3 engine
            if self._active_pyttsx3_engine is not None:
                try:
                    self._active_pyttsx3_engine.stop()
                except Exception as e:
                    logger.debug("Failed to stop active pyttsx3: %s", e)

    def is_interrupted(self) -> bool:
        """Checks if the playback has been interrupted.

        Returns:
            True if stop() was called during active playback, False otherwise.
        """
        with self._lock:
            return self._interrupted

    def play_bytes(self, audio_data: bytes, format: str = "mp3") -> bool:
        """Plays raw audio bytes (WAV or MP3) with active interruption checks.

        Args:
            audio_data: Binary audio bytes.
            format: The format of the audio ("mp3" or "wav").

        Returns:
            True if playback completed without interruption, False otherwise.
        """
        if not audio_data:
            return False

        file_format = format.lower().strip()

        # 1. Play WAV using winsound (SND_MEMORY)
        if file_format == "wav":
            logger.info("Playing WAV bytes (%d bytes)", len(audio_data))
            try:
                # SND_ASYNC lets us check for interruption while playing,
                # we stop it in stop() by playing SND_PURGE.
                winsound.PlaySound(
                    audio_data,
                    winsound.SND_MEMORY | winsound.SND_ASYNC | winsound.SND_NODEFAULT,
                )
                # Keep thread alive during async playback to block caller appropriately
                # but check for interruption.
                # A WAV header at byte 24 contains the sample rate (4 bytes)
                # and byte 28 contains byte rate (4 bytes) which we can use to estimate duration.
                # As a fallback, we poll winsound or just wait. Since winsound doesn't have a status
                # API, we can estimate duration:
                duration = 2.0  # default fallback
                if len(audio_data) > 44:
                    try:
                        byte_rate = int.from_bytes(audio_data[28:32], "little")
                        if byte_rate > 0:
                            duration = (len(audio_data) - 44) / byte_rate
                    except Exception:
                        pass

                logger.debug("Estimated WAV play duration: %.2fs", duration)
                steps = int(duration / 0.05)
                for _ in range(steps):
                    if self.is_interrupted():
                        return False
                    time.sleep(0.05)

                return not self.is_interrupted()
            except Exception as e:
                logger.error("Failed to play WAV bytes: %s", e)
                return False

        # 2. Play MP3 using Windows MCI (mciSendString)
        if file_format == "mp3":
            logger.info("Playing MP3 bytes (%d bytes)", len(audio_data))
            temp_file_path = ""
            try:
                # Write audio data to a temporary file
                fd, temp_file_path = tempfile.mkstemp(suffix=".mp3")
                os.close(fd)
                with open(temp_file_path, "wb") as f:
                    f.write(audio_data)

                winmm = ctypes.windll.winmm

                # Open device
                winmm.mciSendStringW(
                    f'open "{temp_file_path}" type mpegvideo alias auralis_tts',
                    None,
                    0,
                    0,
                )

                # Play non-blocking so we can check for interruption
                winmm.mciSendStringW("play auralis_tts", None, 0, 0)

                # Loop and check status
                buffer = ctypes.create_unicode_buffer(128)
                while True:
                    if self.is_interrupted():
                        winmm.mciSendStringW("stop auralis_tts", None, 0, 0)
                        break

                    winmm.mciSendStringW("status auralis_tts mode", buffer, 128, 0)
                    if buffer.value != "playing":
                        break
                    time.sleep(0.05)

                winmm.mciSendStringW("close auralis_tts", None, 0, 0)
                return not self.is_interrupted()

            except Exception as e:
                logger.error("MCI MP3 playback failed: %s", e)
                return False
            finally:
                if temp_file_path and os.path.exists(temp_file_path):
                    try:
                        os.remove(temp_file_path)
                    except Exception:
                        pass

        logger.warning("Unsupported audio format: %s", format)
        return False

    def _run_queue(self) -> None:
        """Infinite loop running in background thread to drain speech queue."""
        while True:
            try:
                # Blocks until an item is available
                play_task = self._queue.get()
                try:
                    if not self.is_interrupted():
                        play_task()
                except Exception as e:
                    logger.error("Error executing speech task: %s", e)
                finally:
                    self._queue.task_done()
            except Exception as e:
                logger.error("Error in AudioOutput queue worker loop: %s", e)
                time.sleep(0.1)

    def wait_until_done(self) -> None:
        """Blocks the calling thread until the queue is completely drained."""
        self._queue.join()
