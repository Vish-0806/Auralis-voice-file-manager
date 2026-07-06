"""Compatibility parser that orchestrates the NLP pipeline."""

from typing import Dict

from ai.command_normalizer import normalize_command
from ai.entity_extractor import extract_folder_location, extract_targets
from ai.intent_classifier import classify_intent
from utils.logger import get_logger

logger = get_logger(__name__)


def parse_command(command: str) -> Dict[str, str]:
    """Rule-based parser for simple natural-language file commands.

    Returns a dict with `action`, `target`, and optional `location` or `destination` keys.
    """
    if not isinstance(command, str) or not command.strip():
        logger.debug("parse_command received empty command")
        return {"action": "unknown", "target": ""}

    normalized_command = normalize_command(command)
    intent = classify_intent(normalized_command)
    target = extract_targets(normalized_command, intent=intent)

    if intent == "unknown":
        logger.info("No intent matched for command: %s", command)
        return {"action": "unknown", "target": command.strip()}

    result = {"action": intent, "target": target}
    if intent in {"move", "copy"}:
        destination = extract_folder_location(normalized_command, intent=intent)
        if destination:
            result["destination"] = destination
    else:
        location = extract_folder_location(normalized_command, intent=intent) if intent == "create_folder" else ""
        if location:
            result["location"] = location

    logger.info("Parsed command '%s' -> %s", command, result)
    return result
