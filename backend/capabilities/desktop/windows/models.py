"""Data models for window management capability."""

from __future__ import annotations

from pydantic import BaseModel, Field


class WindowDetails(BaseModel):
    """Represents public metadata for a desktop window.

    Attributes:
        handle: The OS-specific unique identifier of the window (HWND).
        title: The text displayed in the window's title bar.
        app_name: The process name of the application owning this window.
        is_active: True if the window has focus.
        is_minimized: True if the window is minimized.
        is_maximized: True if the window is maximized.
    """

    handle: int = Field(description="Unique window handle identifier")
    title: str = Field(description="Title bar text of the window")
    app_name: str = Field(description="Name of the application process owning this window")
    is_active: bool = Field(description="True if the window is currently focused")
    is_minimized: bool = Field(description="True if the window is currently minimized")
    is_maximized: bool = Field(description="True if the window is currently maximized")
