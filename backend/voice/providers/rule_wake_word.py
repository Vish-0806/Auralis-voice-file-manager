"""
Auralis Rule-Based Wake Word Detector
Implements pattern-matching wake word checks.
"""

import re
from typing import Any, Dict, List
from utils.logger import get_logger
from voice.interfaces import IWakeWordDetector

logger = get_logger(__name__)

DEFAULT_WAKE_PHRASES = [
    "hey auralis",
    "hi auralis",
    "hello auralis",
    "auralis",
]

_PUNCTUATION_RE = re.compile(r"[^\w\s]", re.UNICODE)
_EXTRA_SPACE_RE = re.compile(r"\s{2,}")


class RuleWakeWordDetector(IWakeWordDetector):
    """Rule-based wake word detector that handles punctuation and casing."""

    def __init__(self, wake_phrases: List[str] = None) -> None:
        self.wake_phrases = wake_phrases or DEFAULT_WAKE_PHRASES

    def _normalize(self, text: str) -> str:
        """Lowercases and cleans up punctuation or extra whitespaces."""
        text = text.lower()
        text = _PUNCTUATION_RE.sub("", text)
        text = _EXTRA_SPACE_RE.sub(" ", text)
        return text.strip()

    def detect_wake_word(self, command: str) -> Dict[str, Any]:
        """Checks if the input begins with a valid wake phrase and returns clean payload."""
        if not isinstance(command, str):
            logger.warning("detect_wake_word received non-string input: %s", type(command).__name__)
            return {"activated": False, "cleaned_command": ""}

        normalized = self._normalize(command)
        logger.debug("Wake-word check on normalized input: '%s'", normalized)

        for phrase in self.wake_phrases:
            if normalized.startswith(phrase):
                cleaned = normalized[len(phrase):].strip()
                logger.info(
                    "Wake word detected (phrase='%s'). Cleaned command: '%s'",
                    phrase,
                    cleaned,
                )
                return {"activated": True, "cleaned_command": cleaned}

        logger.debug("No wake word detected in input.")
        return {"activated": False, "cleaned_command": ""}
