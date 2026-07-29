"""Voice Orchestrator for the Auralis Voice Orchestration Engine (Phase 9.6).

Main entry point for the Voice Orchestration Engine.
Sequences: session management → confirmation guard → clarification guard →
           dispatch → feedback generation.

No reasoning, planning, filesystem, or speech synthesis.
"""

import logging
import threading
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional

from brain.voice.clarification_manager import ClarificationManager
from brain.voice.command_dispatcher import CommandDispatcher
from brain.voice.confirmation_manager import ConfirmationManager
from brain.voice.feedback_generator import FeedbackGenerator
from brain.voice.voice_models import (
    ConfirmationStatus,
    VoiceCommand,
    VoiceCommandStatus,
    VoiceInteractionResult,
    VoiceResponse,
    VoiceInteractionType,
    VoiceSessionState,
)
from brain.voice.voice_session import VoiceSession

logger = logging.getLogger(__name__)


class VoiceOrchestrator:
    """Thread-safe orchestrator for the complete voice interaction lifecycle.

    Responsibilities:
    - Create and track voice sessions.
    - Route commands through confirmation and clarification guards.
    - Dispatch confirmed, clarified commands into the Brain Pipeline.
    - Generate spoken feedback for every outcome.
    - Manage session lifecycle and cancellation.
    """

    def __init__(
        self,
        confirmation_manager: Optional[ConfirmationManager] = None,
        clarification_manager: Optional[ClarificationManager] = None,
        feedback_generator: Optional[FeedbackGenerator] = None,
        dispatcher: Optional[CommandDispatcher] = None,
    ) -> None:
        """Initialises VoiceOrchestrator.

        All dependencies are injectable for testability.

        Args:
            confirmation_manager: Confirmation workflow manager.
            clarification_manager: Clarification workflow manager.
            feedback_generator: Deterministic feedback generator.
            dispatcher: Brain pipeline dispatcher.
        """
        self._lock = threading.RLock()
        self._confirmation_manager = confirmation_manager or ConfirmationManager()
        self._clarification_manager = clarification_manager or ClarificationManager()
        self._feedback_generator = feedback_generator or FeedbackGenerator()
        self._dispatcher = dispatcher or CommandDispatcher()
        self._sessions: Dict[str, VoiceSession] = {}
        logger.debug("VoiceOrchestrator initialized")

    # ------------------------------------------------------------------
    # Session Management
    # ------------------------------------------------------------------

    def create_session(
        self,
        session_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> VoiceSession:
        """Create and register a new voice session.

        Args:
            session_id: Optional explicit session ID. Auto-generated if omitted.
            conversation_id: Optional associated conversation ID.

        Returns:
            New :class:`VoiceSession`.
        """
        with self._lock:
            session = VoiceSession(session_id=session_id, conversation_id=conversation_id)
            session.transition_state(VoiceSessionState.ACTIVE)
            self._sessions[session.session_id] = session
            return session

    def get_session(self, session_id: str) -> Optional[VoiceSession]:
        """Return a session by ID, or None.

        Args:
            session_id: Session to look up.

        Returns:
            :class:`VoiceSession` or None.
        """
        with self._lock:
            return self._sessions.get(session_id)

    def get_session_state(self, session_id: str) -> VoiceSessionState:
        """Return the current state of a session.

        Args:
            session_id: Session to inspect.

        Returns:
            :class:`VoiceSessionState` (ENDED if not found).
        """
        with self._lock:
            session = self._sessions.get(session_id)
            return session.state if session else VoiceSessionState.ENDED

    def list_sessions(self) -> list:
        """Return all session IDs.

        Returns:
            List of session ID strings.
        """
        with self._lock:
            return list(self._sessions.keys())

    # ------------------------------------------------------------------
    # Command Processing
    # ------------------------------------------------------------------

    def process_command(
        self,
        voice_command: VoiceCommand,
    ) -> VoiceInteractionResult:
        """Process a voice command through the full orchestration lifecycle.

        Flow:
        1. Retrieve or create the session.
        2. Record the command in session history.
        3. If confirmation required → request confirmation and return PENDING result.
        4. If clarification required → request clarification and return PENDING result.
        5. Dispatch into Brain Pipeline.
        6. Generate feedback.
        7. Return VoiceInteractionResult.

        Args:
            voice_command: Processed voice command from Voice Listener.

        Returns:
            Immutable :class:`VoiceInteractionResult`.
        """
        session = self._get_or_create_session(voice_command.session_id)
        session.record_command(voice_command)

        # --- Confirmation guard ---
        if voice_command.requires_confirmation:
            confirmation = self._confirmation_manager.request_confirmation(
                session_id=voice_command.session_id,
                prompt=self._build_confirmation_prompt(voice_command),
                command_id=voice_command.command_id,
            )
            session.set_pending_confirmation(confirmation)
            feedback = self._feedback_generator.generate_confirmation_request(
                prompt=confirmation.prompt,
                command=voice_command,
            )
            logger.info(
                "Confirmation Requested: session_id=%s command_id=%s",
                voice_command.session_id, voice_command.command_id,
            )
            return VoiceInteractionResult(
                command_id=voice_command.command_id,
                session_id=voice_command.session_id,
                success=True,
                status=VoiceCommandStatus.PENDING,
                feedback=feedback,
                confirmation_required=True,
                started_at=datetime.now(timezone.utc),
                finished_at=datetime.now(timezone.utc),
            )

        # --- Clarification guard ---
        if voice_command.requires_clarification:
            clarification = self._clarification_manager.request_clarification(
                session_id=voice_command.session_id,
                prompt=self._build_clarification_prompt(voice_command),
                options=list(voice_command.metadata.get("clarification_options", [])),
                command_id=voice_command.command_id,
            )
            session.set_pending_clarification(clarification)
            feedback = self._feedback_generator.generate_clarification_request(
                prompt=clarification.prompt,
                options=clarification.options,
                command=voice_command,
            )
            logger.info(
                "Clarification Requested: session_id=%s command_id=%s",
                voice_command.session_id, voice_command.command_id,
            )
            return VoiceInteractionResult(
                command_id=voice_command.command_id,
                session_id=voice_command.session_id,
                success=True,
                status=VoiceCommandStatus.PENDING,
                feedback=feedback,
                clarification_required=True,
                started_at=datetime.now(timezone.utc),
                finished_at=datetime.now(timezone.utc),
            )

        # --- Dispatch ---
        return self._dispatch_and_respond(voice_command, session)

    # ------------------------------------------------------------------
    # Confirmation Flow
    # ------------------------------------------------------------------

    def confirm(
        self,
        session_id: str,
        confirmation_id: str,
        accepted: bool,
    ) -> VoiceResponse:
        """Handle the user's response to a confirmation prompt.

        Args:
            session_id: Session performing the confirmation.
            confirmation_id: Target confirmation.
            accepted: True if accepted, False if rejected.

        Returns:
            Immutable :class:`VoiceResponse`.
        """
        session = self.get_session(session_id)
        if session is None:
            return _error_response(session_id, "Session not found.")

        if accepted:
            self._confirmation_manager.accept(confirmation_id)
            logger.info("Confirmation Accepted: session_id=%s confirmation_id=%s", session_id, confirmation_id)
            feedback = VoiceResponse(
                response_id=f"resp-{uuid.uuid4().hex[:8]}",
                session_id=session_id,
                text="Confirmed. Proceeding.",
                interaction_type=VoiceInteractionType.CONFIRMATION,
                success=True,
                created_at=datetime.now(timezone.utc),
            )
        else:
            self._confirmation_manager.reject(confirmation_id)
            logger.info("Confirmation Rejected: session_id=%s confirmation_id=%s", session_id, confirmation_id)
            feedback = VoiceResponse(
                response_id=f"resp-{uuid.uuid4().hex[:8]}",
                session_id=session_id,
                text="Understood. Operation cancelled.",
                interaction_type=VoiceInteractionType.CONFIRMATION,
                success=False,
                created_at=datetime.now(timezone.utc),
            )

        session.clear_pending_confirmation()
        return feedback

    # ------------------------------------------------------------------
    # Clarification Flow
    # ------------------------------------------------------------------

    def clarify(
        self,
        session_id: str,
        clarification_id: str,
        selected_option: str,
    ) -> VoiceResponse:
        """Handle the user's selection in a clarification prompt.

        Args:
            session_id: Session performing the clarification.
            clarification_id: Target clarification.
            selected_option: The option the user selected.

        Returns:
            Immutable :class:`VoiceResponse`.
        """
        session = self.get_session(session_id)
        if session is None:
            return _error_response(session_id, "Session not found.")

        self._clarification_manager.receive_response(clarification_id, selected_option)
        session.clear_pending_clarification()
        logger.info(
            "Clarification Received: session_id=%s clarification_id=%s selected=%s",
            session_id, clarification_id, selected_option,
        )
        return VoiceResponse(
            response_id=f"resp-{uuid.uuid4().hex[:8]}",
            session_id=session_id,
            text=f'Got it. Using "{selected_option}".',
            interaction_type=VoiceInteractionType.CLARIFICATION,
            success=True,
            created_at=datetime.now(timezone.utc),
        )

    # ------------------------------------------------------------------
    # Cancellation
    # ------------------------------------------------------------------

    def cancel_session(self, session_id: str) -> VoiceResponse:
        """Cancel an active session and all pending workflows.

        Args:
            session_id: Session to cancel.

        Returns:
            Immutable :class:`VoiceResponse`.
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return _error_response(session_id, "Session not found.")

            # Cancel any pending confirmation / clarification
            if session.pending_confirmation:
                self._confirmation_manager.cancel(session.pending_confirmation.confirmation_id)
            if session.pending_clarification:
                self._clarification_manager.cancel(session.pending_clarification.clarification_id)

            session.cancel()
            logger.info("Voice Session Ended: session_id=%s (user cancelled)", session_id)

            return VoiceResponse(
                response_id=f"resp-{uuid.uuid4().hex[:8]}",
                session_id=session_id,
                text="Operation cancelled.",
                interaction_type=VoiceInteractionType.CANCELLATION,
                success=True,
                created_at=datetime.now(timezone.utc),
            )

    def end_session(self, session_id: str) -> bool:
        """End a session cleanly.

        Args:
            session_id: Session to end.

        Returns:
            True if session was found and ended, False otherwise.
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return False
            session.end()
            logger.info("Voice Session Ended: session_id=%s", session_id)
            return True

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    def _get_or_create_session(self, session_id: str) -> VoiceSession:
        with self._lock:
            if session_id not in self._sessions:
                return self.create_session(session_id=session_id)
            session = self._sessions[session_id]
            if session.is_ended():
                # Re-create ended session
                return self.create_session(session_id=session_id)
            return session

    def _dispatch_and_respond(
        self,
        command: VoiceCommand,
        session: VoiceSession,
    ) -> VoiceInteractionResult:
        """Dispatch the command and attach feedback to the result."""
        session.transition_state(VoiceSessionState.PROCESSING)
        result = self._dispatcher.dispatch(command, conversation_id=session.conversation_id)
        feedback = self._feedback_generator.generate(command, result)
        # Attach feedback to result via model_copy
        result_with_feedback = result.model_copy(update={"feedback": feedback})
        session.transition_state(VoiceSessionState.IDLE)
        return result_with_feedback

    def _build_confirmation_prompt(self, command: VoiceCommand) -> str:
        """Build a confirmation prompt for the command."""
        text = command.normalized_text or command.raw_text
        return f'Are you sure you want to: "{text}"?'

    def _build_clarification_prompt(self, command: VoiceCommand) -> str:
        """Build a clarification prompt for an ambiguous command."""
        text = command.normalized_text or command.raw_text
        return f'I found multiple matches for "{text}". Which one did you mean?'


# ---------------------------------------------------------------------------
# Private Utilities
# ---------------------------------------------------------------------------

def _error_response(session_id: str, message: str) -> VoiceResponse:
    return VoiceResponse(
        response_id=f"resp-{uuid.uuid4().hex[:8]}",
        session_id=session_id,
        text=message,
        interaction_type=VoiceInteractionType.FEEDBACK,
        success=False,
        created_at=datetime.now(timezone.utc),
    )
