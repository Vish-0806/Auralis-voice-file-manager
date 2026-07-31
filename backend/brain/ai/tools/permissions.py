"""Tool Permission Levels for Auralis AI Tool Calling Runtime (Phase 10.4).

Defines permission levels for access control architecture.
"""

from enum import Enum


class ToolPermissionLevel(str, Enum):
    """Permission access levels for AI tools."""

    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    SYSTEM = "system"
    ADMIN = "admin"
