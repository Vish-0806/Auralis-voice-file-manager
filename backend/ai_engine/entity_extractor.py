"""
Rule-based entity extraction for Auralis commands.
"""

import re
from typing import List

from ai_engine.command_normalizer import normalize_command, normalize_target
from utils.logger import get_logger


logger = get_logger(__name__)


def _strip_action_prefix(command: str, intent: str | None = None) -> str:
	text = normalize_command(command)

	if intent == "create_folder":
		match = re.search(r"\b(?:create|make)\s+(?:a\s+)?(?:folder|directory)\b\s*(.*)", text)
		return (match.group(1) if match else text).strip()

	if intent == "rename":
		match = re.search(r"\brename\b\s*(.*)", text)
		return (match.group(1) if match else text).strip()

	if intent == "move":
		match = re.search(r"\bmove\b\s*(.*)", text)
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

	return text


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
		r"\b(?:open|delete|remove|move|create|make|rename)\b\s*(.+)$",
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


def extract_targets(command: str, intent: str | None = None) -> str:
	"""Extract the most relevant target phrase from a command."""
	if not isinstance(command, str) or not command.strip():
		return ""

	file_names = extract_file_names(command)
	if file_names:
		target = file_names[0]
		logger.debug("Selected file target '%s' from command: %s", target, command)
		return target

	folder_names = extract_folder_names(command)
	if folder_names:
		target = folder_names[0]
		logger.debug("Selected folder target '%s' from command: %s", target, command)
		return target

	remainder = _strip_action_prefix(command, intent=intent)
	target = normalize_target(remainder)

	logger.debug(
		"Extracted target '%s' from command '%s' using intent '%s'",
		target,
		command,
		intent,
	)
	return target


__all__ = ["extract_file_names", "extract_folder_names", "extract_targets"]
