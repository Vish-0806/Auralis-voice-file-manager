"""Backward compatibility wrapper delegating to backend/ai.

TODO: This legacy wrapper can be removed once all references to ai_engine are deleted.
"""

from ai.entity_extractor import (
    extract_file_names,
    extract_folder_names,
    extract_folder_location,
    extract_targets,
)

__all__ = [
    "extract_file_names",
    "extract_folder_names",
    "extract_folder_location",
    "extract_targets",
]
