"""
Auralis Continuous Listener
Monitors input, detects wake words, processes parsed commands, and plays back results.
"""

import threading
import time
from typing import Optional
from utils.logger import get_logger
from voice.interfaces import IVoiceListener
from voice.manager import VoiceManager, get_voice_manager

logger = get_logger(__name__)


class ContinuousListener(IVoiceListener):
    """Continuously runs microphone checks and dispatches recognized commands."""

    def __init__(self, voice_manager: Optional[VoiceManager] = None) -> None:
        self.voice_manager = voice_manager or get_voice_manager()
        self._running = False
        self._thread = None
        self._lock = threading.Lock()

    @property
    def is_running(self) -> bool:
        """Checks if the listener is running thread-safely."""
        with self._lock:
            return self._running

    def start(self, run_in_thread: bool = False) -> None:
        """Starts the main continuous listening loop."""
        should_start = False
        with self._lock:
            if not self._running:
                self._running = True
                should_start = True
                logger.info("listener started")
            else:
                logger.warning("ContinuousListener is already running.")

        if should_start:
            if run_in_thread:
                self._thread = threading.Thread(target=self.listen_loop, daemon=True)
                self._thread.start()
            else:
                self.listen_loop()

    def stop(self) -> None:
        """Stops the loop and wait flags."""
        with self._lock:
            if not self._running:
                logger.warning("ContinuousListener is not running.")
                return

            self._running = False
            logger.info("listener stopped")

    def listen_loop(self) -> None:
        """The core command monitoring loop. Imports and calls through compatibility wrappers to support test patching."""
        import voice.continuous_listener as cl

        while True:
            with self._lock:
                if not self._running:
                    break

            try:
                # Step 1: Listen to microphone input
                recognized_text = cl.listen()

                # Step 2: Ignore empty input
                if not recognized_text:
                    continue

                # Step 3: Check wake word
                wake_result = cl.detect_wake_word(recognized_text)
                if not wake_result.get("activated"):
                    continue

                logger.info("wake word detected")
                command = wake_result.get("cleaned_command", "")

                # Handle empty command after wake word (e.g. user just said "Auralis")
                if not command:
                    logger.info("Wake word detected with empty command")
                    try:
                        cl.tts_speak("How can I help you?")
                    except Exception as e:
                        logger.error("Failed to speak prompt: %s", str(e))
                    continue

                # Step 4: Parse or handle pending action
                from capabilities.files.file_operations import get_pending_action
                from ai_engine.intent_classifier import classify_intent

                pending = get_pending_action()
                if pending:
                    logger.info("Pending action exists. Checking for voice confirmation/cancellation: '%s'", command)
                    intent = classify_intent(command)
                    logger.info("Classified voice intent for pending action: '%s'", intent)
                    if intent == "confirm":
                        parsed_action = {"action": "confirm", "target": ""}
                    elif intent == "cancel":
                        parsed_action = {"action": "cancel", "target": ""}
                    else:
                        logger.warning("Voice command '%s' ignored because a confirmation is pending", command)
                        try:
                            cl.tts_speak("Action pending. Please say yes or no.")
                        except Exception as e:
                            logger.error("Failed to speak pending warning: %s", str(e))
                        continue
                else:
                    parsed_action = cl.parse_command(command)

                # Step 5: Execute file operation
                try:
                    result = cl.execute_action(parsed_action)
                except Exception as exc:
                    logger.exception("Error executing action: %s", exc)
                    result = "Failed to execute command"

                logger.info("command executed")

                # Step 6: Speak response
                try:
                    from utils.helpers import format_speak_message
                    speak_msg = format_speak_message(result, parsed_action)
                    cl.tts_speak(speak_msg)
                except Exception as e:
                    logger.error("Failed to speak response: %s", str(e))

            except Exception as e:
                logger.exception("Unexpected error in listen loop: %s", str(e))
                # Add a brief pause to avoid tight loops on persistent errors
                time.sleep(0.5)


_listener_instance = None
_listener_lock = threading.Lock()


def get_listener() -> ContinuousListener:
    """Gets the default ContinuousListener singleton."""
    global _listener_instance
    if _listener_instance is None:
        with _listener_lock:
            if _listener_instance is None:
                _listener_instance = ContinuousListener()
    return _listener_instance
