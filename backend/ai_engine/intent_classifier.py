"""
Rule-based intent classification for Auralis commands.
"""

import re

from utils.logger import get_logger


logger = get_logger(__name__)


INTENT_PATTERNS = [
	("create_folder", [r"\b(?:create|make)\s+(?:a\s+)?(?:folder|directory)\b"]),
	("rename", [r"\brename\b", r"\b(?:change|set)\s+name\b"]),
	("move", [r"\bmove\b", r"\brelocate\b"]),
	("delete", [r"\b(?:delete|remove|trash|discard)\b"]),
	("search", [r"\b(?:search|find|look\s+for)\b"]),
	("open", [r"\b(?:open|show|go\s+to|navigate\s+to)\b"]),
]


def classify_intent(command: str) -> str:
	"""Classify a natural-language command into a rule-based intent."""
	if not isinstance(command, str) or not command.strip():
		logger.debug("classify_intent received empty command")
		return "unknown"

	normalized = command.lower().strip()

	for intent, patterns in INTENT_PATTERNS:
		for pattern in patterns:
			if re.search(pattern, normalized):
				logger.debug("Classified intent '%s' for command: %s", intent, command)
				return intent

	logger.debug("No intent matched for command: %s", command)
	return "unknown"


__all__ = ["classify_intent"]
