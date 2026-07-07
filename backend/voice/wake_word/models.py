"""Wake Word Subsystem Models.

Defines the data structures, configurations, and event models used by the Wake Word Engine.
"""

from dataclasses import dataclass, field
from typing import List, Optional
import time


@dataclass
class WakeWordConfiguration:
    """Configuration options for the Wake Word Subsystem.

    Attributes:
        wake_phrases (List[str]): List of phrases that activate the detector.
        sample_rate (int): Audio sampling rate in Hz (default: 16000).
        chunk_size (int): Size of each audio buffer read in frames (default: 1024).
        sensitivity (float): Wake word detection sensitivity threshold between 0.0 and 1.0 (default: 0.5).
        device_index (Optional[int]): Optional system microphone device index to use.
    """

    wake_phrases: List[str] = field(
        default_factory=lambda: ["hey auralis", "hello auralis", "auralis"]
    )
    sample_rate: int = 16000
    chunk_size: int = 1024
    sensitivity: float = 0.5
    device_index: Optional[int] = None


@dataclass
class WakeWordState:
    """Tracks the dynamic state of the Wake Word Engine.

    Attributes:
        is_listening (bool): Whether the microphone listener is actively capturing audio.
        last_detected_time (Optional[float]): POSIX timestamp of the last wake word detection event.
        status_message (str): Diagnostic message detailing the current status of the engine.
    """

    is_listening: bool = False
    last_detected_time: Optional[float] = None
    status_message: str = "idle"


@dataclass
class WakeWordEvent:
    """Represents a detected wake word event.

    Attributes:
        phrase (str): The specific wake phrase that was detected.
        detected_at (float): POSIX timestamp of when the wake word was detected.
        confidence (float): Confidence score of the detection between 0.0 and 1.0.
        audio_data_summary (Optional[str]): Diagnostic message detailing the audio properties.
    """

    phrase: str
    detected_at: float = field(default_factory=time.time)
    confidence: float = 1.0
    audio_data_summary: Optional[str] = None
