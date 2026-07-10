"""Data models for clipboard capability."""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class ClipboardEntry(BaseModel):
    """Represents a single clipboard history entry.

    Attributes:
        content: The text representation of the clipboard contents.
        content_type: The content type label (e.g., 'text', 'file_paths', 'image', 'empty').
        timestamp: The datetime when the entry was recorded.
        size_bytes: The size of the clipboard contents in bytes.
    """

    content: str = Field(description="Clipboard text content representation")
    content_type: str = Field(description="Content format type label")
    timestamp: datetime = Field(description="Timestamp when the entry was captured")
    size_bytes: int = Field(ge=0, description="Size of the contents in bytes")
