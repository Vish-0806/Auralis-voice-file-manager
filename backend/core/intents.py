"""Typed intent definitions for Auralis core orchestration."""

from __future__ import annotations

from enum import Enum


class Intent(str, Enum):
    """Supported assistant execution intents."""

    OPEN_FOLDER = "OPEN_FOLDER"
    OPEN_FILE = "OPEN_FILE"
    SEARCH_FILE = "SEARCH_FILE"
    LIST_DIRECTORY = "LIST_DIRECTORY"
    UNKNOWN = "UNKNOWN"


__all__ = ["Intent"]