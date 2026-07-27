"""Resolves relative and pronoun-based follow-up commands using dialogue state."""

from __future__ import annotations

import logging
import re
from typing import Any, Optional

from brain.conversation_intelligence.models import DialogueState, DialogueHistory

logger = logging.getLogger(__name__)


class FollowUpResolver:
    """Resolves relative command references like 'open it', 'run again', 'same folder'."""

    def __init__(self, entity_linker: Any = None) -> None:
        self._entity_linker = entity_linker

    def is_followup(self, command: str) -> bool:
        """Determines if the command is a follow-up reference."""
        cmd_lower = command.lower().strip()
        relative_patterns = [
            r"\b(it|that|this|those)\b",
            r"\brun again\b",
            r"\bretry\b",
            r"\bcontinue\b",
            r"\bcancel it\b",
            r"\bsame (folder|directory|dir)\b",
            r"\bsame (project|workspace)\b",
        ]
        return any(re.search(pat, cmd_lower) for pat in relative_patterns)

    def resolve(
        self,
        command: str,
        state: DialogueState,
        history: DialogueHistory,
        assistant_context: Optional[Any] = None,
    ) -> tuple[str, dict[str, Any], bool, Optional[str]]:
        """Resolves relative references in the command.

        Returns:
            A tuple of:
            - resolved_command (str)
            - resolved_entities (dict)
            - requires_clarification (bool)
            - clarification_prompt (Optional[str])
        """
        cmd_lower = command.lower().strip()
        resolved_cmd = command
        resolved_entities: dict[str, Any] = {}

        # 1. Handle "cancel it" / "cancel"
        if cmd_lower == "cancel it" or cmd_lower == "cancel":
            return "cancel", {}, False, None

        # 2. Handle "run again" / "retry"
        if "run again" in cmd_lower or "retry" in cmd_lower:
            # Find last command from history
            last_user_cmd = None
            for turn in reversed(history.turns):
                if turn.role == "user" and not self.is_followup(turn.content):
                    last_user_cmd = turn.content
                    break

            if last_user_cmd:
                logger.info("Resolved 'run again' to last command: '%s'", last_user_cmd)
                return last_user_cmd, {}, False, None
            else:
                return (
                    command,
                    {},
                    True,
                    "I don't have a record of a previous command to run again.",
                )

        # 3. Handle "continue"
        if cmd_lower == "continue":
            if state.pending_clarification:
                # User wants to continue but has clarification pending, we prompt again
                return (
                    command,
                    {},
                    True,
                    state.pending_clarification.prompt,
                )
            if state.active_workflow:
                return f"continue workflow {state.active_workflow}", {"workflow": state.active_workflow}, False, None
            return "continue", {}, False, None

        # 4. Handle "same project" / "same workspace"
        proj_match = re.search(r"\b(same project|same workspace)\b", resolved_cmd, re.IGNORECASE)
        if proj_match:
            project_path = state.current_workspace
            if not project_path and assistant_context and assistant_context.workspace_context:
                project_path = assistant_context.workspace_context.content
            if project_path:
                resolved_cmd = re.sub(
                    r"\b(same project|same workspace)\b",
                    project_path,
                    resolved_cmd,
                    flags=re.IGNORECASE,
                )
                resolved_entities["project"] = project_path
            else:
                return (
                    command,
                    {},
                    True,
                    "I couldn't resolve the active project path. Which project do you mean?",
                )

        # 5. Handle "same folder" / "same directory" / "same dir"
        folder_match = re.search(r"\b(same folder|same directory|same dir)\b", resolved_cmd, re.IGNORECASE)
        if folder_match:
            # Check last referenced folder from linker or state or context
            folder_path = None
            if self._entity_linker:
                folder_path = self._entity_linker.get_last_referenced("folder", state, history)
            if not folder_path:
                folder_path = state.current_workspace
            if not folder_path and assistant_context:
                if assistant_context.current_context:
                    folder_path = assistant_context.current_context.metadata.additional_info.get("workspace_path")
                if not folder_path and assistant_context.workspace_context:
                    folder_path = assistant_context.workspace_context.content

            if folder_path:
                resolved_cmd = re.sub(
                    r"\b(same folder|same directory|same dir)\b",
                    folder_path,
                    resolved_cmd,
                    flags=re.IGNORECASE,
                )
                resolved_entities["folder"] = folder_path
            else:
                return (
                    command,
                    {},
                    True,
                    "I couldn't find an active directory in context. Which folder do you mean?",
                )

        # 6. Handle Pronouns: "it", "that", "this", "those"
        pronoun_match = re.search(r"\b(it|that|this|those)\b", resolved_cmd, re.IGNORECASE)
        if pronoun_match:
            pronoun = pronoun_match.group(1)
            # Ask the entity linker to resolve what the pronoun is referring to
            resolved_val = None
            ref_type = None

            if self._entity_linker:
                resolved_val, ref_type = self._entity_linker.resolve_pronoun(state, history)

            if not resolved_val and assistant_context:
                # Fallback to resolver behavior: check recent executions
                from brain.planning.reference_resolver import ReferenceResolver
                resolver = ReferenceResolver()
                resolved_val = resolver._resolve_previous_target(assistant_context)
                ref_type = "file" if resolved_val and "." in resolved_val else "folder"

            if resolved_val:
                resolved_cmd = re.sub(
                    rf"\b{pronoun}\b",
                    resolved_val,
                    resolved_cmd,
                    flags=re.IGNORECASE,
                )
                resolved_entities[ref_type or "pronoun"] = resolved_val
            else:
                # Ambiguity: could not resolve pronoun target
                return (
                    command,
                    {},
                    True,
                    "I couldn't resolve what you're referring to. Which file or folder do you mean?",
                )

        return resolved_cmd, resolved_entities, False, None
