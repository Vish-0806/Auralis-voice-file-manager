"""
Continuous Listening module for Auralis Voice Assistant.
"""

import threading
import time
from utils.logger import get_logger
from voice_engine.speech_to_text import listen
from voice_engine.wake_word import detect_wake_word
from voice_engine.text_to_speech import speak as tts_speak
from ai_engine.command_parser import parse_command
from file_engine.file_operations import execute_action

logger = get_logger(__name__)


class ContinuousListener:
    """
    ContinuousListener class that monitors microphone input,
    detects the wake word, parses commands, executes file actions,
    and speaks the response.
    """

    def __init__(self) -> None:
        self._running = False
        self._thread = None
        self._lock = threading.Lock()

    def start(self, run_in_thread: bool = False) -> None:
        """
        Start the continuous listening loop.
        
        Args:
            run_in_thread: If True, spins up a background thread to run the loop.
                           If False, runs the loop synchronously in the current thread.
        """
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
        """
        Stop the continuous listening loop.
        """
        with self._lock:
            if not self._running:
                logger.warning("ContinuousListener is not running.")
                return

            self._running = False
            logger.info("listener stopped")

    def listen_loop(self) -> None:
        """
        Main loop to continuously capture and process audio commands.
        """
        while True:
            with self._lock:
                if not self._running:
                    break

            try:
                # Step 1: Listen to microphone input
                recognized_text = listen()

                # Step 2: Ignore empty input
                if not recognized_text:
                    continue

                # Step 3: Check wake word
                wake_result = detect_wake_word(recognized_text)
                if not wake_result.get("activated"):
                    continue

                logger.info("wake word detected")
                command = wake_result.get("cleaned_command", "")

                # Handle empty command after wake word (e.g. user just said "Auralis")
                if not command:
                    logger.info("Wake word detected with empty command")
                    try:
                        tts_speak("How can I help you?")
                    except Exception as e:
                        logger.error("Failed to speak prompt: %s", str(e))
                    continue

                # Step 4: Parse command
                parsed_action = parse_command(command)

                # Step 5: Execute file operation
                try:
                    result = execute_action(parsed_action)
                except Exception as exc:
                    logger.exception("Error executing action: %s", exc)
                    result = "Failed to execute command"

                logger.info("command executed")

                # Step 6: Speak response
                try:
                    lr = result.lower()
                    if lr.startswith("opened"):
                        speak_msg = result
                    elif "created" in lr:
                        speak_msg = "Folder created successfully"
                    elif "not found" in lr:
                        speak_msg = f"{parsed_action.get('target')} not found"
                    elif lr == "unknown action":
                        speak_msg = "Command not recognized"
                    else:
                        speak_msg = result

                    tts_speak(speak_msg)
                except Exception as e:
                    logger.error("Failed to speak response: %s", str(e))

            except Exception as e:
                logger.exception("Unexpected error in listen loop: %s", str(e))
                # Add a brief pause to avoid tight loops on persistent errors
                time.sleep(0.5)
