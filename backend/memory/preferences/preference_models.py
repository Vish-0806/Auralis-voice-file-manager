"""User Preference Domain Models, Schema Schemas, and Custom Exceptions."""

from typing import Any, Dict, NamedTuple, Type
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field
# pyrefly: ignore [missing-import]
from memory.exceptions import MemoryException


# Custom exceptions for User Preferences
class PreferenceError(MemoryException):
    """Base exception for all user preference operations."""
    pass


class InvalidPreferenceError(PreferenceError):
    """Raised when a preference category, key, value type, or required constraint fails validation."""
    pass


class DuplicatePreferenceError(PreferenceError):
    """Raised when attempting to create a preference entry that already exists."""
    pass


class PreferenceSchema(NamedTuple):
    """Container defining validation metadata for a preference key."""
    category: str
    key: str
    value_type: Type
    required: bool = False
    default: Any = None


# Allowed categories, keys, and values configuration schema
VALID_PREFERENCES: Dict[str, Dict[str, PreferenceSchema]] = {
    "ide": {
        "theme": PreferenceSchema("ide", "theme", str, default="vs-dark"),
        "font_size": PreferenceSchema("ide", "font_size", int, default=14),
        "tab_size": PreferenceSchema("ide", "tab_size", int, default=4),
    },
    "browser": {
        "default": PreferenceSchema("browser", "default", str, default="chrome"),
        "incognito_mode": PreferenceSchema("browser", "incognito_mode", bool, default=False),
    },
    "terminal": {
        "shell": PreferenceSchema("terminal", "shell", str, default="powershell"),
        "history_limit": PreferenceSchema("terminal", "history_limit", int, default=1000),
    },
    "voice": {
        "tts_enabled": PreferenceSchema("voice", "tts_enabled", bool, default=True),
        "speech_rate": PreferenceSchema("voice", "speech_rate", float, default=1.0),
        "voice_name": PreferenceSchema("voice", "voice_name", str, default="en-US-GuyNeural"),
    },
    "theme": {
        "mode": PreferenceSchema("theme", "mode", str, default="dark"),
        "accent_color": PreferenceSchema("theme", "accent_color", str, default="#3b82f6"),
    },
    "downloads_folder": {
        "path": PreferenceSchema("downloads_folder", "path", str, required=True),
    },
    "music": {
        "volume": PreferenceSchema("music", "volume", int, default=50),
        "player": PreferenceSchema("music", "player", str, default="spotify"),
    },
    "notifications": {
        "enabled": PreferenceSchema("notifications", "enabled", bool, default=True),
        "sound": PreferenceSchema("notifications", "sound", bool, default=True),
    },
    "language": {
        "locale": PreferenceSchema("language", "locale", str, default="en_US"),
    },
    "timezone": {
        "tz": PreferenceSchema("timezone", "tz", str, default="UTC"),
    },
}
