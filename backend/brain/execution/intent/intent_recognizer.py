"""Intent Recognizer for the Auralis Intent Resolution Subsystem (Phase 12.2).

Responsible for:
- normalizing raw user text
- removing conversational filler phrases
- detecting command category and specific action
- assigning confidence score rating
- returning structured UserIntent models

Performs 100% deterministic rule-based pattern matching without making any external AI calls.
"""

import re
from typing import List, Tuple

from brain.execution.intent.exceptions import IntentRecognitionError
from brain.execution.intent.intent_models import (
    IntentCategory,
    IntentConfidence,
    UserIntent,
)
from brain.execution.intent.interfaces import IIntentRecognizer

FILLER_PHRASES: List[str] = [
    r"\bhey auralis\b",
    r"\bauralis\b",
    r"\bcan you please\b",
    r"\bcould you please\b",
    r"\bwould you mind\b",
    r"\bcan you\b",
    r"\bcould you\b",
    r"\bwould you\b",
    r"\bi want to\b",
    r"\bi would like to\b",
    r"\bi need to\b",
    r"\bplease\b",
    r"\bkindly\b",
    r"\bshall we\b",
    r"\bgo ahead and\b",
    r"\bjust\b",
]

OPT_MODIFIER = r"\s+(?:a\s+|an\s+|the\s+|all\s+|my\s+|some\s+)?"

COMMAND_PATTERNS: List[Tuple[str, IntentCategory, str, IntentConfidence]] = [
    # FILE_MANAGEMENT
    (r"\b(create|make|mkdir)" + OPT_MODIFIER + r"(folder|directory|file)\b", IntentCategory.FILE_MANAGEMENT, "CREATE_FOLDER", IntentConfidence.HIGH),
    (r"\b(delete|remove|trash|rm)" + OPT_MODIFIER + r"(file|files|folder|folders|directory)\b", IntentCategory.FILE_MANAGEMENT, "DELETE_ITEM", IntentConfidence.HIGH),
    (r"\b(move|transfer)" + OPT_MODIFIER + r"(file|files|folder|folders|directory)\b", IntentCategory.FILE_MANAGEMENT, "MOVE_ITEM", IntentConfidence.HIGH),
    (r"\b(copy|duplicate)" + OPT_MODIFIER + r"(file|files|folder|folders|directory)\b", IntentCategory.FILE_MANAGEMENT, "COPY_ITEM", IntentConfidence.HIGH),
    (r"\b(rename)" + OPT_MODIFIER + r"(file|files|folder|folders|directory)\b", IntentCategory.FILE_MANAGEMENT, "RENAME_ITEM", IntentConfidence.HIGH),
    (r"\b(organize|sort|cleanup)" + OPT_MODIFIER + r"(files|folder|directory)\b", IntentCategory.FILE_MANAGEMENT, "ORGANIZE_FOLDER", IntentConfidence.HIGH),

    # FILE_SEARCH
    (r"\b(search|find|locate)" + OPT_MODIFIER + r"(?:[a-z0-9_\-]+\s+)*(file|files|pdf|pdfs|doc|docs|document|documents|image|images|picture|pictures|video|videos|folder|folders)\b", IntentCategory.FILE_SEARCH, "SEARCH_FILE", IntentConfidence.HIGH),
    (r"\b(where is|locate)\b", IntentCategory.FILE_SEARCH, "LOCATE_FILE", IntentConfidence.MEDIUM),
    (r"\b(list files|dir|ls)\b", IntentCategory.FILE_SEARCH, "LIST_FILES", IntentConfidence.HIGH),

    # APPLICATION_CONTROL
    (r"\b(open|launch|start|run)" + OPT_MODIFIER + r"(app|application|chrome|firefox|edge|vscode|vs code|notepad|explorer|calculator|spotify|terminal)\b", IntentCategory.APPLICATION_CONTROL, "OPEN_APPLICATION", IntentConfidence.HIGH),
    (r"\b(close|kill|exit|terminate|quit)" + OPT_MODIFIER + r"(app|application|chrome|firefox|edge|vscode|vs code|notepad|explorer|calculator|spotify|terminal)\b", IntentCategory.APPLICATION_CONTROL, "CLOSE_APPLICATION", IntentConfidence.HIGH),
    (r"\b(restart)" + OPT_MODIFIER + r"(app|application)\b", IntentCategory.APPLICATION_CONTROL, "RESTART_APPLICATION", IntentConfidence.HIGH),

    # WINDOW_MANAGEMENT
    (r"\b(minimize)" + OPT_MODIFIER + r"window\b", IntentCategory.WINDOW_MANAGEMENT, "MINIMIZE_WINDOW", IntentConfidence.HIGH),
    (r"\b(maximize)" + OPT_MODIFIER + r"window\b", IntentCategory.WINDOW_MANAGEMENT, "MAXIMIZE_WINDOW", IntentConfidence.HIGH),
    (r"\b(focus|bring to front)" + OPT_MODIFIER + r"window\b", IntentCategory.WINDOW_MANAGEMENT, "FOCUS_WINDOW", IntentConfidence.HIGH),
    (r"\b(close)" + OPT_MODIFIER + r"window\b", IntentCategory.WINDOW_MANAGEMENT, "CLOSE_WINDOW", IntentConfidence.HIGH),

    # SYSTEM_CONTROL
    (r"\b(set volume|change volume)\b", IntentCategory.SYSTEM_CONTROL, "SET_VOLUME", IntentConfidence.HIGH),
    (r"\b(mute)\b", IntentCategory.SYSTEM_CONTROL, "MUTE", IntentConfidence.HIGH),
    (r"\b(unmute)\b", IntentCategory.SYSTEM_CONTROL, "UNMUTE", IntentConfidence.HIGH),
    (r"\b(set brightness)\b", IntentCategory.SYSTEM_CONTROL, "SET_BRIGHTNESS", IntentConfidence.HIGH),
    (r"\b(shutdown|power off|reboot|restart pc|lock screen|sleep mode)\b", IntentCategory.SYSTEM_CONTROL, "SYSTEM_POWER", IntentConfidence.HIGH),

    # DEVICE_CONTROL
    (r"\b(enable|turn on)\s+(wifi|bluetooth)\b", IntentCategory.DEVICE_CONTROL, "ENABLE_DEVICE", IntentConfidence.HIGH),
    (r"\b(disable|turn off)\s+(wifi|bluetooth)\b", IntentCategory.DEVICE_CONTROL, "DISABLE_DEVICE", IntentConfidence.HIGH),

    # CLIPBOARD
    (r"\b(copy selection|copy to clipboard)\b", IntentCategory.CLIPBOARD, "COPY_SELECTION", IntentConfidence.HIGH),
    (r"\b(paste|paste clipboard)\b", IntentCategory.CLIPBOARD, "PASTE", IntentConfidence.HIGH),
    (r"\b(clear clipboard)\b", IntentCategory.CLIPBOARD, "CLEAR_CLIPBOARD", IntentConfidence.HIGH),

    # SCREENSHOT
    (r"\b(take screenshot|screen capture|screenshot)\b", IntentCategory.SCREENSHOT, "TAKE_SCREENSHOT", IntentConfidence.HIGH),

    # WORKFLOW_PLANNING
    (r"\b(plan|create workflow|build pipeline|multi-step|sequence)\b", IntentCategory.WORKFLOW_PLANNING, "PLAN_WORKFLOW", IntentConfidence.HIGH),

    # AI_GENERATION
    (r"\b(generate|summarize|explain|draft|write code|translate)\b", IntentCategory.AI_GENERATION, "GENERATE_CONTENT", IntentConfidence.HIGH),

    # ASSISTANT_QUERY
    (r"\b(status|help|who are you|what can you do|info|hello|hi)\b", IntentCategory.ASSISTANT_QUERY, "ASSISTANT_STATUS", IntentConfidence.HIGH),
]


class IntentRecognizer(IIntentRecognizer):
    """Deterministic rule-based recognizer for classifying user prompt intents."""

    def normalize_text(self, text: str) -> str:
        """Normalize raw text by trimming, lowercasing, and stripping punctuation."""
        if not text:
            return ""
        clean = text.strip().lower()
        clean = re.sub(r"[^\w\s\.\:\-\\/]", " ", clean)
        return " ".join(clean.split())

    def remove_filler_words(self, text: str) -> str:
        """Strip conversational filler phrases from text."""
        clean = text
        for filler in FILLER_PHRASES:
            clean = re.sub(filler, " ", clean, flags=re.IGNORECASE)
        return " ".join(clean.split())

    def detect_command_type(self, text: str) -> Tuple[IntentCategory, str, IntentConfidence]:
        """Detect intent category, specific action, and confidence rating using pattern matching."""
        if not text.strip():
            return IntentCategory.UNKNOWN, "UNKNOWN", IntentConfidence.NONE

        clean = self.remove_filler_words(self.normalize_text(text))

        for pat, cat, act, conf in COMMAND_PATTERNS:
            if re.search(pat, clean, flags=re.IGNORECASE):
                return cat, act, conf

        # Secondary fallback keyword matching
        words = set(clean.split())
        if words & {"copy", "move", "delete", "create", "folder", "file", "rename"}:
            return IntentCategory.FILE_MANAGEMENT, "FILE_ACTION", IntentConfidence.MEDIUM

        if words & {"search", "find", "locate", "list"}:
            return IntentCategory.FILE_SEARCH, "SEARCH_ACTION", IntentConfidence.MEDIUM

        if words & {"open", "launch", "close", "run"}:
            return IntentCategory.APPLICATION_CONTROL, "APP_ACTION", IntentConfidence.MEDIUM

        if words & {"volume", "brightness", "mute", "lock", "sleep"}:
            return IntentCategory.SYSTEM_CONTROL, "SYSTEM_ACTION", IntentConfidence.MEDIUM

        if words & {"wifi", "bluetooth"}:
            return IntentCategory.DEVICE_CONTROL, "DEVICE_ACTION", IntentConfidence.MEDIUM

        if words & {"summarize", "explain", "write", "generate", "code"}:
            return IntentCategory.AI_GENERATION, "GENERATE_ACTION", IntentConfidence.LOW

        if words & {"help", "status", "hello", "hi"}:
            return IntentCategory.ASSISTANT_QUERY, "QUERY_ACTION", IntentConfidence.LOW

        return IntentCategory.UNKNOWN, "UNKNOWN", IntentConfidence.NONE

    def recognize(self, text: str) -> UserIntent:
        """Recognize structured UserIntent deterministically from raw input.

        Args:
            text: Raw user prompt string.

        Returns:
            Populated UserIntent model.

        Raises:
            IntentRecognitionError: If text is None or empty.
        """
        if text is None:
            raise IntentRecognitionError("Input text cannot be None")

        normalized = self.normalize_text(text)
        cleaned = self.remove_filler_words(normalized)

        if not normalized.strip():
            return UserIntent(
                category=IntentCategory.UNKNOWN,
                raw_prompt=text,
                normalized_text="",
                action="UNKNOWN",
                confidence=IntentConfidence.NONE,
            )

        category, action, confidence = self.detect_command_type(cleaned)

        return UserIntent(
            category=category,
            raw_prompt=text,
            normalized_text=cleaned,
            action=action,
            confidence=confidence,
            metadata={"original_length": len(text), "cleaned_length": len(cleaned)},
        )
