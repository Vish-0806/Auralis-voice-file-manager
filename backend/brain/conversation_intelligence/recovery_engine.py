"""Recovers active context, workflows, routines, and pending tasks of interrupted sessions."""

from __future__ import annotations

import logging
from typing import Any, Optional

from brain.conversation_intelligence.models import DialogueState, DialoguePhase
from brain.conversation_intelligence.state_manager import DialogueStateManager

logger = logging.getLogger(__name__)


class ContextRecoveryEngine:
    """Manages dialogue state snapshots to recover aborted or interrupted routines and workflows."""

    def __init__(self, state_manager: DialogueStateManager) -> None:
        self._state_manager = state_manager

    def save_recovery_snapshot(
        self,
        session_id: str,
        active_workflow: Optional[str] = None,
        active_routine: Optional[str] = None,
        pending_execution: Optional[dict[str, Any]] = None,
        planning_context: Optional[dict[str, Any]] = None,
    ) -> None:
        """Stores a recovery snapshot inside the dialogue state metadata."""
        state = self._state_manager.get_state(session_id)
        snapshot = {
            "active_workflow": active_workflow,
            "active_routine": active_routine,
            "pending_execution": pending_execution,
            "planning_context": planning_context,
            "workspace": state.current_workspace,
            "timestamp": state.updated_at.isoformat(),
        }
        state.metadata["recovery_snapshot"] = snapshot
        self._state_manager.save_state(state)
        logger.info("Saved context recovery snapshot for session %s", session_id)

    def has_recovery_data(self, session_id: str) -> bool:
        """Checks if a session has an available recovery snapshot."""
        state = self._state_manager.get_state(session_id)
        return "recovery_snapshot" in state.metadata

    def recover_session(self, session_id: str) -> Optional[dict[str, Any]]:
        """Restores the dialogue state and returns the snapshot parameters to resume execution."""
        state = self._state_manager.get_state(session_id)
        snapshot = state.metadata.get("recovery_snapshot")
        if not snapshot:
            logger.info("No recovery snapshot found for session %s", session_id)
            return None

        logger.info("Recovering session %s from snapshot", session_id)

        # Restore active variables to state
        if snapshot.get("workspace"):
            state.current_workspace = snapshot["workspace"]
        if snapshot.get("active_workflow"):
            state.active_workflow = snapshot["active_workflow"]

        # If a pending execution exists, transition state phase to process it or clarify
        if snapshot.get("pending_execution"):
            state.phase = DialoguePhase.PROCESSING_TASK

        self._state_manager.save_state(state)
        return snapshot

    def clear_recovery_snapshot(self, session_id: str) -> None:
        """Purges any saved recovery data for a session."""
        state = self._state_manager.get_state(session_id)
        state.metadata.pop("recovery_snapshot", None)
        self._state_manager.save_state(state)
        logger.info("Cleared recovery snapshot for session %s", session_id)
