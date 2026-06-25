from __future__ import annotations

import threading
import platform
from typing import Optional

from utils.logger import get_logger

logger = get_logger(__name__)


# Module-level engine and locks to enforce a singleton engine instance
_engine = None
_engine_lock = threading.Lock()
# Prevent concurrent calls to engine.runAndWait()
_speak_lock = threading.Lock()


def _init_engine() -> 'pyttsx3.Engine':
    """Initialize and return the pyttsx3 engine (created once).

    This is lazy and thread-safe. On Windows we prefer the 'sapi5' driver.
    """
    global _engine
    if _engine is not None:
        return _engine

    with _engine_lock:
        if _engine is not None:
            return _engine

        try:
            import pyttsx3

            driver_name = None
            if platform.system() == "Windows":
                driver_name = "sapi5"

            _engine = pyttsx3.init(driverName=driver_name) if driver_name else pyttsx3.init()

            # sensible defaults (can be changed via setters)
            try:
                _engine.setProperty("rate", 150)
                _engine.setProperty("volume", 1.0)
            except Exception:
                # Some drivers might not support property setting; ignore safely
                logger.debug("Driver did not accept default property settings.")

            logger.info("pyttsx3 engine initialized using driver %s", driver_name or "default")
            return _engine

        except Exception as exc:  # pragma: no cover - runtime environment dependent
            logger.exception("Failed to initialize pyttsx3 engine: %s", exc)
            raise


def speak(text: str, wait: bool = True) -> bool:
    """Speak the supplied text using the singleton pyttsx3 engine.

    Args:
        text: The text to speak. Must be a non-empty string.
        wait: If True, block until speech completes. If False, queue the speech.

    Returns:
        True if speech was queued/executed successfully, False otherwise.
    """
    if not isinstance(text, str):
        logger.error("speak() called with non-string input: %r", type(text))
        return False

    text = text.strip()
    if not text:
        logger.warning("speak() called with empty or whitespace-only text")
        return False

    try:
        engine = _init_engine()
    except Exception:
        # _init_engine already logged the exception
        return False

    logger.info("Speaking text (%d chars): %s", len(text), text if len(text) < 200 else text[:197] + "...")

    try:
        with _speak_lock:
            engine.say(text)
            if wait:
                engine.runAndWait()
            else:
                # runAndWait must be called eventually by the process; caller may invoke it.
                # We call it here in a non-blocking manner by spinning a tiny thread.
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


# --- Future configuration helpers ---
def set_rate(rate: int) -> bool:
    """Set speech rate (words per minute)."""
    try:
        engine = _init_engine()
        engine.setProperty("rate", int(rate))
        logger.info("TTS rate set to %s", rate)
        return True
    except Exception:
        logger.exception("Failed to set TTS rate")
        return False


def set_volume(volume: float) -> bool:
    """Set volume (0.0 to 1.0)."""
    try:
        engine = _init_engine()
        v = float(volume)
        if not (0.0 <= v <= 1.0):
            raise ValueError("volume must be between 0.0 and 1.0")
        engine.setProperty("volume", v)
        logger.info("TTS volume set to %s", v)
        return True
    except Exception:
        logger.exception("Failed to set TTS volume")
        return False


def set_voice(voice_id: str) -> bool:
    """Select voice by id. To inspect available voices use `get_voices()`."""
    try:
        engine = _init_engine()
        engine.setProperty("voice", voice_id)
        logger.info("TTS voice set to %s", voice_id)
        return True
    except Exception:
        logger.exception("Failed to set TTS voice %s", voice_id)
        return False


def get_voices() -> Optional[list]:
    """Return available voice descriptors from the engine, or None if unavailable."""
    try:
        engine = _init_engine()
        return engine.getProperty("voices")
    except Exception:
        logger.exception("Failed to retrieve voices from TTS engine")
        return None


__all__ = ["speak", "set_rate", "set_volume", "set_voice", "get_voices"]
