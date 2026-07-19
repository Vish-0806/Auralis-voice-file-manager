"""Reference resolver service for parsing and replacing conversational references with concrete context entities."""

import logging
import re
from typing import Any, Dict, Optional
from memory.models.domain_models import AssistantContext
from brain.controller.models import ResolvedRequest

logger = logging.getLogger(__name__)


class ReferenceResolver:
    """Service that identifies and replaces conversational references (e.g. 'it', 'same folder')

    with concrete entity values sourced from the current AssistantContext state.
    """

    def __init__(self) -> None:
        """Initializes the ReferenceResolver."""
        pass

    def resolve(self, request_text: str, context: AssistantContext) -> ResolvedRequest:
        """Parses the request text, identifies references, and resolves them.

        Args:
            request_text: The raw user message.
            context: The current AssistantContext containing active and history details.

        Returns:
            A ResolvedRequest object.
        """
        if not request_text:
            return ResolvedRequest(
                original_request="",
                resolved_request="",
                resolved_entities={},
                confidence_score=0.0,
            )

        resolved_text = request_text
        resolved_entities: Dict[str, Any] = {}
        confidences = []

        # 1. Same Application / Same App
        app_match = re.search(
            r"\b(same application|same app)\b", resolved_text, re.IGNORECASE
        )
        if app_match:
            try:
                app_resolved = self._resolve_same_application(context)
                if app_resolved:
                    resolved_text = re.sub(
                        r"\b(same application|same app)\b",
                        lambda m: app_resolved,
                        resolved_text,
                        flags=re.IGNORECASE,
                    )
                    resolved_entities["application"] = app_resolved
                    confidences.append(1.0)
                else:
                    confidences.append(0.0)
            except Exception:
                logger.warning(
                    "Exception during application reference resolution",
                    exc_info=True,
                )
                confidences.append(0.0)

        # 2. Same Folder / Same Directory / Same Dir
        folder_match = re.search(
            r"\b(same folder|same directory|same dir)\b",
            resolved_text,
            re.IGNORECASE,
        )
        if folder_match:
            try:
                folder_resolved = self._resolve_same_folder(context)
                if folder_resolved:
                    resolved_text = re.sub(
                        r"\b(same folder|same directory|same dir)\b",
                        lambda m: folder_resolved,
                        resolved_text,
                        flags=re.IGNORECASE,
                    )
                    resolved_entities["folder"] = folder_resolved
                    confidences.append(1.0)
                else:
                    confidences.append(0.0)
            except Exception:
                logger.warning(
                    "Exception during folder reference resolution",
                    exc_info=True,
                )
                confidences.append(0.0)

        # 3. Same File
        file_match = re.search(
            r"\b(same file)\b", resolved_text, re.IGNORECASE
        )
        if file_match:
            try:
                file_resolved = self._resolve_same_file(context)
                if file_resolved:
                    resolved_text = re.sub(
                        r"\b(same file)\b",
                        lambda m: file_resolved,
                        resolved_text,
                        flags=re.IGNORECASE,
                    )
                    resolved_entities["file"] = file_resolved
                    confidences.append(1.0)
                else:
                    confidences.append(0.0)
            except Exception:
                logger.warning(
                    "Exception during file reference resolution", exc_info=True
                )
                confidences.append(0.0)

        # 4. Previous / Last One
        prev_match = re.search(
            r"\b(previous|last one)\b", resolved_text, re.IGNORECASE
        )
        if prev_match:
            try:
                prev_resolved = self._resolve_previous_target(context)
                if prev_resolved:
                    resolved_text = re.sub(
                        r"\b(previous|last one)\b",
                        lambda m: prev_resolved,
                        resolved_text,
                        flags=re.IGNORECASE,
                    )
                    resolved_entities["previous"] = prev_resolved
                    confidences.append(1.0)
                else:
                    confidences.append(0.0)
            except Exception:
                logger.warning(
                    "Exception during previous reference resolution",
                    exc_info=True,
                )
                confidences.append(0.0)

        # 5. Pronouns: it / them / this / that
        pronoun_match = re.search(
            r"\b(it|them|this|that)\b", resolved_text, re.IGNORECASE
        )
        if pronoun_match:
            try:
                pronoun_resolved = self._resolve_pronoun(context)
                if pronoun_resolved:
                    resolved_text = re.sub(
                        r"\b(it|them|this|that)\b",
                        lambda m: pronoun_resolved,
                        resolved_text,
                        flags=re.IGNORECASE,
                    )
                    resolved_entities["pronoun"] = pronoun_resolved
                    confidences.append(1.0)
                else:
                    confidences.append(0.0)
            except Exception:
                logger.warning(
                    "Exception during pronoun reference resolution",
                    exc_info=True,
                )
                confidences.append(0.0)

        # Compute overall confidence
        confidence = sum(confidences) / len(confidences) if confidences else 0.0

        return ResolvedRequest(
            original_request=request_text,
            resolved_request=resolved_text,
            resolved_entities=resolved_entities,
            confidence_score=confidence,
        )

    def _resolve_same_application(
        self, context: AssistantContext
    ) -> Optional[str]:
        # A. Check current context active window
        if context.current_context:
            win = context.current_context.metadata.additional_info.get(
                "active_window"
            )
            if win and isinstance(win, str) and win.strip():
                return win.strip()

        # B. Check recent executions for applications
        for execution in context.recent_executions:
            # Check action target
            action = execution.metadata.additional_info.get("action")
            if action in ["OPEN_APPLICATION", "CLOSE_APPLICATION"]:
                target = execution.metadata.additional_info.get(
                    "input_parameters", {}
                ).get("target")
                if target:
                    return str(target)
            # General parameter check
            params = execution.metadata.additional_info.get(
                "input_parameters", {}
            )
            for key in ["app", "app_name", "application", "program"]:
                if params.get(key):
                    return str(params[key])

        # C. Check recent conversations
        for conv in context.recent_conversations:
            match = re.search(
                r"\b(?:open|launch|start|run|focus)\s+([a-zA-Z0-9_\-\s]+)\b",
                conv.content,
                re.IGNORECASE,
            )
            if match:
                return match.group(1).strip()

        return None

    def _resolve_same_folder(self, context: AssistantContext) -> Optional[str]:
        # A. Check current context workspace path
        if context.current_context:
            path = context.current_context.metadata.additional_info.get(
                "workspace_path"
            )
            if not path:
                path = context.current_context.content
            if path and isinstance(path, str) and ("/" in path or "\\" in path):
                return path

        # B. Check workspace context path
        if context.workspace_context and context.workspace_context.content:
            return context.workspace_context.content

        # C. Check recent executions for path parameters
        for execution in context.recent_executions:
            params = execution.metadata.additional_info.get(
                "input_parameters", {}
            )
            for key in ["path", "directory", "folder", "dest", "source", "src"]:
                val = params.get(key)
                if val and isinstance(val, str) and ("/" in val or "\\" in val):
                    # Check if it looks like a folder (does not have dot-file extension at end)
                    if not re.search(r"\.[a-zA-Z0-9]{1,5}$", val):
                        return val

        return None

    def _resolve_same_file(self, context: AssistantContext) -> Optional[str]:
        # A. Check recent executions for file parameters
        for execution in context.recent_executions:
            params = execution.metadata.additional_info.get(
                "input_parameters", {}
            )
            for key in ["file", "filename", "file_path", "target", "src"]:
                val = params.get(key)
                if val and isinstance(val, str):
                    if re.search(r"\.[a-zA-Z0-9]{1,5}$", val):
                        return val

        # B. Check recent conversations for file names/paths
        for conv in context.recent_conversations:
            match = re.search(
                r"\b([a-zA-Z0-9_\-\/\\:]+\.[a-zA-Z0-9]{1,5})\b", conv.content
            )
            if match:
                return match.group(1)

        return None

    def _resolve_previous_target(
        self, context: AssistantContext
    ) -> Optional[str]:
        # Check last execution target
        if context.recent_executions:
            latest = context.recent_executions[0]
            params = latest.metadata.additional_info.get(
                "input_parameters", {}
            )
            for key in ["target", "file_path", "path", "app_name", "app"]:
                if params.get(key):
                    return str(params[key])

        # Check last conversation content
        if context.recent_conversations:
            latest = context.recent_conversations[0]
            match = re.search(
                r"\b(?:open|delete|create|move|run|copy|list|set)\s+([a-zA-Z0-9_\-\.\/\\:]+)\b",
                latest.content,
                re.IGNORECASE,
            )
            if match:
                return match.group(1).strip()

        return None

    def _resolve_pronoun(self, context: AssistantContext) -> Optional[str]:
        # Pronouns resolve to the target of the most recent action/execution
        return self._resolve_previous_target(context)
