"""Manages the pipeline lifecycle, background loops, and exception recoveries."""

import threading
import time
from typing import Optional
from utils.logger import get_logger

from core.exceptions import PlanningException, DispatchException, CapabilityException
from voice.ux import AssistantStatus
from voice.integration.voice_pipeline import VoicePipeline

logger = get_logger(__name__)


class PipelineController:
    """Controls running loops, starts/stops background thread, and implements error recovery."""

    def __init__(self, voice_pipeline: VoicePipeline) -> None:
        """Initializes the PipelineController.

        Args:
            voice_pipeline: End-to-end VoicePipeline instance.
        """
        self.pipeline = voice_pipeline
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    @property
    def is_running(self) -> bool:
        """Checks if the pipeline loop is actively running.

        Returns:
            True if loop is running, False otherwise.
        """
        with self._lock:
            return self._running

    def start(self, run_in_thread: bool = True) -> None:
        """Starts the background continuous voice pipeline monitoring loop.

        Args:
            run_in_thread: If True, executes the loop in a background thread.
        """
        with self._lock:
            if self._running:
                logger.warning("PipelineController is already running.")
                return
            self._running = True
            logger.info("PipelineController starting.")

        if run_in_thread:
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()
        else:
            self._loop()

    def stop(self) -> None:
        """Stops the continuous pipeline monitoring loop and closes audio streams."""
        with self._lock:
            if not self._running:
                logger.warning("PipelineController is not running.")
                return
            self._running = False
            logger.info("PipelineController stopping.")

        # Trigger TTS output interruption to cancel active audio playing
        self.pipeline.text_to_speech.audio_output.stop()

        # Shutdown active conversation
        self.pipeline.conversation_manager.end_conversation()
        self.pipeline.context_manager.clear()

        # Join background thread
        if self._thread is not None:
            self._thread.join(timeout=3.0)
            self._thread = None

        logger.info("PipelineController stopped.")

    def _loop(self) -> None:
        """Continuous pipeline step runner loop with exception routing."""
        while True:
            with self._lock:
                if not self._running:
                    break

            try:
                # Process a single step (will block on STT when active)
                self.pipeline.process_step()
                time.sleep(0.05)  # brief sleep to prevent cpu spiking

            except Exception as e:
                self._handle_error(e)

    def _handle_error(self, exc: Exception) -> None:
        """Decodes exceptions and executes targeted error recovery policies.

        Args:
            exc: The caught Exception.
        """
        err_msg = str(exc)
        logger.exception("Pipeline error encountered: %s", err_msg)

        # 1. Error Recovery: Microphone disconnect
        if "microphone" in err_msg.lower() or "pyaudio" in err_msg.lower() or "device" in err_msg.lower():
            logger.warning("Microphone hardware error detected. Entering recovery backoff...")
            self.pipeline.feedback_manager.transition_to(
                AssistantStatus.ERROR,
                custom_message="Microphone disconnected. Retrying...",
            )
            self.pipeline.event_router.publish("MICROPHONE_ERROR", {"error": err_msg})
            # Sleep for 5 seconds to back off before retrying
            time.sleep(5.0)
            return

        # Check if conversation is active to decide if we notify the user
        active_session = self.pipeline.conversation_manager.get_active_session()

        # 2. Error Recovery: Recognition (STT) failure
        if "stt" in err_msg.lower() or "recognition" in err_msg.lower():
            self.pipeline.event_router.publish("RECOGNITION_ERROR", {"error": err_msg})
            if active_session is not None:
                self.pipeline.feedback_manager.transition_to(AssistantStatus.ERROR)
                self.pipeline.text_to_speech.speak(
                    "I'm sorry, I couldn't hear you clearly. Could you repeat that?"
                )
                self.pipeline.feedback_manager.transition_to(AssistantStatus.WAITING)
            return

        # 3. Error Recovery: Planner failure
        if isinstance(exc, PlanningException) or "planning" in err_msg.lower():
            self.pipeline.event_router.publish("PLANNING_ERROR", {"error": err_msg})
            if active_session is not None:
                self.pipeline.feedback_manager.transition_to(AssistantStatus.ERROR)
                self.pipeline.text_to_speech.speak(
                    "I couldn't formulate a plan for that command. Please try again."
                )
                self.pipeline.feedback_manager.transition_to(AssistantStatus.WAITING)
            return

        # 4. Error Recovery: Capability / Dispatcher failure
        if isinstance(exc, (DispatchException, CapabilityException)) or "dispatch" in err_msg.lower() or "capability" in err_msg.lower():
            self.pipeline.event_router.publish("CAPABILITY_ERROR", {"error": err_msg})
            if active_session is not None:
                self.pipeline.feedback_manager.transition_to(AssistantStatus.ERROR)
                self.pipeline.text_to_speech.speak(
                    "An error occurred while executing that operation. Please try again."
                )
                self.pipeline.feedback_manager.transition_to(AssistantStatus.WAITING)
            return

        # 5. Generic Unexpected exceptions
        self.pipeline.event_router.publish("UNEXPECTED_ERROR", {"error": err_msg})
        if active_session is not None:
            self.pipeline.feedback_manager.transition_to(AssistantStatus.ERROR)
            self.pipeline.text_to_speech.speak("An unexpected error occurred.")
            self.pipeline.feedback_manager.transition_to(AssistantStatus.WAITING)
        time.sleep(0.5)  # brief throttle to prevent rapid infinite looping
