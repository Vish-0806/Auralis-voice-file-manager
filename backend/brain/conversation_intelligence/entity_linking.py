"""Links and resolves referenced files, folders, applications, and workflows across dialogue turns."""

from __future__ import annotations

import logging
from typing import Optional

from brain.conversation_intelligence.models import DialogueState, DialogueHistory

logger = logging.getLogger(__name__)


class EntityLinkingEngine:
    """Links nouns and references (e.g. 'it') to previously resolved concrete objects."""

    def register_entity(self, state: DialogueState, entity_type: str, value: str) -> None:
        """Stores a referenced entity value in dialogue metadata."""
        if "entities" not in state.metadata:
            state.metadata["entities"] = {}
        # Keep track of timestamps/order by updating the value
        state.metadata["entities"][entity_type] = {
            "value": value,
            "timestamp": state.updated_at.isoformat(),
        }
        logger.info("Registered entity of type %s: '%s'", entity_type, value)

    def get_last_referenced(
        self, entity_type: str, state: DialogueState, history: DialogueHistory
    ) -> Optional[str]:
        """Finds the most recently referenced entity of a given type."""
        # 1. Check current turn metadata in dialogue state
        entities = state.metadata.get("entities", {})
        if entity_type in entities:
            return entities[entity_type]["value"]

        # 2. Check dialogue state attributes
        if entity_type == "project" and state.current_workspace:
            return state.current_workspace
        if entity_type == "workflow" and state.active_workflow:
            return state.active_workflow
        if entity_type == "task" and state.active_task:
            return state.active_task

        # 3. Check history turns (newest to oldest)
        for turn in reversed(history.turns):
            # Check resolved objects
            if entity_type in turn.resolved_objects:
                return turn.resolved_objects[entity_type]
            # Check entities dictionary
            if entity_type in turn.entities:
                return turn.entities[entity_type]

        return None

    def resolve_pronoun(
        self, state: DialogueState, history: DialogueHistory
    ) -> tuple[Optional[str], Optional[str]]:
        """Resolves a general pronoun (like 'it') to the most recent concrete entity.

        Returns:
            A tuple of (resolved_value, entity_type), or (None, None) if not resolvable.
        """
        # We order entity types by reference priority: file, folder, application, workflow, project
        priority_types = ["file", "folder", "application", "workflow", "project"]

        # Find the latest referenced entity among these types
        latest_val = None
        latest_type = None
        latest_time = None

        entities = state.metadata.get("entities", {})
        for etype in priority_types:
            if etype in entities:
                val_data = entities[etype]
                # Compare timestamp string or check ordering
                val = val_data["value"]
                tstr = val_data["timestamp"]
                if latest_time is None or tstr > latest_time:
                    latest_val = val
                    latest_type = etype
                    latest_time = tstr

        if latest_val:
            return latest_val, latest_type

        # Fallback to history turns
        for turn in reversed(history.turns):
            # Check files/folders in resolved_objects or entities
            for etype in priority_types:
                if turn.resolved_objects.get(etype):
                    return turn.resolved_objects[etype], etype
                if turn.entities.get(etype):
                    return turn.entities[etype], etype

        # Check dialogue state direct variables
        if state.active_task:
            return state.active_task, "task"
        if state.active_workflow:
            return state.active_workflow, "workflow"
        if state.current_workspace:
            return state.current_workspace, "project"

        return None, None
