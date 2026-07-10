"""Typed intent definitions for Auralis core orchestration."""

from __future__ import annotations

from enum import Enum


class Intent(str, Enum):
    """Supported assistant execution intents."""

    OPEN_FOLDER = "OPEN_FOLDER"
    OPEN_FILE = "OPEN_FILE"
    SEARCH_FILE = "SEARCH_FILE"
    LIST_DIRECTORY = "LIST_DIRECTORY"
    CREATE_FOLDER = "CREATE_FOLDER"
    DELETE_FOLDER = "DELETE_FOLDER"
    ORGANIZE_FOLDER = "ORGANIZE_FOLDER"
    GET_FILE_INFO = "GET_FILE_INFO"
    OPEN_APPLICATION = "OPEN_APPLICATION"
    CLOSE_APPLICATION = "CLOSE_APPLICATION"
    RESTART_APPLICATION = "RESTART_APPLICATION"
    LIST_RUNNING_APPLICATIONS = "LIST_RUNNING_APPLICATIONS"
    UNKNOWN = "UNKNOWN"


__all__ = ["Intent"]