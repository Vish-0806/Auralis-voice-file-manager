"""Data models for input automation capability."""

from __future__ import annotations

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


class InputCoordinate(BaseModel):
    """Represents x, y screen coordinates.

    Attributes:
        x: Pointer horizontal position.
        y: Pointer vertical position.
    """

    x: int = Field(description="Horizontal pixel coordinate (>= 0)")
    y: int = Field(description="Vertical pixel coordinate (>= 0)")
