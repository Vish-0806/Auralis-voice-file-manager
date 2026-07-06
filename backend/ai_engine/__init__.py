"""Backward compatibility wrapper delegating to backend/ai.

TODO: This legacy package can be removed once all references to ai_engine are deleted.
"""

from ai import (
    parse_command,
    normalize_command,
    normalize_target,
    classify_intent,
    extract_file_names,
    extract_folder_location,
    extract_folder_names,
    extract_targets,
)

__all__ = [
    "parse_command",
    "normalize_command",
    "normalize_target",
    "classify_intent",
    "extract_file_names",
    "extract_folder_location",
    "extract_folder_names",
    "extract_targets",
]
