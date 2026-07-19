"""Data models for application management."""

from __future__ import annotations

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


class RunningApplication(BaseModel):
    """Represents a running desktop application instance.

    Attributes:
        name: The human-readable name of the application.
        pid: The process ID (PID) of the application.
        status: The running status (e.g., 'running', 'sleeping').
    """

    name: str = Field(description="The name of the application")
    pid: int = Field(description="The process identifier (PID)")
    status: str = Field(default="running", description="Process execution status")


class ApplicationDetails(BaseModel):
    """Details of a registered application.

    Attributes:
        name: Stable name key.
        executable_path: Expected absolute path to executable.
        is_running: Whether the app is currently running.
    """

    name: str = Field(description="The name of the application")
    executable_path: str = Field(description="Resolved path of the executable")
    is_running: bool = Field(description="True if the application is currently running")
