"""
Auralis Voice Subsystem Interfaces
Defines abstract contracts for all voice components.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class IAudioStream(ABC):
    """Abstract contract for audio streams."""

    @abstractmethod
    def read(self, chunk_size: int) -> bytes:
        """Reads a chunk of bytes from the audio input source."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Closes the audio stream."""
        pass


class ISpeechRecognizer(ABC):
    """Abstract contract for speech-to-text recognition."""

    @abstractmethod
    def recognize(self, timeout: float = 10.0, phrase_time_limit: float = 10.0) -> Optional[str]:
        """Listens to the audio source and returns recognized text in lowercase."""
        pass


class ISpeechSynthesizer(ABC):
    """Abstract contract for text-to-speech synthesis."""

    @abstractmethod
    def speak(self, text: str, wait: bool = True) -> bool:
        """Speaks the text, optionally blocking until complete."""
        pass

    @abstractmethod
    def set_rate(self, rate: int) -> bool:
        """Sets the speaking rate (words per minute)."""
        pass

    @abstractmethod
    def set_volume(self, volume: float) -> bool:
        """Sets the speaking volume (0.0 to 1.0)."""
        pass

    @abstractmethod
    def set_voice(self, voice_id: str) -> bool:
        """Selects a voice by identifier."""
        pass

    @abstractmethod
    def get_voices(self) -> Optional[List[Any]]:
        """Returns available voice definitions."""
        pass


class IWakeWordDetector(ABC):
    """Abstract contract for wake word detection and normalisation."""

    @abstractmethod
    def detect_wake_word(self, command: str) -> Dict[str, Any]:
        """Detects wake phrases and returns structured result with cleaned command."""
        pass


class IVoiceSessionManager(ABC):
    """Abstract contract for managing active voice session states."""

    @abstractmethod
    def get_pending_action(self) -> Optional[Dict[str, Any]]:
        """Retrieves the currently pending action."""
        pass

    @abstractmethod
    def set_pending_action(self, action: str, target: str, destination: Optional[str] = None) -> None:
        """Sets a pending action details."""
        pass

    @abstractmethod
    def clear_pending_action(self) -> None:
        """Clears the pending action details."""
        pass


class IVoiceListener(ABC):
    """Abstract contract for the background continuous voice loop."""

    @property
    @abstractmethod
    def is_running(self) -> bool:
        """Checks if the listener is running."""
        pass

    @abstractmethod
    def start(self, run_in_thread: bool = False) -> None:
        """Starts continuous monitoring loop."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stops the loop."""
        pass
