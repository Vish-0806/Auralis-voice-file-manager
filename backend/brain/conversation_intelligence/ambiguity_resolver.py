"""Detects and resolves ambiguities in user commands (e.g., multiple matching files)."""

from __future__ import annotations

import logging
import os
import re
from typing import Any, Optional
import uuid

from brain.conversation_intelligence.models import DialogueState, PendingClarification
from automation.workflow.workflow_registry import WorkflowRegistry

logger = logging.getLogger(__name__)


class AmbiguityResolver:
    """Detects ambiguity in commands and generates PendingClarification requests."""

    def __init__(self, search_engine: Any = None) -> None:
        self._search_engine = search_engine

    def resolve_ambiguity(
        self,
        command: str,
        resolved_entities: dict[str, Any],
        state: DialogueState,
        assistant_context: Optional[Any] = None,
    ) -> Optional[PendingClarification]:
        """Scans the command and entities for ambiguities.

        Returns a PendingClarification if ambiguity is detected, otherwise None.
        """
        # 1. Check for workflow ambiguity
        workflow_target = resolved_entities.get("workflow") or self._extract_workflow_candidate(command)
        if workflow_target:
            registry = WorkflowRegistry()
            all_workflows = list(registry.list_workflows())
            matching_workflows = list(set([
                wf.name for wf in all_workflows
                if workflow_target.lower() in wf.name.lower()
            ]))
            if len(matching_workflows) > 1:
                logger.info("Ambiguity detected for workflow: %s matched %s", workflow_target, matching_workflows)
                options = sorted(matching_workflows)
                prompt = f"I found multiple workflows matching '{workflow_target}': {', '.join(options)}. Which one did you mean?"
                return PendingClarification(
                    clarification_id=f"clar_{uuid.uuid4().hex[:8]}",
                    parameter_name="workflow",
                    original_value=workflow_target,
                    options=options,
                    prompt=prompt,
                    command_to_resume=command,
                )

        # 2. Check for project/workspace ambiguity
        project_target = resolved_entities.get("project") or self._extract_project_candidate(command)
        if project_target:
            # Check user workspace profiles if any, or mock folders
            # Let's say we check folder directories in some default locations
            workspace_roots = []
            if assistant_context and hasattr(assistant_context, "preferences"):
                # Simulating workspace scanning or using preferences
                pass
            
            # Simple simulation: let's say we have multiple projects matching a name in standard places
            # If the project target is a simple name, check if it matches multiple directories in workspace context
            active_root = state.current_workspace
            if not active_root and assistant_context and assistant_context.workspace_context:
                active_root = assistant_context.workspace_context.content

            if active_root and os.path.exists(active_root):
                try:
                    candidates = []
                    for name in os.listdir(active_root):
                        full_path = os.path.join(active_root, name)
                        if os.path.isdir(full_path) and project_target.lower() in name.lower():
                            candidates.append(full_path)
                    if len(candidates) > 1:
                        logger.info("Ambiguity detected for project: %s matched %s", project_target, candidates)
                        options = sorted(candidates)
                        prompt = f"I found multiple directories matching project '{project_target}': {', '.join(options)}. Which directory did you mean?"
                        return PendingClarification(
                            clarification_id=f"clar_{uuid.uuid4().hex[:8]}",
                            parameter_name="project",
                            original_value=project_target,
                            options=options,
                            prompt=prompt,
                            command_to_resume=command,
                        )
                except Exception:
                    pass

        # 3. Check for application ambiguity
        app_target = resolved_entities.get("application") or self._extract_app_candidate(command)
        if app_target:
            # Let's say we have multiple browser or editor choices
            known_apps = ["Google Chrome", "Mozilla Firefox", "Microsoft Edge", "Visual Studio Code", "Notepad"]
            matching_apps = [
                app for app in known_apps
                if app_target.lower() in app.lower()
            ]
            if len(matching_apps) > 1:
                logger.info("Ambiguity detected for application: %s matched %s", app_target, matching_apps)
                options = sorted(matching_apps)
                prompt = f"I found multiple applications matching '{app_target}': {', '.join(options)}. Which one did you mean?"
                return PendingClarification(
                    clarification_id=f"clar_{uuid.uuid4().hex[:8]}",
                    parameter_name="application",
                    original_value=app_target,
                    options=options,
                    prompt=prompt,
                    command_to_resume=command,
                )

        # 4. Check for file ambiguity (most common)
        file_target = resolved_entities.get("file") or self._extract_file_candidate(command)
        if file_target:
            # Determine the search scope/root
            search_dirs = []
            active_root = state.current_workspace
            if not active_root and assistant_context and assistant_context.workspace_context:
                active_root = assistant_context.workspace_context.content
            if active_root and os.path.exists(active_root):
                search_dirs.append(active_root)

            # Also search default folders via SearchEngine/PathResolver if empty
            if self._search_engine:
                try:
                    for root_path in self._search_engine._resolve_scope_roots():
                        if root_path and root_path.exists():
                            search_dirs.append(str(root_path.resolve()))
                except Exception:
                    pass

            if not search_dirs:
                # Fallback search dirs
                search_dirs = [os.getcwd()]

            matches = []
            for d in search_dirs:
                try:
                    for root, _, files in os.walk(d):
                        for f in files:
                            # Exact match or contains match depending on specific query
                            if f.lower() == file_target.lower() or (
                                "." in file_target and f.lower().endswith(file_target.lower())
                            ):
                                matches.append(os.path.join(root, f))
                except Exception:
                    pass

            matches = list(set(matches))  # deduplicate
            if len(matches) > 1:
                logger.info("Ambiguity detected for file: %s matched %s", file_target, matches)
                options = sorted(matches)
                prompt = f"I found multiple files matching '{file_target}': {', '.join(options)}. Which file did you mean?"
                return PendingClarification(
                    clarification_id=f"clar_{uuid.uuid4().hex[:8]}",
                    parameter_name="file",
                    original_value=file_target,
                    options=options,
                    prompt=prompt,
                    command_to_resume=command,
                )

        return None

    def _extract_file_candidate(self, command: str) -> Optional[str]:
        """Extracts candidate file name from command using simple regex."""
        # Match anything that looks like a file extension (e.g. notes.txt, script.py, etc.)
        match = re.search(r"\b([a-zA-Z0-9_\-\/\\:]+\.[a-zA-Z0-9]{1,5})\b", command)
        if match:
            return match.group(1)
        return None

    def _extract_workflow_candidate(self, command: str) -> Optional[str]:
        """Extracts candidate workflow from command."""
        match = re.search(r"\b(?:workflow|run|start|execute)\s+([a-zA-Z0-9_\-\s]{3,})\b", command, re.IGNORECASE)
        if match:
            cand = match.group(1).strip()
            # filter out common verbs/prepositions
            if cand not in ["mode", "job", "task", "process"]:
                return cand
        return None

    def _extract_project_candidate(self, command: str) -> Optional[str]:
        """Extracts candidate project from command."""
        match = re.search(r"\b(?:project|workspace|directory)\s+([a-zA-Z0-9_\-\s]{3,})\b", command, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    def _extract_app_candidate(self, command: str) -> Optional[str]:
        """Extracts candidate application from command."""
        match = re.search(r"\b(?:app|application|open|launch|close)\s+([a-zA-Z0-9_\-\s]{3,})\b", command, re.IGNORECASE)
        if match:
            cand = match.group(1).strip()
            if cand not in ["mode", "file", "folder", "directory"]:
                return cand
        return None
