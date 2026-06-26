"""
Auralis Speech Synthesizer
Exposes the text-to-speech engine API.
"""

from typing import Any, List, Optional
from voice.interfaces import ISpeechSynthesizer
from voice.providers.pyttsx3_synthesizer import Pyttsx3Synthesizer


class SpeechSynthesizer(ISpeechSynthesizer):
    """Orchestrates speech playback using configured engine providers."""

    def __init__(self, provider: Optional[ISpeechSynthesizer] = None) -> None:
        self.provider = provider or Pyttsx3Synthesizer()

    def speak(self, text: str, wait: bool = True) -> bool:
        """Plays speech feedback."""
        return self.provider.speak(text, wait=wait)

    def set_rate(self, rate: int) -> bool:
        """Sets play rate."""
        return self.provider.set_rate(rate)

    def set_volume(self, volume: float) -> bool:
        """Sets volume."""
        return self.provider.set_volume(volume)

    def set_voice(self, voice_id: str) -> bool:
        """Sets speaker voice ID."""
        return self.provider.set_voice(voice_id)

    def get_voices(self) -> Optional[List[Any]]:
        """Lists available voice IDs."""
        return self.provider.get_voices()
