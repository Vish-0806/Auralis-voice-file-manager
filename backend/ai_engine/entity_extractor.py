"""
Rule-based entity extraction for Auralis commands.
"""

import re
from typing import List

from ai_engine.command_normalizer import normalize_command, normalize_target
from utils.logger import get_logger


logger = get_logger(__name__)


LOCATION_ENTITIES = ["desktop", "downloads", "documents", "pictures", "music", "videos"]
LOCATION_PREPOSITIONS = r"(?:in|on|inside|within|under|at|to|into)"


def _strip_action_prefix(command: str, intent: str | None = None) -> str:
	text = normalize_command(command)

	if intent == "create_folder":
		match = re.search(r"\b(?:create|make)\s+(?:a\s+)?(?:folder|directory)\b\s*(.*)", text)
		return (match.group(1) if match else text).strip()

	if intent == "rename":
		match = re.search(r"\brename\b\s*(.*)", text)
		return (match.group(1) if match else text).strip()

	if intent == "move":
		match = re.search(r"\b(?:move|transfer)\b\s*(.*)", text)
		return (match.group(1) if match else text).strip()

	if intent == "copy":
		match = re.search(r"\bcopy\b\s*(.*)", text)
		return (match.group(1) if match else text).strip()

	if intent == "search":
		match = re.search(r"\b(?:search|find|locate)\b(?:\s+for)?\s*(.*)", text)
		if not match:
			match = re.search(r"\blook\s+for\b\s*(.*)", text)
		if not match:
			match = re.search(r"\bwhere\s+is\b\s*(.*)", text)
		return (match.group(1) if match else text).strip()

	if intent in {"open", "delete"}:
		match = re.search(r"\b(?:open|show|go to|navigate to|delete|remove|trash|discard)\b\s*(.*)", text)
		return (match.group(1) if match else text).strip()

	if intent == "organize":
		match = re.search(r"\b(?:organize|clean|sort)\b\s*(.*)", text)
		return (match.group(1) if match else text).strip()

	return text


def _extract_location_match(text: str) -> re.Match[str] | None:
	location_pattern = r"\b" + LOCATION_PREPOSITIONS + r"\s+(?:the\s+)?(" + "|".join(LOCATION_ENTITIES) + r")\b"
	return re.search(location_pattern, text)


def _remove_location_clause(text: str) -> str:
	match = _extract_location_match(text)
	if not match:
		return text

	remaining = (text[: match.start()] + " " + text[match.end() :]).strip()
	return re.sub(r"\s+", " ", remaining)


def extract_file_names(command: str) -> List[str]:
	"""Extract file-like tokens from a command."""
	if not isinstance(command, str) or not command.strip():
		return []

	text = command.strip()
	candidates = []

	candidates.extend(re.findall(r'"([^"]+\.[A-Za-z0-9]{1,8})"', text))
	candidates.extend(re.findall(r"'([^']+\.[A-Za-z0-9]{1,8})'", text))
	candidates.extend(re.findall(r"(?<!\S)([^\s\"']+\.[A-Za-z0-9]{1,8})(?!\S)", text))

	cleaned = []
	for candidate in candidates:
		value = candidate.strip().strip("\"'")
		if value and value not in cleaned:
			cleaned.append(value)

	logger.debug("Extracted file names from '%s': %s", command, cleaned)
	return cleaned


def extract_folder_names(command: str) -> List[str]:
	"""Extract folder-like tokens from a command."""
	if not isinstance(command, str) or not command.strip():
		return []

	text = normalize_command(command)
	candidates = []

	for pattern in [
		r"\b(?:folder|directory)\b\s*(.+)$",
		r"\b(?:open|delete|remove|move|create|make|rename|copy|transfer)\b\s*(.+)$",
		r"\b(?:search|find|locate)\b(?:\s+for)?\s*(.+)$",
		r"\blook\s+for\b\s*(.+)$",
		r"\bwhere\s+is\b\s*(.+)$",
	]:
		match = re.search(pattern, text)
		if match:
			candidates.append(match.group(1).strip())

	results = []
	for candidate in candidates:
		normalized = normalize_target(candidate)
		if normalized and normalized not in results:
			results.append(normalized)

	logger.debug("Extracted folder names from '%s': %s", command, results)
	return results


def extract_folder_location(command: str, intent: str | None = None) -> str:
	"""Extract the destination folder location from a command."""
	if not isinstance(command, str) or not command.strip():
		return ""

	text = normalize_command(command)
	if intent in {"create_folder", "move", "copy"}:
		text = _strip_action_prefix(text, intent=intent)

	match = _extract_location_match(text)
	location = match.group(1) if match else ""

	logger.debug("Extracted folder location from '%s': %s", command, location)
	return location


def extract_targets(command: str, intent: str | None = None) -> str:
	"""Extract the most relevant target phrase from a command."""
	if not isinstance(command, str) or not command.strip():
		return ""

	target = ""
	file_names = extract_file_names(command)
	if file_names:
		target = file_names[0]
		logger.debug("Selected file target '%s' from command: %s", target, command)
	else:
		folder_names = extract_folder_names(command)
		if folder_names:
			target = folder_names[0]
			if intent in {"create_folder", "move", "copy"}:
				target = normalize_target(_remove_location_clause(target))
			logger.debug("Selected folder target '%s' from command: %s", target, command)
		else:
			remainder = _strip_action_prefix(command, intent=intent)
			target = normalize_target(remainder)
			if intent in {"create_folder", "move", "copy"}:
				target = normalize_target(_remove_location_clause(target))

	# Filter out isolated prepositions
	if target in {"to", "into", "in", "on", "inside", "within", "under", "at"}:
		target = ""

	logger.debug(
		"Extracted target '%s' from command '%s' using intent '%s'",
		target,
		command,
		intent,
	)
	return target


__all__ = ["extract_file_names", "extract_folder_names", "extract_folder_location", "extract_targets"]
