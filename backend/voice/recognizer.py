"""
Auralis Speech Recognizer
Exposes the speech-to-text recognition API.
"""

from typing import Optional
from voice.interfaces import ISpeechRecognizer
from voice.providers.google_recognizer import GoogleSpeechRecognizer


class SpeechRecognizer(ISpeechRecognizer):
    """Orchestrates speech recognition using configured providers."""

    def __init__(self, provider: Optional[ISpeechRecognizer] = None) -> None:
        self.provider = provider or GoogleSpeechRecognizer()

    def recognize(self, timeout: float = 10.0, phrase_time_limit: float = 10.0) -> Optional[str]:
        """Delegates recognition to the underlying provider."""
        return self.provider.recognize(timeout=timeout, phrase_time_limit=phrase_time_limit)
