"""Workspace subsystem custom models, templates, and exceptions."""

from typing import Any, Dict, List
from memory.exceptions import MemoryException


# Custom Exceptions
class WorkspaceError(MemoryException):
    """Base exception for all workspace profile errors."""
    pass


class InvalidWorkspaceError(WorkspaceError):
    """Raised when workspace configuration validation fails."""
    pass


class WorkspaceNotFoundError(WorkspaceError):
    """Raised when the specified workspace profile is not found."""
    pass


# Default Workspace Templates
WORKSPACE_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "coding": {
        "path": "/projects/code",
        "settings": {
            "applications": [{"name": "VS Code", "args": []}, {"name": "Terminal", "args": []}],
            "projects": ["/projects/code"],
            "browser_tabs": ["https://github.com", "https://stackoverflow.com"],
            "terminal_config": {"shell": "powershell", "commands": []},
            "env_vars": {"MODE": "development"},
            "startup_order": ["applications", "browser_tabs"],
            "metadata": {"description": "Workspace for coding activities", "tags": ["coding", "dev"]},
        },
    },
    "study": {
        "path": "/documents/study",
        "settings": {
            "applications": [{"name": "Microsoft Edge", "args": []}],
            "projects": [],
            "browser_tabs": ["https://wikipedia.org", "https://scholar.google.com"],
            "terminal_config": {},
            "env_vars": {"MODE": "focus"},
            "startup_order": ["applications", "browser_tabs"],
            "metadata": {"description": "Workspace for research and studying", "tags": ["study", "focus"]},
        },
    },
    "meeting": {
        "path": "/documents/notes",
        "settings": {
            "applications": [{"name": "Notepad", "args": []}],
            "projects": [],
            "browser_tabs": [],
            "terminal_config": {},
            "env_vars": {"STATUS": "busy"},
            "startup_order": ["applications"],
            "metadata": {"description": "Workspace for meetings and notes", "tags": ["meeting", "notes"]},
        },
    },
    "gaming": {
        "path": "/games",
        "settings": {
            "applications": [{"name": "Spotify", "args": []}],
            "projects": [],
            "browser_tabs": [],
            "terminal_config": {},
            "env_vars": {},
            "startup_order": ["applications"],
            "metadata": {"description": "Workspace for gaming and music", "tags": ["gaming", "play"]},
        },
    },
    "presentation": {
        "path": "/documents/slides",
        "settings": {
            "applications": [{"name": "Microsoft Edge", "args": []}],
            "projects": [],
            "browser_tabs": ["https://slides.google.com"],
            "terminal_config": {},
            "env_vars": {},
            "startup_order": ["applications", "browser_tabs"],
            "metadata": {"description": "Workspace for presentations", "tags": ["presentation"]},
        },
    },
    "custom": {
        "path": "/workspace",
        "settings": {
            "applications": [],
            "projects": [],
            "browser_tabs": [],
            "terminal_config": {},
            "env_vars": {},
            "startup_order": [],
            "metadata": {"description": "Custom user workspace", "tags": ["custom"]},
        },
    },
}
