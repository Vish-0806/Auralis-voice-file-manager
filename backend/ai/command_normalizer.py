"""Rule-based text normalization helpers for Auralis commands."""

import re

from utils.logger import get_logger

logger = get_logger(__name__)

FILLER_PHRASES = [
    r"please",
    r"can you",
    r"could you",
    r"would you",
    r"my",
    r"the",
    r"called",
]

TRAILING_NOISE_WORDS = [
    r"folder",
    r"directory",
    r"file",
    r"files",
]

COMMON_FOLDER_NAMES = {
    "download": "downloads",
    "downloads": "downloads",
    "document": "documents",
    "documents": "documents",
    "picture": "pictures",
    "pictures": "pictures",
    "photo": "pictures",
    "photos": "pictures",
    "video": "videos",
    "videos": "videos",
    "desktop": "desktop",
    "music": "music",
}


def _remove_phrases(text: str, phrases: list[str]) -> str:
    for phrase in phrases:
        text = re.sub(r"\b" + phrase + r"\b", "", text)
    return text


def normalize_command(command: str) -> str:
    """Normalize a user command into a compact, rule-based form."""
    if not isinstance(command, str) or not command.strip():
        return ""

    normalized = command.lower()
    normalized = re.sub(r"[\,!?;:]", "", normalized)
    normalized = _remove_phrases(normalized, FILLER_PHRASES)

    if not re.match(r"^\s*(create|make)\b", normalized):
        normalized = _remove_phrases(normalized, TRAILING_NOISE_WORDS)

    for source, replacement in COMMON_FOLDER_NAMES.items():
        normalized = re.sub(r"\b" + re.escape(source) + r"\b", replacement, normalized)

    normalized = re.sub(r"\s+", " ", normalized).strip()

    logger.debug("Normalized command '%s' -> '%s'", command, normalized)
    return normalized


def normalize_target(target: str) -> str:
    """Normalize a target name such as a folder or file-like phrase."""
    if not isinstance(target, str) or not target.strip():
        return ""

    value = normalize_command(target)

    if value in COMMON_FOLDER_NAMES:
        return COMMON_FOLDER_NAMES[value]

    if value.endswith("s"):
        return value

    if value in ["download", "document", "picture", "photo", "video"]:
        return COMMON_FOLDER_NAMES.get(value, value + "s")

    return value


__all__ = ["normalize_command", "normalize_target"]
