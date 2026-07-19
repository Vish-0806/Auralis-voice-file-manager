"""
Auralis Microphone Audio Stream
Wraps the SpeechRecognition microphone resource to conform to IAudioStream.
"""

# pyrefly: ignore [missing-import]
import speech_recognition as sr
from voice.interfaces import IAudioStream


class MicrophoneAudioStream(IAudioStream):
    """Wraps standard system microphone capture configurations."""

    def __init__(self, device_index: int = None, sample_rate: int = 16000, chunk_size: int = 1024) -> None:
        self.device_index = device_index
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self._microphone = sr.Microphone(
            device_index=device_index,
            sample_rate=sample_rate,
            chunk_size=chunk_size
        )

    def get_source(self) -> sr.Microphone:
        """Exposes the underlying speech_recognition Microphone source object."""
        return self._microphone

    def read(self, chunk_size: int) -> bytes:
        """Reads a chunk of bytes from the audio stream (stub implementation)."""
        return b""

    def close(self) -> None:
        """Closes the stream."""
        pass
