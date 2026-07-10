"""Data models for screenshot capability."""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class ScreenshotDetails(BaseModel):
    """Represents captured screenshot metadata details.

    Attributes:
        path: The file path where the screenshot was saved, if any.
        timestamp: The datetime when the capture occurred.
        width: Image width in pixels.
        height: Image height in pixels.
        format: Image codec/encoding format (e.g., 'PNG').
    """

    path: str | None = Field(None, description="Local save path of the screenshot image file")
    timestamp: datetime = Field(description="Capture timestamp")
    width: int = Field(gt=0, description="Image width in pixels")
    height: int = Field(gt=0, description="Image height in pixels")
    format: str = Field("PNG", description="Encoding format name")
