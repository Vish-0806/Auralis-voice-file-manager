"""
Auralis pyttsx3 Text-to-Speech Provider
Implements speech synthesis using local engine drivers.
"""

from __future__ import annotations

import threading
import platform
from typing import Optional, List, Any

from utils.logger import get_logger
from voice.interfaces import ISpeechSynthesizer

logger = get_logger(__name__)


class Pyttsx3Synthesizer(ISpeechSynthesizer):
    """Thread-safe lazy-initialization wrapper around the pyttsx3 local library."""

    _engine = None
    _engine_lock = threading.Lock()
    _speak_lock = threading.Lock()

    @classmethod
    def _init_engine(cls) -> Any:
        if cls._engine is not None:
            return cls._engine

        with cls._engine_lock:
            if cls._engine is not None:
                return cls._engine

            try:
                # pyrefly: ignore [missing-import]
                import pyttsx3

                driver_name = None
                if platform.system() == "Windows":
                    driver_name = "sapi5"

                cls._engine = pyttsx3.init(driverName=driver_name) if driver_name else pyttsx3.init()

                # sensible defaults
                try:
                    cls._engine.setProperty("rate", 150)
                    cls._engine.setProperty("volume", 1.0)
                except Exception:
                    logger.debug("Driver did not accept default property settings.")

                logger.info("pyttsx3 engine initialized using driver %s", driver_name or "default")
                return cls._engine

            except Exception as exc:
                logger.exception("Failed to initialize pyttsx3 engine: %s", exc)
                raise

    def speak(self, text: str, wait: bool = True) -> bool:
        """Speaks the text. Spawns background thread if wait=False."""
        if not isinstance(text, str):
            logger.error("speak() called with non-string input: %r", type(text))
            return False

        text = text.strip()
        if not text:
            logger.warning("speak() called with empty or whitespace-only text")
            return False

        try:
            engine = self._init_engine()
        except Exception:
            return False

        logger.info("Speaking text (%d chars): %s", len(text), text if len(text) < 200 else text[:197] + "...")

        try:
            with self._speak_lock:
                engine.say(text)
                if wait:
                    engine.runAndWait()
                else:
                    def _runner(e):
                        try:
                            e.runAndWait()
                        except Exception:
                            logger.exception("Background speech runner failed")

                    t = threading.Thread(target=_runner, args=(engine,), daemon=True)
                    t.start()

            return True

        except Exception as exc:
            logger.exception("Error during text-to-speech: %s", exc)
            return False

    def set_rate(self, rate: int) -> bool:
        """Set voice play rate."""
        try:
            engine = self._init_engine()
            engine.setProperty("rate", int(rate))
            logger.info("TTS rate set to %s", rate)
            return True
        except Exception:
            logger.exception("Failed to set TTS rate")
            return False

    def set_volume(self, volume: float) -> bool:
        """Set volume level."""
        try:
            engine = self._init_engine()
            v = float(volume)
            if not (0.0 <= v <= 1.0):
                raise ValueError("volume must be between 0.0 and 1.0")
            engine.setProperty("volume", v)
            logger.info("TTS volume set to %s", v)
            return True
        except Exception:
            logger.exception("Failed to set TTS volume")
            return False

    def set_voice(self, voice_id: str) -> bool:
        """Set active speaker voice id."""
        try:
            engine = self._init_engine()
            engine.setProperty("voice", voice_id)
            logger.info("TTS voice set to %s", voice_id)
            return True
        except Exception:
            logger.exception("Failed to set TTS voice %s", voice_id)
            return False

    def get_voices(self) -> Optional[List[Any]]:
        """List all voices available."""
        try:
            engine = self._init_engine()
            return engine.getProperty("voices")
        except Exception:
            logger.exception("Failed to retrieve voices from TTS engine")
            return None
