"""Voice Session for the Auralis Voice Orchestration Engine (Phase 9.6).

Manages the lifecycle and state of a single voice interaction session,
including pending confirmations, clarifications, and command history.
"""

import logging
import threading
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from brain.voice.voice_models import (
    VoiceCommand,
    VoiceConfirmation,
    VoiceClarification,
    VoiceSessionState,
)

logger = logging.getLogger(__name__)

# Valid state transitions
_VALID_TRANSITIONS: Dict[VoiceSessionState, List[VoiceSessionState]] = {
    VoiceSessionState.IDLE: [VoiceSessionState.ACTIVE, VoiceSessionState.ENDED],
    VoiceSessionState.ACTIVE: [
        VoiceSessionState.PROCESSING,
        VoiceSessionState.CONFIRMING,
        VoiceSessionState.CLARIFYING,
        VoiceSessionState.IDLE,
        VoiceSessionState.ENDED,
    ],
    VoiceSessionState.PROCESSING: [
        VoiceSessionState.ACTIVE,
        VoiceSessionState.IDLE,
        VoiceSessionState.ENDED,
    ],
    VoiceSessionState.CONFIRMING: [
        VoiceSessionState.ACTIVE,
        VoiceSessionState.PROCESSING,
        VoiceSessionState.IDLE,
        VoiceSessionState.ENDED,
    ],
    VoiceSessionState.CLARIFYING: [
        VoiceSessionState.ACTIVE,
        VoiceSessionState.PROCESSING,
        VoiceSessionState.IDLE,
        VoiceSessionState.ENDED,
    ],
    VoiceSessionState.ENDED: [],
}


class VoiceSession:
    """Thread-safe voice session tracking a single user voice interaction lifecycle.

    Responsibilities:
    - Track session state and apply valid transitions.
    - Hold the current pending confirmation and clarification.
    - Maintain command history.
    - Support cancellation and cleanup.
    """

    def __init__(
        self,
        session_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> None:
        """Initialises VoiceSession.

        Args:
            session_id: Optional explicit session ID. Auto-generated if omitted.
            conversation_id: Optional associated conversation / brain pipeline ID.
        """
        self._lock = threading.RLock()
        self.session_id: str = session_id or f"vs-{uuid.uuid4().hex[:8]}"
        self.conversation_id: Optional[str] = conversation_id
        self._state: VoiceSessionState = VoiceSessionState.IDLE
        self._pending_confirmation: Optional[VoiceConfirmation] = None
        self._pending_clarification: Optional[VoiceClarification] = None
        self._command_history: List[VoiceCommand] = []
        self.started_at: datetime = datetime.now(timezone.utc)
        self.ended_at: Optional[datetime] = None
        logger.info("Voice Session Started: session_id=%s", self.session_id)

    # ------------------------------------------------------------------
    # State Management
    # ------------------------------------------------------------------

    @property
    def state(self) -> VoiceSessionState:
        """Current session state."""
        with self._lock:
            return self._state

    def transition_state(self, new_state: VoiceSessionState) -> bool:
        """Transition to *new_state* if the transition is valid.

        Args:
            new_state: Target state.

        Returns:
            True if transition succeeded, False if invalid.
        """
        with self._lock:
            allowed = _VALID_TRANSITIONS.get(self._state, [])
            if new_state not in allowed:
                logger.warning(
                    "VoiceSession invalid transition: session_id=%s %s → %s",
                    self.session_id, self._state, new_state,
                )
                return False
            old_state = self._state
            self._state = new_state
            if new_state == VoiceSessionState.ENDED:
                self.ended_at = datetime.now(timezone.utc)
            logger.debug(
                "VoiceSession state transition: session_id=%s %s → %s",
                self.session_id, old_state, new_state,
            )
            return True

    def force_state(self, new_state: VoiceSessionState) -> None:
        """Force-set state without transition validation (internal use only).

        Args:
            new_state: Target state.
        """
        with self._lock:
            self._state = new_state
            if new_state == VoiceSessionState.ENDED:
                self.ended_at = datetime.now(timezone.utc)

    # ------------------------------------------------------------------
    # Confirmation
    # ------------------------------------------------------------------

    def set_pending_confirmation(self, confirmation: VoiceConfirmation) -> None:
        """Store a pending confirmation and transition to CONFIRMING.

        Args:
            confirmation: Confirmation to hold.
        """
        with self._lock:
            self._pending_confirmation = confirmation
            self.transition_state(VoiceSessionState.CONFIRMING)

    def clear_pending_confirmation(self) -> None:
        """Remove the pending confirmation and return to ACTIVE."""
        with self._lock:
            self._pending_confirmation = None
            if self._state == VoiceSessionState.CONFIRMING:
                self.transition_state(VoiceSessionState.ACTIVE)

    @property
    def pending_confirmation(self) -> Optional[VoiceConfirmation]:
        """Current pending confirmation, if any."""
        with self._lock:
            return self._pending_confirmation

    # ------------------------------------------------------------------
    # Clarification
    # ------------------------------------------------------------------

    def set_pending_clarification(self, clarification: VoiceClarification) -> None:
        """Store a pending clarification and transition to CLARIFYING.

        Args:
            clarification: Clarification to hold.
        """
        with self._lock:
            self._pending_clarification = clarification
            self.transition_state(VoiceSessionState.CLARIFYING)

    def clear_pending_clarification(self) -> None:
        """Remove the pending clarification and return to ACTIVE."""
        with self._lock:
            self._pending_clarification = None
            if self._state == VoiceSessionState.CLARIFYING:
                self.transition_state(VoiceSessionState.ACTIVE)

    @property
    def pending_clarification(self) -> Optional[VoiceClarification]:
        """Current pending clarification, if any."""
        with self._lock:
            return self._pending_clarification

    # ------------------------------------------------------------------
    # Command History
    # ------------------------------------------------------------------

    def record_command(self, command: VoiceCommand) -> None:
        """Append *command* to the session history.

        Args:
            command: Received voice command to record.
        """
        with self._lock:
            self._command_history.append(command)
            logger.debug(
                "VoiceSession command recorded: session_id=%s command_id=%s",
                self.session_id, command.command_id,
            )

    def get_command_history(self) -> List[VoiceCommand]:
        """Return a copy of the command history.

        Returns:
            List of :class:`VoiceCommand` objects.
        """
        with self._lock:
            return list(self._command_history)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def cancel(self) -> None:
        """Cancel the session idempotently, clearing all pending state."""
        with self._lock:
            self._pending_confirmation = None
            self._pending_clarification = None
            if self._state != VoiceSessionState.ENDED:
                self.force_state(VoiceSessionState.ENDED)
            logger.info("Voice Session Ended: session_id=%s (cancelled)", self.session_id)

    def end(self) -> None:
        """End the session cleanly."""
        with self._lock:
            self._pending_confirmation = None
            self._pending_clarification = None
            self.force_state(VoiceSessionState.ENDED)
            logger.info("Voice Session Ended: session_id=%s", self.session_id)

    # ------------------------------------------------------------------
    # State Helpers
    # ------------------------------------------------------------------

    def is_active(self) -> bool:
        """Return True if the session is in an active-interaction state."""
        with self._lock:
            return self._state in (
                VoiceSessionState.ACTIVE,
                VoiceSessionState.PROCESSING,
                VoiceSessionState.CONFIRMING,
                VoiceSessionState.CLARIFYING,
            )

    def is_idle(self) -> bool:
        """Return True if the session is idle."""
        with self._lock:
            return self._state == VoiceSessionState.IDLE

    def is_processing(self) -> bool:
        """Return True if the session is currently dispatching a command."""
        with self._lock:
            return self._state == VoiceSessionState.PROCESSING

    def is_ended(self) -> bool:
        """Return True if the session has ended."""
        with self._lock:
            return self._state == VoiceSessionState.ENDED

    def summary(self) -> Dict:
        """Return a non-frozen dict summary of session state for diagnostics."""
        with self._lock:
            return {
                "session_id": self.session_id,
                "conversation_id": self.conversation_id,
                "state": self._state.value,
                "command_count": len(self._command_history),
                "has_pending_confirmation": self._pending_confirmation is not None,
                "has_pending_clarification": self._pending_clarification is not None,
                "started_at": self.started_at.isoformat(),
                "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            }
