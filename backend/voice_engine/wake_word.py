"""
Wake Word Detection module for Auralis Voice Assistant.
Provides lightweight, rule-based wake word detection that identifies
activation phrases and extracts the cleaned command payload.
"""

from utils.logger import get_logger

logger = get_logger(__name__)

# Supported wake phrases, ordered longest-first so greedy matching
# strips the most specific prefix before falling back to shorter ones.
WAKE_PHRASES = [
    "hey auralis",
    "hi auralis",
    "hello auralis",
    "auralis",
]


def detect_wake_word(command: str) -> dict:
    """
    Detect whether a voice command begins with a supported wake phrase.

    The check is case-insensitive and ignores leading/trailing whitespace.
    When a wake phrase is found the function returns the remaining text
    after the phrase (also trimmed) as ``cleaned_command``.

    Args:
        command: Raw voice command string captured from speech-to-text.

    Returns:
        dict with two keys:
            - activated (bool): True if a wake phrase was detected.
            - cleaned_command (str): The command text after the wake phrase,
              or an empty string when not activated.

    Examples:
        >>> detect_wake_word("Hey Auralis open downloads")
        {'activated': True, 'cleaned_command': 'open downloads'}

        >>> detect_wake_word("open downloads")
        {'activated': False, 'cleaned_command': ''}
    """
    if not isinstance(command, str):
        logger.warning("detect_wake_word received non-string input: %s", type(command).__name__)
        return {"activated": False, "cleaned_command": ""}

    normalized = command.strip().lower()
    logger.debug("Wake-word check on normalized input: '%s'", normalized)

    for phrase in WAKE_PHRASES:
        if normalized.startswith(phrase):
            # Extract everything after the wake phrase and strip whitespace.
            cleaned = normalized[len(phrase):].strip()
            logger.info(
                "Wake word detected (phrase='%s'). Cleaned command: '%s'",
                phrase,
                cleaned,
            )
            return {"activated": True, "cleaned_command": cleaned}

    logger.debug("No wake word detected in input.")
    return {"activated": False, "cleaned_command": ""}
