"""State Manager implementation for Auralis (Phase 13.3).

Maintains dialogue states, turn snapshots, dialogue metadata, and context merges.
Thread-safe using threading.RLock().
"""

from datetime import datetime, timezone
import logging
import threading
from typing import Any, Dict, List, Optional

from brain.assistant.dialogue.interfaces import IDialogueStateManager
from brain.assistant.dialogue.models import (
    DialogueContext,
    DialogueState,
    DialogueStatus,
    DialogueTurn,
)

logger = logging.getLogger(__name__)


class StateManager(IDialogueStateManager):
    """Thread-safe manager providing state snapshots, turn listings, and context updates."""

    def __init__(self, lock: Optional[threading.RLock] = None) -> None:
        self._lock = lock or threading.RLock()
        self._contexts: Dict[str, DialogueContext] = {}
        self._states: Dict[str, DialogueState] = {}
        self._turn_history: Dict[str, List[DialogueTurn]] = {}

    def record_turn(self, session_id: str, turn: DialogueTurn) -> None:
        """Record a turn into history and update dialogue state snapshot."""
        with self._lock:
            if session_id not in self._turn_history:
                self._turn_history[session_id] = []
            self._turn_history[session_id].append(turn)

            clarification = turn.metadata.get("clarification_prompt") if turn.requires_clarification else None
            confirmation = turn.metadata.get("confirmation_prompt") if turn.requires_confirmation else None

            status = DialogueStatus.PROCESSING
            if turn.requires_clarification:
                status = DialogueStatus.WAITING_FOR_CLARIFICATION
            elif turn.requires_confirmation:
                status = DialogueStatus.WAITING_FOR_CONFIRMATION

            state = DialogueState(
                status=status,
                current_turn=turn,
                turn_count=len(self._turn_history[session_id]),
                pending_clarification=clarification,
                pending_confirmation=confirmation,
                last_updated=datetime.now(timezone.utc),
            )
            self._states[session_id] = state

    def get_state(self, session_id: str) -> Optional[DialogueState]:
        """Retrieve current dialogue state snapshot."""
        with self._lock:
            return self._states.get(session_id)

    def update_context(
        self, session_id: str, context_updates: Dict[str, Any]
    ) -> DialogueContext:
        """Merge context updates into session dialogue context."""
        with self._lock:
            ctx = self._contexts.get(session_id) or DialogueContext(session_id=session_id)
            merged_vars = {**ctx.variables, **context_updates}
            updated = ctx.model_copy(update={"variables": merged_vars})
            self._contexts[session_id] = updated
            return updated

    def get_turns(self, session_id: str) -> List[DialogueTurn]:
        """Retrieve turn history for a session."""
        with self._lock:
            return list(self._turn_history.get(session_id, []))

    def clear(self) -> None:
        """Clear all stored dialogue states and turn histories."""
        with self._lock:
            self._contexts.clear()
            self._states.clear()
            self._turn_history.clear()
