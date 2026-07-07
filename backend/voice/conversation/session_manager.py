"""Session manager for orchestrating voice conversations.

Coordinates wake word detection, speech-to-text, command execution, and
text-to-speech backends. Handles session transitions, inactivity timeouts,
and explicit exit commands.
"""

import time
from typing import Any, Callable, Dict, Optional, Set, Tuple
from utils.logger import get_logger

from voice.conversation.conversation_state import ConversationState
from voice.conversation.context import ConversationContext
from voice.conversation.inactivity_timer import InactivityTimer
from voice.conversation.models import ConversationSession

logger = get_logger(__name__)

# Standard conversation exit commands
CONVERSATION_EXIT_COMMANDS: Set[str] = {
    "goodbye",
    "exit",
    "stop listening",
    "cancel",
    "never mind",
    "thank you",
}


class SessionManager:
    """Orchestrates the voice conversation lifecycle and transitions states."""

    def __init__(
        self,
        wake_word_detector: Callable[[str], Dict[str, Any]],
        speech_recognizer: Callable[[], Any],  # Returns a SpeechResult or similar
        command_executor: Callable[[str, ConversationContext], Tuple[str, Dict[str, Any]]],
        tts_speaker: Callable[[str], None],
        timeout_seconds: float = 30.0,
    ) -> None:
        """Initializes the SessionManager with delegates for voice operations.

        Args:
            wake_word_detector: Callable checking if a phrase contains the wake word.
            speech_recognizer: Callable capturing and transcribing microphone audio.
            command_executor: Callable executing commands and returning a response
                and dictionary of updated context fields.
            tts_speaker: Callable synthesizing spoken output to the user.
            timeout_seconds: Seconds of inactivity before auto-ending the session.
        """
        self.wake_word_detector = wake_word_detector
        self.speech_recognizer = speech_recognizer
        self.command_executor = command_executor
        self.tts_speaker = tts_speaker
        self.timeout_seconds = timeout_seconds

        self.current_session: Optional[ConversationSession] = None
        self.inactivity_timer = InactivityTimer(
            timeout_seconds, self.handle_session_timeout
        )

    def get_active_session(self) -> Optional[ConversationSession]:
        """Returns the current active conversation session, if one exists.

        Returns:
            The active ConversationSession or None.
        """
        if self.current_session is not None and self.current_session.is_active:
            return self.current_session
        return None

    def start_conversation(self) -> ConversationSession:
        """Starts a new conversation session, transitioning state to LISTENING.

        Returns:
            The newly created ConversationSession.
        """
        logger.info("Starting new conversation session")
        session = ConversationSession(
            state=ConversationState.LISTENING,
            start_time=time.time(),
            last_active_time=time.time(),
            is_active=True,
        )
        self.current_session = session
        self.inactivity_timer.start()

        # Speak initial greeting
        try:
            self.tts_speaker("How can I help you?")
        except Exception as e:
            logger.error("Failed to speak session start greeting: %s", e)

        return session

    def end_conversation(self) -> None:
        """Ends the active conversation session, resetting state to SLEEPING."""
        session = self.get_active_session()
        if session is not None:
            logger.info("Ending conversation session %s", session.session_id)
            session.is_active = False
            session.state = ConversationState.SLEEPING
            self.inactivity_timer.cancel()
            self.current_session = None

    def handle_session_timeout(self) -> None:
        """Callback invoked when inactivity timer expires, ending the session."""
        session = self.get_active_session()
        if session is not None:
            logger.info("Session %s timed out due to inactivity", session.session_id)
            try:
                # Notify the user of timeout sign-off
                self.tts_speaker("Goodbye.")
            except Exception as e:
                logger.error("Failed to speak session timeout greeting: %s", e)
            self.end_conversation()

    def handle_input(self, transcribed_text: str) -> Optional[str]:
        """Processes a transcribed command, executes it, and manages state.

        Args:
            transcribed_text: Plain text command transcribed from user speech.

        Returns:
            The plain text response from the execution or sign-off, or None.
        """
        if not transcribed_text:
            return None

        command = transcribed_text.strip().lower()
        session = self.get_active_session()

        # Case A: No active conversation session
        if session is None:
            wake_result = self.wake_word_detector(transcribed_text)
            if wake_result.get("activated", False):
                session = self.start_conversation()
                cleaned_cmd = wake_result.get("cleaned_command", "").strip()
                if cleaned_cmd:
                    # Proceed with command trailing the wake word immediately
                    return self._process_command(cleaned_cmd, session)
                return "Conversation started."
            return None

        # Case B: Active conversation session exists
        self.inactivity_timer.reset()
        session.last_active_time = time.time()

        # Check for exit commands
        if command in CONVERSATION_EXIT_COMMANDS:
            logger.info("Exit command '%s' received. Signing off.", command)
            try:
                self.tts_speaker("Goodbye.")
            except Exception as e:
                logger.error("Failed to speak exit response: %s", e)
            self.end_conversation()
            return "Goodbye."

        # Process standard command
        return self._process_command(command, session)

    def _process_command(
        self, command: str, session: ConversationSession
    ) -> str:
        """Internal helper to execute a command, update context, and play TTS.

        Args:
            command: Cleaned plain text command to execute.
            session: Active ConversationSession.

        Returns:
            Execution response string.
        """
        logger.info("Processing command: '%s'", command)
        session.state = ConversationState.PROCESSING
        session.context.last_command = command

        try:
            # Execute command using injected delegate
            response_text, context_updates = self.command_executor(
                command, session.context
            )

            # Update context parameters
            self._update_context(session.context, context_updates)
            session.context.last_response = response_text

            logger.info("Command result: '%s'", response_text)
            session.state = ConversationState.SPEAKING

            # Synthesize response voice
            self.tts_speaker(response_text)

            session.state = ConversationState.WAITING_FOR_RESPONSE
            self.inactivity_timer.reset()
            return response_text

        except Exception as e:
            logger.exception("Error executing command '%s': %s", command, e)
            session.state = ConversationState.ERROR
            err_msg = "An error occurred while processing your request."
            try:
                self.tts_speaker(err_msg)
            except Exception:
                pass
            session.state = ConversationState.WAITING_FOR_RESPONSE
            self.inactivity_timer.reset()
            return err_msg

    def _update_context(
        self, context: ConversationContext, updates: Dict[str, Any]
    ) -> None:
        """Helper to update conversation context attributes from dict updates."""
        if not updates:
            return

        if "current_file" in updates:
            context.current_file = updates["current_file"]
        if "current_folder" in updates:
            context.current_folder = updates["current_folder"]
        if "pending_confirmation" in updates:
            context.pending_confirmation = updates["pending_confirmation"]
        if "metadata" in updates and isinstance(updates["metadata"], dict):
            context.metadata.update(updates["metadata"])

    def run_conversation_step(self) -> bool:
        """Executes a single step of the conversation listening/running cycle.

        Returns:
            True if a step was processed, False if no input or error.
        """
        session = self.get_active_session()

        # Update state to LISTENING when actively reading microphone
        if session is not None:
            session.state = ConversationState.LISTENING

        try:
            logger.debug("Listening for voice input...")
            # Blocking/timeout capture via injected speech recognizer delegate
            result = self.speech_recognizer()

            if result is None or not getattr(result, "success", False):
                # Timeout or empty recording
                if session is not None and getattr(result, "error", "") == "Timeout: No speech detected":
                    logger.info("No speech detected. Handling timeout.")
                    # Will trigger timeout flow directly
                    self.handle_session_timeout()
                return False

            transcribed_text = getattr(result, "text", "")
            if not transcribed_text:
                return False

            self.handle_input(transcribed_text)
            return True

        except Exception as e:
            logger.error("Exception in conversation loop step: %s", e)
            if session is not None:
                session.state = ConversationState.ERROR
            return False
