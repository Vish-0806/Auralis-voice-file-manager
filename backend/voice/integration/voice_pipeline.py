"""Voice integration pipeline coordinating all modular voice subsystems."""

from datetime import datetime, UTC
from typing import Any, Dict, Optional
from utils.logger import get_logger

from core.models import AssistantRequest, SessionContext
from voice.speech import Microphone, SpeechToText, SpeechResult
from voice.conversation import SessionManager, CONVERSATION_EXIT_COMMANDS
from voice.context import ContextManager
from voice.tts import TextToSpeech
from voice.ux import FeedbackManager, AssistantStatus
from voice.integration.event_router import EventRouter

logger = get_logger(__name__)


class VoicePipeline:
    """End-to-end voice pipeline execution coordinator."""

    def __init__(
        self,
        assistant: Any,
        wake_word_detector: Any,
        conversation_manager: SessionManager,
        speech_to_text: SpeechToText,
        context_manager: ContextManager,
        text_to_speech: TextToSpeech,
        feedback_manager: FeedbackManager,
        event_router: EventRouter,
        microphone: Optional[Microphone] = None,
    ) -> None:
        """Initializes the VoicePipeline.

        Args:
            assistant: The core Auralis Assistant instance.
            wake_word_detector: The WakeWordDetector instance.
            conversation_manager: The active session conversation manager.
            speech_to_text: Speech transcribing service.
            context_manager: Active context tracker.
            text_to_speech: Response speaking service.
            feedback_manager: Voice UX state-alerts coordinator.
            event_router: Subsystem event pub-sub router.
            microphone: Optional Microphone device. None uses default.
        """
        self.assistant = assistant
        self.wake_word_detector = wake_word_detector
        self.conversation_manager = conversation_manager
        self.speech_to_text = speech_to_text
        self.context_manager = context_manager
        self.text_to_speech = text_to_speech
        self.feedback_manager = feedback_manager
        self.event_router = event_router
        self.microphone = microphone or Microphone()

    def process_step(self, text_input: Optional[str] = None) -> bool:
        """Runs a single pipeline processing step (either text or mic-based).

        Args:
            text_input: Optional plain text to simulate user speech.

        Returns:
            True if a command was successfully processed, False otherwise.
        """
        active_session = self.conversation_manager.get_active_session()

        # CASE A: Simulation/Text command mode
        if text_input is not None:
            logger.info("Processing step via text simulation: '%s'", text_input)
            cmd = text_input.strip()

            if active_session is None:
                # Check for wake word
                wake_event = self.wake_word_detector.detect_in_text(cmd)
                if wake_event is not None:
                    self.event_router.publish("WAKE_WORD_DETECTED", wake_event)
                    self.feedback_manager.transition_to(AssistantStatus.WAKE_DETECTED)
                    active_session = self.conversation_manager.start_conversation()
                    self.feedback_manager.transition_to(AssistantStatus.LISTENING)

                    # Extract trailing command
                    cleaned_cmd = cmd.lower().replace(wake_event.phrase.lower(), "").strip()
                    if cleaned_cmd:
                        self.process_command(cleaned_cmd)
                        return True
                    return False
                return False
            else:
                self.process_command(cmd)
                return True

        # CASE B: Microphone/Audio capture mode
        if active_session is None:
            # Low-latency background wake phrase listening (sleeping state)
            # Listen with short timeout
            logger.debug("Active listening for wake phrase...")
            speech_result = self.speech_to_text.recognize(self.microphone, timeout=2.0)
            if speech_result.success and speech_result.text:
                wake_event = self.wake_word_detector.detect_in_text(speech_result.text)
                if wake_event is not None:
                    logger.info("Wake word matched from microphone!")
                    self.event_router.publish("WAKE_WORD_DETECTED", wake_event)
                    self.feedback_manager.transition_to(AssistantStatus.WAKE_DETECTED)
                    active_session = self.conversation_manager.start_conversation()
                    self.feedback_manager.transition_to(AssistantStatus.LISTENING)

                    # Extract trailing command
                    cleaned_cmd = speech_result.text.lower().replace(wake_event.phrase.lower(), "").strip()
                    if cleaned_cmd:
                        self.process_command(cleaned_cmd)
                        return True
            return False

        else:
            # Active conversation session (listening / follow-up command state)
            self.feedback_manager.transition_to(AssistantStatus.LISTENING)
            speech_result = self.speech_to_text.recognize(self.microphone)

            if not speech_result.success:
                # Check if it was an inactivity timeout
                if speech_result.error == "Timeout: No speech detected":
                    logger.info("Speech recognition timeout. Ending conversation.")
                    self.conversation_manager.handle_session_timeout()
                    self.context_manager.clear()
                    self.event_router.publish("SESSION_ENDED", {"reason": "timeout"})
                    self.feedback_manager.transition_to(AssistantStatus.SLEEPING)
                else:
                    # Let controller handle recognition failure exceptions
                    raise RuntimeError(f"STT Failure: {speech_result.error}")
                return False

            self.event_router.publish("SPEECH_RECOGNIZED", {"text": speech_result.text})
            self.process_command(speech_result.text)
            return True

    def process_command(self, raw_command: str) -> str:
        """Processes a plain text command, resolving context and executing.

        Args:
            raw_command: Plain text command from speech or simulation.

        Returns:
            The spoken text response string.
        """
        # Interrupt any ongoing TTS playback immediately on new input
        self.text_to_speech.audio_output.stop()

        command = raw_command.strip()
        cmd_lower = command.lower()
        active_session = self.conversation_manager.get_active_session()

        if active_session is None:
            # Defensive check
            return ""

        # 1. Check for conversation exit commands
        if cmd_lower in CONVERSATION_EXIT_COMMANDS:
            logger.info("Conversation exit command matching: '%s'", cmd_lower)
            self.feedback_manager.transition_to(AssistantStatus.SLEEPING)
            self.text_to_speech.speak("Goodbye.")
            self.conversation_manager.end_conversation()
            self.context_manager.clear()
            self.event_router.publish("SESSION_ENDED", {"reason": "user_exit"})
            return "Goodbye."

        # 2. Resolve Context References
        resolution = self.context_manager.resolve_references(command)
        if resolution.requires_clarification:
            logger.info("Reference resolution requires clarification: '%s'", resolution.clarification_prompt)
            self.feedback_manager.transition_to(AssistantStatus.WAITING)
            self.text_to_speech.speak(resolution.clarification_prompt)
            return resolution.clarification_prompt

        resolved_cmd = resolution.resolved_command
        self.event_router.publish("CONTEXT_RESOLVED", {"original": command, "resolved": resolved_cmd})

        # 3. Formulate AssistantRequest and SessionContext
        request = AssistantRequest(
            message=resolved_cmd,
            source="voice",
            timestamp=datetime.now(UTC),
        )
        session_ctx = SessionContext(
            session_id=active_session.session_id,
            current_directory=self.context_manager.state.current_folder,
            active_capability=self.context_manager.state.current_capability,
            conversation_id=active_session.session_id,
        )

        # 4. Invoke Assistant Execution
        self.feedback_manager.transition_to(AssistantStatus.PROCESSING)
        self.event_router.publish("EXECUTION_STARTED", {"command": resolved_cmd})

        response = self.assistant.process_request(request, session_ctx)

        # Check execution status
        if not response.result.success:
            logger.warning("Assistant execution failed: %s", response.result.error)
            self.feedback_manager.transition_to(AssistantStatus.ERROR)
            self.text_to_speech.speak(response.response)
            self.feedback_manager.transition_to(AssistantStatus.WAITING)
            self.event_router.publish("EXECUTION_FINISHED", {"success": False, "error": response.result.error})
            return response.response

        # Successful Execution
        logger.info("Assistant execution succeeded")
        self.event_router.publish("EXECUTION_FINISHED", {"success": True, "intent": response.plan.intent.value})

        # 5. Extract values and update context manager
        data = response.result.data
        current_file = data.get("current_file") or data.get("filename") or data.get("file")
        current_folder = data.get("current_folder") or data.get("directory") or data.get("folder")
        search_results = data.get("search_results") or data.get("files") or data.get("results")

        self.context_manager.update(
            current_file=current_file,
            current_folder=current_folder or session_ctx.current_directory,
            current_search_results=search_results,
            current_capability=response.plan.intent.value,
            last_intent=response.plan.intent.value,
            last_execution_result=response.response,
            pending_confirmation=data.get("pending_confirmation"),
        )

        # 6. Speak response via Text-To-Speech
        self.feedback_manager.transition_to(AssistantStatus.SPEAKING)
        self.text_to_speech.speak(response.response)
        self.feedback_manager.transition_to(AssistantStatus.WAITING)

        return response.response
