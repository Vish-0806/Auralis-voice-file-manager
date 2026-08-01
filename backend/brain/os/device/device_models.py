"""Device Subsystem Domain Models for Auralis (Phase 11.7).

Defines immutable Pydantic v2 models and enums representing hardware devices,
audio devices, display devices, input devices, network interfaces, storage drives,
battery status, operation requests/results, capabilities, health status, and runtime state.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


class DeviceType(str, Enum):
    """Classification of hardware device categories."""

    AUDIO = "audio"
    DISPLAY = "display"
    INPUT = "input"
    NETWORK = "network"
    STORAGE = "storage"
    POWER = "power"
    UNKNOWN = "unknown"


class DeviceState(str, Enum):
    """Operational state of a hardware device."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    DISABLED = "disabled"
    UNKNOWN = "unknown"


class AudioDeviceType(str, Enum):
    """Classification of audio devices."""

    INPUT_MIC = "input_mic"
    OUTPUT_SPEAKER = "output_speaker"
    HEADPHONES = "headphones"
    UNKNOWN = "unknown"


class NetworkType(str, Enum):
    """Classification of network interface types."""

    ETHERNET = "ethernet"
    WIFI = "wifi"
    BLUETOOTH = "bluetooth"
    LOOPBACK = "loopback"
    UNKNOWN = "unknown"


class PowerState(str, Enum):
    """Battery power and charging state."""

    CHARGING = "charging"
    DISCHARGING = "discharging"
    FULL = "full"
    UNKNOWN = "unknown"


class DeviceInfo(BaseModel):
    """Immutable basic hardware device metadata."""

    model_config = ConfigDict(frozen=True)

    device_id: str = ""
    name: str = ""
    device_type: DeviceType = DeviceType.UNKNOWN
    state: DeviceState = DeviceState.UNKNOWN
    manufacturer: str = ""
    is_default: bool = False
    is_enabled: bool = True


class AudioDevice(BaseModel):
    """Immutable audio hardware device details."""

    model_config = ConfigDict(frozen=True)

    info: DeviceInfo = Field(default_factory=DeviceInfo)
    audio_type: AudioDeviceType = AudioDeviceType.UNKNOWN
    volume_level: float = 100.0
    is_muted: bool = False
    sample_rate: int = 44100
    channels: int = 2


class DisplayDevice(BaseModel):
    """Immutable display monitor device details."""

    model_config = ConfigDict(frozen=True)

    info: DeviceInfo = Field(default_factory=DeviceInfo)
    width: int = 1920
    height: int = 1080
    refresh_rate: int = 60
    is_primary: bool = True
    scaling_factor: float = 1.0


class InputDevice(BaseModel):
    """Immutable input hardware device details."""

    model_config = ConfigDict(frozen=True)

    info: DeviceInfo = Field(default_factory=DeviceInfo)
    input_category: str = "keyboard"
    is_wireless: bool = False


class NetworkDevice(BaseModel):
    """Immutable network adapter details."""

    model_config = ConfigDict(frozen=True)

    info: DeviceInfo = Field(default_factory=DeviceInfo)
    network_type: NetworkType = NetworkType.UNKNOWN
    mac_address: str = ""
    ip_address: str = ""
    speed_mbps: int = 1000
    is_connected: bool = True


class StorageDevice(BaseModel):
    """Immutable storage volume/drive details."""

    model_config = ConfigDict(frozen=True)

    info: DeviceInfo = Field(default_factory=DeviceInfo)
    mount_point: str = ""
    total_bytes: int = 0
    free_bytes: int = 0
    is_removable: bool = False


class BatteryStatus(BaseModel):
    """Immutable power and battery status snapshot."""

    model_config = ConfigDict(frozen=True)

    is_present: bool = False
    power_state: PowerState = PowerState.UNKNOWN
    percentage: float = 100.0
    time_remaining_seconds: Optional[float] = None


class DeviceCapabilities(BaseModel):
    """Immutable device runtime capabilities report."""

    model_config = ConfigDict(frozen=True)

    supports_device_enumeration: bool = True
    supports_volume_control: bool = True
    supports_device_toggle: bool = True
    supports_battery_monitoring: bool = True


class DeviceStatistics(BaseModel):
    """Immutable device subsystem runtime statistics."""

    model_config = ConfigDict(frozen=True)

    total_devices_discovered: int = 0
    active_devices_count: int = 0
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0


class DeviceHealth(BaseModel):
    """Immutable health status of Device Subsystem services."""

    model_config = ConfigDict(frozen=True)

    healthy: bool = True
    status: str = "READY"
    active_devices_count: int = 0
    battery_percent: float = 100.0
    uptime_seconds: float = 0.0
    details: Dict[str, Any] = Field(default_factory=dict)


class DeviceRuntimeStatus(BaseModel):
    """Immutable overall Device Runtime status report."""

    model_config = ConfigDict(frozen=True)

    state: str = "Initializing"
    healthy: bool = True
    provider_registered: bool = False
    active_devices_count: int = 0
    total_operations: int = 0
    uptime_seconds: float = 0.0


class DeviceOperationRequest(BaseModel):
    """Immutable device control operation request."""

    model_config = ConfigDict(frozen=True)

    device_id: str = ""
    action: str = "refresh"
    volume: Optional[float] = None
    mute: Optional[bool] = None
    enable: Optional[bool] = None


class DeviceOperationResult(BaseModel):
    """Immutable result of a device control operation."""

    model_config = ConfigDict(frozen=True)

    success: bool = True
    device_id: str = ""
    action: str = "refresh"
    error: Optional[str] = None
    duration_ms: float = 0.0
