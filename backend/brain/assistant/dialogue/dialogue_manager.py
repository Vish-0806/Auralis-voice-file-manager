"""Dialogue Manager implementation for Auralis (Phase 13.3).

Manages dialogue sessions, turn creation, state transitions, and dialogue flow validation.
Thread-safe using threading.RLock().
"""

from datetime import datetime, timezone
import logging
import threading
from typing import Any, Dict, List, Optional

from brain.assistant.dialogue.exceptions import (
    DialogueSessionError,
    DialogueStateError,
    DialogueValidationError,
)
from brain.assistant.dialogue.interfaces import IDialogueManager
from brain.assistant.dialogue.models import (
    DialogueAction,
    DialogueContext,
    DialogueMode,
    DialoguePolicy,
    DialogueSession,
    DialogueStatus,
    DialogueTurn,
)

logger = logging.getLogger(__name__)


class DialogueManager(IDialogueManager):
    """Thread-safe manager handling dialogue session lifecycle, turn registration, and state machine transitions."""

    def __init__(self, lock: Optional[threading.RLock] = None) -> None:
        self._lock = lock or threading.RLock()
        self._sessions: Dict[str, DialogueSession] = {}

    def create_session(
        self,
        conversation_id: Optional[str] = None,
        mode: DialogueMode = DialogueMode.DEFAULT,
        policy: Optional[DialoguePolicy] = None,
        context: Optional[DialogueContext] = None,
    ) -> DialogueSession:
        """Create and register a new dialogue session."""
        with self._lock:
            pol = policy or DialoguePolicy()
            ctx = context or DialogueContext(conversation_id=conversation_id)
            if conversation_id and not ctx.conversation_id:
                ctx = ctx.model_copy(update={"conversation_id": conversation_id})

            sess = DialogueSession(
                conversation_id=conversation_id,
                status=DialogueStatus.IDLE,
                mode=mode,
                turns=[],
                context=ctx,
                policy=pol,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            # Bind session_id to context
            bound_ctx = sess.context.model_copy(update={"session_id": sess.session_id})
            final_sess = sess.model_copy(update={"context": bound_ctx})

            self._sessions[final_sess.session_id] = final_sess
            logger.debug("Created dialogue session id=%s conv_id=%s", final_sess.session_id, conversation_id)
            return final_sess

    def get_session(self, session_id: str) -> Optional[DialogueSession]:
        """Retrieve a dialogue session by ID."""
        with self._lock:
            return self._sessions.get(session_id)

    def create_turn(
        self,
        session_id: str,
        user_input: str,
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DialogueTurn:
        """Create and append a new dialogue turn to a session.

        Raises:
            DialogueSessionError: If session_id is not found.
            DialogueValidationError: If user_input is empty.
        """
        if not user_input or not user_input.strip():
            raise DialogueValidationError("user_input cannot be empty")

        with self._lock:
            sess = self._sessions.get(session_id)
            if sess is None:
                raise DialogueSessionError(f"Dialogue session '{session_id}' not found")

            turn_num = len(sess.turns) + 1
            turn = DialogueTurn(
                session_id=session_id,
                turn_number=turn_num,
                user_input=user_input,
                confidence=confidence,
                started_at=datetime.now(timezone.utc),
                metadata=metadata or {},
            )

            updated_turns = list(sess.turns) + [turn]
            updated_sess = sess.model_copy(
                update={
                    "turns": updated_turns,
                    "status": DialogueStatus.PROCESSING,
                    "updated_at": datetime.now(timezone.utc),
                }
            )
            self._sessions[session_id] = updated_sess
            logger.debug("Created turn #%d for session %s", turn_num, session_id)
            return turn

    def update_status(
        self, session_id: str, new_status: DialogueStatus
    ) -> DialogueSession:
        """Update dialogue session status with state machine transition validation."""
        with self._lock:
            sess = self._sessions.get(session_id)
            if sess is None:
                raise DialogueSessionError(f"Dialogue session '{session_id}' not found")

            curr_status = sess.status
            if curr_status == DialogueStatus.COMPLETED and new_status != DialogueStatus.COMPLETED:
                raise DialogueStateError(
                    f"Cannot transition session '{session_id}' from COMPLETED to {new_status}"
                )

            updated = sess.model_copy(
                update={
                    "status": new_status,
                    "updated_at": datetime.now(timezone.utc),
                }
            )
            self._sessions[session_id] = updated
            logger.debug("Updated session '%s' status: %s -> %s", session_id, curr_status, new_status)
            return updated

    def complete_turn(
        self,
        session_id: str,
        turn_id: str,
        system_response: str,
        completed_status: DialogueStatus = DialogueStatus.IDLE,
    ) -> DialogueTurn:
        """Mark a dialogue turn complete with system response text."""
        with self._lock:
            sess = self._sessions.get(session_id)
            if sess is None:
                raise DialogueSessionError(f"Dialogue session '{session_id}' not found")

            target_turn: Optional[DialogueTurn] = None
            updated_turns: List[DialogueTurn] = []

            for turn in sess.turns:
                if turn.turn_id == turn_id:
                    target_turn = turn.model_copy(
                        update={
                            "system_response": system_response,
                            "completed_at": datetime.now(timezone.utc),
                        }
                    )
                    updated_turns.append(target_turn)
                else:
                    updated_turns.append(turn)

            if target_turn is None:
                raise DialogueSessionError(f"Turn '{turn_id}' not found in session '{session_id}'")

            updated_sess = sess.model_copy(
                update={
                    "turns": updated_turns,
                    "status": completed_status,
                    "updated_at": datetime.now(timezone.utc),
                }
            )
            self._sessions[session_id] = updated_sess
            return target_turn

    def list_sessions(
        self, status: Optional[DialogueStatus] = None
    ) -> List[DialogueSession]:
        """List all active or filtered dialogue sessions."""
        with self._lock:
            if status is None:
                return list(self._sessions.values())
            return [s for s in self._sessions.values() if s.status == status]

    def clear(self) -> None:
        """Clear all registered dialogue sessions."""
        with self._lock:
            self._sessions.clear()
