"""Data models for system control capability."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SystemStatus(BaseModel):
    """Represents the status of OS system controls.

    Attributes:
        volume: The current master volume level (0-100).
        is_muted: True if the master audio is muted.
        brightness: The current screen brightness level (0-100).
        wifi_enabled: True if Wi-Fi is enabled.
        bluetooth_enabled: True if Bluetooth is enabled.
    """

    volume: int = Field(ge=0, le=100, description="Master audio volume level")
    is_muted: bool = Field(description="Muted status of the system audio")
    brightness: int = Field(ge=0, le=100, description="Screen brightness level")
    wifi_enabled: bool = Field(description="Wi-Fi interface active state")
    bluetooth_enabled: bool = Field(description="Bluetooth radio active state")
