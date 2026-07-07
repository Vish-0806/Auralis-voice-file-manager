"""Models for the speech recognition subsystem.

Defines the configuration, request, and result models used for voice capture
and speech-to-text transcription.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SpeechConfiguration:
    """Configuration options for speech capture and recognition.

    Attributes:
        backend: Preferred recognition backend ("faster-whisper" or "speech-recognition").
        model_size: Size of the Whisper model to load (e.g., "tiny", "base", "small").
        language: ISO 639-1 language code (e.g., "en"). None triggers auto-detection.
        timeout: Maximum time in seconds to wait for initial speech.
        phrase_time_limit: Maximum duration in seconds for the recorded phrase.
        silence_threshold: Amplitude RMS threshold below which audio is silent.
        silence_duration: Seconds of continuous silence required to stop recording.
        device_index: Specific hardware microphone device index. None uses default.
        sample_rate: Recording sample rate in Hz (default 16000).
        sample_width: Bytes per sample (default 2 for 16-bit audio).
        channels: Number of audio channels (default 1 for mono).
    """

    backend: str = "faster-whisper"
    model_size: str = "base"
    language: Optional[str] = "en"
    timeout: float = 10.0
    phrase_time_limit: Optional[float] = None
    silence_threshold: int = 500
    silence_duration: float = 1.5
    device_index: Optional[int] = None
    sample_rate: int = 16000
    sample_width: int = 2
    channels: int = 1


@dataclass
class SpeechRequest:
    """Encapsulates processed audio ready for speech-to-text transcription.

    Attributes:
        audio_data: Raw PCM audio bytes or fully formatted WAV bytes.
        sample_rate: Audio sample rate in Hz.
        sample_width: Bytes per sample.
        channels: Number of audio channels.
    """

    audio_data: bytes
    sample_rate: int = 16000
    sample_width: int = 2
    channels: int = 1


@dataclass
class SpeechResult:
    """Structure returned after a speech-to-text recognition attempt.

    Attributes:
        text: Transcribed lowercased text string, or None if failed.
        success: Boolean flag representing if recognition was successful.
        error: Description of any failure if success is False.
        latency: Time taken in seconds to perform the transcription.
    """

    text: Optional[str]
    success: bool
    error: Optional[str] = None
    latency: float = 0.0
