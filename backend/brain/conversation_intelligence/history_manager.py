"""Manages session dialogue history, including entity extraction references and branching."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional
import uuid

from brain.conversation_intelligence.models import DialogueHistory, DialogueTurn

logger = logging.getLogger(__name__)


class DialogueHistoryManager:
    """Manages long-running dialogue histories, turns, entities, and branches."""

    def __init__(self, persistence_manager: Any = None) -> None:
        self._persistence = persistence_manager
        self._in_memory_histories: dict[str, DialogueHistory] = {}

    def get_history(self, session_id: str) -> DialogueHistory:
        """Retrieves or initializes dialogue history for a session."""
        if self._persistence:
            try:
                hist = self._persistence.load_history(session_id)
                if hist:
                    self._in_memory_histories[session_id] = hist
                    return hist
            except Exception as e:
                logger.error("Failed to load history from persistence for session %s: %s", session_id, e)

        if session_id not in self._in_memory_histories:
            self._in_memory_histories[session_id] = DialogueHistory(session_id=session_id)
        return self._in_memory_histories[session_id]

    def save_history(self, history: DialogueHistory) -> None:
        """Saves the dialogue history to memory and persistence."""
        self._in_memory_histories[history.session_id] = history
        if self._persistence:
            try:
                self._persistence.save_history(history)
            except Exception as e:
                logger.error("Failed to save history to persistence for session %s: %s", history.session_id, e)

    def add_turn(
        self,
        session_id: str,
        role: str,
        content: str,
        entities: Optional[dict[str, Any]] = None,
        resolved_objects: Optional[dict[str, Any]] = None,
        branch_id: Optional[str] = None,
    ) -> DialogueTurn:
        """Appends a dialogue turn to either the main branch or a specific sub-branch."""
        history = self.get_history(session_id)
        turn = DialogueTurn(
            turn_id=f"turn_{uuid.uuid4().hex[:8]}",
            role=role,
            content=content,
            timestamp=datetime.now(timezone.utc),
            entities=entities or {},
            resolved_objects=resolved_objects or {},
        )

        if branch_id:
            if branch_id not in history.branches:
                history.branches[branch_id] = []
            history.branches[branch_id].append(turn)
            logger.info("Added turn %s to branch %s", turn.turn_id, branch_id)
        else:
            history.turns.append(turn)
            logger.info("Added turn %s to main conversation path", turn.turn_id)

        self.save_history(history)
        return turn

    def start_branch(self, session_id: str, branch_id: str) -> None:
        """Initializes a new conversation branch."""
        history = self.get_history(session_id)
        if branch_id not in history.branches:
            history.branches[branch_id] = []
            self.save_history(history)
            logger.info("Started dialogue branch %s for session %s", branch_id, session_id)

    def get_branch_turns(self, session_id: str, branch_id: str) -> list[DialogueTurn]:
        """Retrieves turns of a specific branch, fallback to empty list."""
        history = self.get_history(session_id)
        return history.branches.get(branch_id, [])

    def clear_history(self, session_id: str) -> None:
        """Clears the history log for a session."""
        self._in_memory_histories.pop(session_id, None)
        if self._persistence:
            try:
                self._persistence.delete_history(session_id)
            except Exception as e:
                logger.error("Failed to delete history in persistence for session %s: %s", session_id, e)
