"""Defines configuration and response models for Text-to-Speech synthesis."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class TTSConfiguration:
    """Configuration options for speech synthesis engines.

    Attributes:
        engine: The target engine type ("edge-tts" or "pyttsx3").
        voice_id: The specific speaker identifier. None uses the default.
        rate: Speech pace in words per minute (WPM, default 150).
        volume: Speech volume range (0.0 to 1.0, default 1.0).
        language: ISO 639-1 language code (default "en").
    """

    engine: str = "edge-tts"
    voice_id: Optional[str] = None
    rate: int = 150
    volume: float = 1.0
    language: str = "en"


@dataclass
class SpeechResponse:
    """Holds the result of a text-to-speech synthesis operation.

    Attributes:
        text: The source plain text string.
        audio_data: Binary generated speech audio bytes (MP3/WAV), or None.
        success: Boolean flag representing if the synthesis was successful.
        error: Description of failure if success is False.
        latency: Time taken in seconds to synthesize the speech.
    """

    text: str
    audio_data: Optional[bytes] = None
    success: bool = True
    error: Optional[str] = None
    latency: float = 0.0
