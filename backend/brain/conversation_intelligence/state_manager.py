"""Manages active dialogue states and transitions for the session."""

from __future__ import annotations

import logging
from typing import Any, Optional
from datetime import datetime, timezone

from brain.conversation_intelligence.models import DialogueState, DialoguePhase, PendingClarification

logger = logging.getLogger(__name__)


class DialogueStateManager:
    """Manages active dialogue state, variables, and transitions."""

    def __init__(self, persistence_manager: Any = None) -> None:
        """Initializes state manager with an optional persistence layer."""
        self._persistence = persistence_manager
        self._in_memory_states: dict[str, DialogueState] = {}

    def get_state(self, session_id: str) -> DialogueState:
        """Retrieves or initializes the dialogue state for a session."""
        if self._persistence:
            try:
                state = self._persistence.load_state(session_id)
                if state:
                    self._in_memory_states[session_id] = state
                    return state
            except Exception as e:
                logger.error("Failed to load state from persistence for session %s: %s", session_id, e)

        if session_id not in self._in_memory_states:
            self._in_memory_states[session_id] = DialogueState(session_id=session_id)
        return self._in_memory_states[session_id]

    def save_state(self, state: DialogueState) -> None:
        """Saves the dialogue state to memory and persistence."""
        state.updated_at = datetime.now(timezone.utc)
        self._in_memory_states[state.session_id] = state

        if self._persistence:
            try:
                self._persistence.save_state(state)
            except Exception as e:
                logger.error("Failed to save state to persistence for session %s: %s", state.session_id, e)

    def transition_phase(self, session_id: str, phase: DialoguePhase) -> DialogueState:
        """Transitions the conversation flow phase."""
        state = self.get_state(session_id)
        logger.info("Transitioning session %s phase from %s to %s", session_id, state.phase.value, phase.value)
        state.phase = phase
        self.save_state(state)
        return state

    def set_active_task(self, session_id: str, task: Optional[str]) -> DialogueState:
        """Sets the current active task context."""
        state = self.get_state(session_id)
        state.active_task = task
        if task:
            state.phase = DialoguePhase.PROCESSING_TASK
        self.save_state(state)
        return state

    def set_active_workflow(self, session_id: str, workflow: Optional[str]) -> DialogueState:
        """Sets the current active workflow context."""
        state = self.get_state(session_id)
        state.active_workflow = workflow
        self.save_state(state)
        return state

    def set_workspace(self, session_id: str, workspace_path: Optional[str]) -> DialogueState:
        """Sets the active workspace path."""
        state = self.get_state(session_id)
        state.current_workspace = workspace_path
        self.save_state(state)
        return state

    def set_pending_clarification(
        self, session_id: str, clarification: Optional[PendingClarification]
    ) -> DialogueState:
        """Saves or clears a pending clarification, updating phase accordingly."""
        state = self.get_state(session_id)
        state.pending_clarification = clarification
        if clarification:
            state.phase = DialoguePhase.WAITING_FOR_CLARIFICATION
        elif state.phase == DialoguePhase.WAITING_FOR_CLARIFICATION:
            state.phase = DialoguePhase.IDLE
        self.save_state(state)
        return state

    def clear_state(self, session_id: str) -> None:
        """Evicts active states for a session."""
        self._in_memory_states.pop(session_id, None)
        if self._persistence:
            try:
                self._persistence.delete_state(session_id)
            except Exception as e:
                logger.error("Failed to delete state in persistence for session %s: %s", session_id, e)
