"""Planner contracts and keyword-based request analysis for Auralis.

This module implements the core planning boundary only. It converts an
AssistantRequest into a structured ExecutionPlan using lightweight keyword
parsing and simple heuristics. No AI services, file operations, or execution
side effects are performed here.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Final

from .exceptions import ValidationException
from .interfaces import IPlanner
from .intents import Intent
from .models import AssistantRequest, ExecutionPlan as CoreExecutionPlan, SessionContext

ExecutionPlan = CoreExecutionPlan


class Planner(IPlanner):
    """Builds simple execution plans from assistant requests.

    The planner uses only deterministic keyword parsing so it remains fully
    unit-testable and independent from any language model or execution engine.
    """

    SUPPORTED_INTENTS: Final[tuple[Intent, ...]] = (
        Intent.OPEN_FOLDER,
        Intent.OPEN_FILE,
        Intent.SEARCH_FILE,
        Intent.LIST_DIRECTORY,
        Intent.CREATE_FOLDER,
        Intent.DELETE_FOLDER,
        Intent.UNKNOWN,
    )

    _FOLDER_NAMES: Final[tuple[str, ...]] = (
        "desktop",
        "downloads",
        "documents",
        "pictures",
        "music",
        "videos",
    )

    _OPEN_FOLDER_HINTS: Final[tuple[str, ...]] = (
        "open folder",
        "open the folder",
        "go to folder",
        "navigate to folder",
        "show folder",
    )

    _OPEN_FILE_HINTS: Final[tuple[str, ...]] = (
        "open file",
        "open the file",
        "open document",
        "open the document",
    )

    _SEARCH_FILE_HINTS: Final[tuple[str, ...]] = (
        "search file",
        "find file",
        "look for file",
        "search for",
        "find",
    )

    _LIST_DIRECTORY_HINTS: Final[tuple[str, ...]] = (
        "list directory",
        "list folder",
        "show directory",
        "show files in",
        "list files in",
        "show contents",
        "list contents",
    )

    _CREATE_FOLDER_HINTS: Final[tuple[str, ...]] = (
        "create folder",
        "create a folder",
        "make folder",
        "make a folder",
        "new folder",
        "create directory",
        "make directory",
    )

    _DELETE_FOLDER_HINTS: Final[tuple[str, ...]] = (
        "delete folder",
        "delete the folder",
        "remove folder",
        "remove the folder",
        "trash folder",
        "discard folder",
    )

    _FILE_EXTENSION_PATTERN: Final[re.Pattern[str]] = re.compile(
        r"\b[^\s<>:\"'|?*]+\.(?:txt|md|pdf|docx|doc|csv|xlsx|xls|json|yaml|yml|png|jpg|jpeg|gif|mp3|wav|mp4|zip)\b",
        re.IGNORECASE,
    )

    _QUOTED_TEXT_PATTERN: Final[re.Pattern[str]] = re.compile(
        r'"([^"]+)"|\'([^\']+)\'',
    )

    def __init__(
        self,
        agent_brain: Any | None = None,
        event_bus: Any | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initializes the planner.

        Args:
            agent_brain: Retained for compatibility with the current codebase.
            event_bus: Retained for compatibility with the current codebase.
            logger: Optional logger used for planner diagnostics.
        """

        self._agent_brain = agent_brain
        self._event_bus = event_bus
        self._logger = logger or logging.getLogger(__name__)

    def create_plan(
        self,
        request: AssistantRequest,
        context: SessionContext | None = None,
    ) -> ExecutionPlan:
        """Creates a structured execution plan from a user request.

        Args:
            request: The incoming assistant request.
            context: Optional session context for future extensibility.

        Returns:
            A validated ExecutionPlan populated with intent, target, and
            confidence metadata.

        Raises:
            ValidationException: If the request is missing a usable message.
        """

        self._validate_request(request)

        normalized_message = self._normalize_text(request.message)
        intent = self._detect_intent(normalized_message)

        folder_name = None
        destination_folder = None
        if intent == Intent.CREATE_FOLDER:
            folder_name, destination_folder = self._extract_folder_info_from_message(request.message)
            target = folder_name
        elif intent == Intent.DELETE_FOLDER:
            folder_name = self._extract_delete_folder_info_from_message(request.message)
            target = folder_name
        else:
            target = self._extract_target(normalized_message, intent)

        confidence = self._calculate_confidence(normalized_message, intent, target)

        parameters: dict[str, Any] = {
            "source": request.source,
            "normalized_message": normalized_message,
        }
        if context is not None:
            parameters["session_context"] = context.model_dump()
        if target is not None:
            parameters["target"] = target

        if intent == Intent.CREATE_FOLDER:
            parameters["folder_name"] = folder_name
            parameters["destination_folder"] = destination_folder
        elif intent == Intent.DELETE_FOLDER:
            parameters["folder_name"] = folder_name

        plan = ExecutionPlan(
            intent=intent,
            target=target,
            parameters=parameters,
            confidence=confidence,
        )

        self._logger.debug(
            "Created execution plan",
            extra={
                "intent": intent.value,
                "target": target,
                "confidence": confidence,
            },
        )
        return plan

    def validate_plan(self, plan: ExecutionPlan) -> bool:
        """Validates that a plan is structurally ready for downstream use.

        Args:
            plan: The execution plan to validate.

        Returns:
            True when the plan is valid, otherwise False.
        """

        if not isinstance(plan, CoreExecutionPlan):
            return False

        if plan.intent not in self.SUPPORTED_INTENTS:
            return False

        if not 0.0 <= plan.confidence <= 1.0:
            return False

        if not isinstance(plan.parameters, dict):
            return False

        if plan.target is not None and not plan.target.strip():
            return False

        return True

    def _validate_request(self, request: AssistantRequest) -> None:
        """Validates the incoming request object.

        Args:
            request: The assistant request to validate.

        Raises:
            ValidationException: If the request is not usable.
        """

        if not isinstance(request, AssistantRequest):
            raise ValidationException("Request must be an AssistantRequest instance.")

        if not request.message or not request.message.strip():
            raise ValidationException("Request message cannot be empty.")

        if not request.source or not request.source.strip():
            raise ValidationException("Request source cannot be empty.")

    def _normalize_text(self, text: str) -> str:
        """Normalizes request text for deterministic keyword matching.

        Args:
            text: The raw request message.

        Returns:
            A lower-cased, whitespace-normalized string.
        """

        normalized = text.strip().lower()
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized

    def _detect_intent(self, normalized_message: str) -> Intent:
        """Detects the most likely supported intent.

        Args:
            normalized_message: The normalized request text.

        Returns:
            One of the supported intent labels.
        """

        if self._contains_any(normalized_message, self._CREATE_FOLDER_HINTS):
            return Intent.CREATE_FOLDER

        if self._contains_any(normalized_message, self._DELETE_FOLDER_HINTS):
            return Intent.DELETE_FOLDER

        if self._looks_like_open_file_request(normalized_message):
            return Intent.OPEN_FILE

        if self._looks_like_open_folder_request(normalized_message):
            return Intent.OPEN_FOLDER

        if self._contains_any(normalized_message, self._LIST_DIRECTORY_HINTS):
            return Intent.LIST_DIRECTORY

        if self._contains_any(normalized_message, self._SEARCH_FILE_HINTS):
            return Intent.SEARCH_FILE

        if self._looks_like_file_request(normalized_message):
            return Intent.OPEN_FILE

        if self._looks_like_directory_request(normalized_message):
            return Intent.LIST_DIRECTORY

        return Intent.UNKNOWN

    def _extract_target(self, normalized_message: str, intent: Intent) -> str | None:
        """Extracts a likely target from the normalized request.

        Args:
            normalized_message: The normalized request text.
            intent: The detected intent.

        Returns:
            A likely file or folder target, or None when no clear target exists.
        """

        quoted_target = self._extract_quoted_text(normalized_message)
        if quoted_target:
            return quoted_target

        explicit_folder = self._extract_folder_name(normalized_message)
        if explicit_folder:
            return explicit_folder

        explicit_file = self._extract_file_name(normalized_message)
        if explicit_file:
            return explicit_file

        if intent in {Intent.OPEN_FOLDER, Intent.LIST_DIRECTORY}:
            return self._extract_tail_after_action(normalized_message)

        if intent == Intent.OPEN_FILE:
            return self._extract_tail_after_action(normalized_message)

        if intent == Intent.SEARCH_FILE:
            return self._extract_search_phrase(normalized_message)

        if intent == Intent.CREATE_FOLDER:
            folder_name, _ = self._extract_folder_info_from_message(normalized_message)
            return folder_name

        if intent == Intent.DELETE_FOLDER:
            return self._extract_delete_folder_info_from_message(normalized_message)

        return None

    def _calculate_confidence(
        self,
        normalized_message: str,
        intent: Intent,
        target: str | None,
    ) -> float:
        """Calculates a confidence score for the detected plan.

        Args:
            normalized_message: The normalized request text.
            intent: The detected intent.
            target: The extracted target, if any.

        Returns:
            A confidence value between 0.0 and 1.0.
        """

        base_scores = {
            Intent.OPEN_FOLDER: 0.72,
            Intent.OPEN_FILE: 0.74,
            Intent.SEARCH_FILE: 0.70,
            Intent.LIST_DIRECTORY: 0.68,
            Intent.CREATE_FOLDER: 0.75,
            Intent.DELETE_FOLDER: 0.75,
            Intent.UNKNOWN: 0.20,
        }
        confidence = base_scores.get(intent, 0.20)

        if target:
            confidence += 0.18

        if self._contains_any(normalized_message, self._FOLDER_NAMES):
            confidence += 0.05

        if self._extract_file_name(normalized_message) is not None:
            confidence += 0.05

        return round(min(confidence, 1.0), 2)

    def _contains_any(self, text: str, phrases: tuple[str, ...]) -> bool:
        """Checks whether any phrase is present in the text."""

        return any(phrase in text for phrase in phrases)

    def _extract_quoted_text(self, text: str) -> str | None:
        """Extracts quoted text from a request."""

        match = self._QUOTED_TEXT_PATTERN.search(text)
        if match is None:
            return None

        quoted = match.group(1) or match.group(2)
        if quoted is None:
            return None

        return quoted.strip()

    def _extract_folder_name(self, text: str) -> str | None:
        """Extracts a common folder name from the request."""

        for folder_name in self._FOLDER_NAMES:
            if re.search(rf"\b{re.escape(folder_name)}\b", text):
                return folder_name.title()
        return None

    def _extract_file_name(self, text: str) -> str | None:
        """Extracts a likely file name from the request."""

        match = self._FILE_EXTENSION_PATTERN.search(text)
        if match is None:
            return None

        return match.group(0).strip()

    def _extract_tail_after_action(self, text: str) -> str | None:
        """Extracts text after a common action phrase.

        Args:
            text: The normalized request text.

        Returns:
            The trailing target text, if any.
        """

        action_patterns = (
            r"(?:open|list|show|find|search|go to|navigate to|look for|browse)\s+(?:the\s+)?(?:folder|file|directory|contents|files)?\s*(?:in|at|from|for)?\s*(.+)$",
            r"(?:open|list|show|find|search)\s+(.+)$",
        )

        for pattern in action_patterns:
            match = re.search(pattern, text)
            if match is None:
                continue

            candidate = match.group(1).strip()
            candidate = re.sub(r"^(?:the|a|an)\s+", "", candidate)
            if candidate:
                return candidate

        return None

    def _extract_search_phrase(self, text: str) -> str | None:
        """Extracts the phrase likely being searched for.

        Args:
            text: The normalized request text.

        Returns:
            The extracted search phrase, if any.
        """

        match = re.search(
            r"(?:search for|find|look for)\s+(?:the\s+)?(.+)$",
            text,
        )
        if match is None:
            return self._extract_tail_after_action(text)

        candidate = match.group(1).strip()
        candidate = re.sub(r"^(?:the|a|an)\s+", "", candidate)
        return candidate or None

    def _looks_like_file_request(self, text: str) -> bool:
        """Checks for obvious file-oriented wording."""

        return "file" in text or self._extract_file_name(text) is not None

    def _looks_like_open_file_request(self, text: str) -> bool:
        """Checks for an explicit open-file request."""

        if self._contains_any(text, self._OPEN_FILE_HINTS):
            return True

        return text.startswith("open ") and self._looks_like_file_request(text)

    def _looks_like_open_folder_request(self, text: str) -> bool:
        """Checks for an explicit open-folder request."""

        if self._contains_any(text, self._OPEN_FOLDER_HINTS):
            return True

        return text.startswith("open ") and self._contains_any(text, self._FOLDER_NAMES)

    def _looks_like_directory_request(self, text: str) -> bool:
        """Checks for obvious directory-oriented wording."""

        return any(keyword in text for keyword in ("folder", "directory", "contents", "files in"))

    def _extract_folder_info_from_message(self, message: str) -> tuple[str | None, str | None]:
        """Extracts case-preserved folder name and destination from the original message."""

        # Pattern 1: Create folder [folder_name] in [destination]
        p1 = re.compile(
            r"(?:create|make|new)\s+(?:a\s+)?(?:folder|directory)\s+(?:called\s+)?(.+?)(?:\s+(?:in|on|inside|at|into)\s+(.+))?$",
            re.IGNORECASE
        )
        # Pattern 2: Create folder in/on/inside [destination] called [folder_name]
        p2 = re.compile(
            r"(?:create|make|new)\s+(?:a\s+)?(?:folder|directory)\s+(?:in|on|inside|at|into)\s+(.+?)\s+(?:called\s+)?(.+)",
            re.IGNORECASE
        )

        m2 = p2.search(message)
        if m2:
            destination = m2.group(1).strip().strip("\"'")
            folder_name = m2.group(2).strip().strip("\"'")
            return folder_name, destination

        m1 = p1.search(message)
        if m1:
            folder_name = m1.group(1).strip().strip("\"'")
            destination = m1.group(2).strip().strip("\"'") if m1.group(2) else None
            return folder_name, destination

        return None, None

    def _extract_delete_folder_info_from_message(self, message: str) -> str | None:
        """Extracts case-preserved folder name to delete from the original message."""

        p = re.compile(
            r"(?:delete|remove|trash|discard)\s+(?:the\s+)?(?:folder|directory)\s+(.+)",
            re.IGNORECASE
        )
        m = p.search(message)
        if m:
            return m.group(1).strip().strip("\"'")
        return None


__all__ = ["ExecutionPlan", "Planner"]