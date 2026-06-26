"""
Auralis Voice Subsystem Models
Defines basic data structures and parameters.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class WakeWordResult:
    """Structure returned by the wake word detector."""
    activated: bool
    cleaned_command: str


@dataclass
class VoiceConfig:
    """Configuration options for voice synthesis and listening."""
    rate: int = 150
    volume: float = 1.0
    voice_id: Optional[str] = None


@dataclass
class VoiceSession:
    """Represents a telemetry or state session for voice operations."""
    session_id: str
    is_active: bool = True
    last_active_time: float = field(default_factory=float)
