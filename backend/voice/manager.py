"""
Auralis Voice Manager
Coordinates wake word, speech recognition, speech synthesis, and sessions.
"""

from typing import Any, Dict, List, Optional
from voice.interfaces import IWakeWordDetector, ISpeechRecognizer, ISpeechSynthesizer, IVoiceSessionManager
from voice.providers.rule_wake_word import RuleWakeWordDetector
from voice.recognizer import SpeechRecognizer
from voice.synthesizer import SpeechSynthesizer
from voice.voice_session import VoiceSessionManager


class VoiceManager:
    """The central entry point coordinating voice tasks."""

    def __init__(
        self,
        wake_word_detector: Optional[IWakeWordDetector] = None,
        speech_recognizer: Optional[ISpeechRecognizer] = None,
        speech_synthesizer: Optional[ISpeechSynthesizer] = None,
        session_manager: Optional[IVoiceSessionManager] = None
    ) -> None:
        self.wake_word_detector = wake_word_detector or RuleWakeWordDetector()
        self.speech_recognizer = speech_recognizer or SpeechRecognizer()
        self.speech_synthesizer = speech_synthesizer or SpeechSynthesizer()
        self.session_manager = session_manager or VoiceSessionManager()

    def listen(self, timeout: float = 10.0, phrase_time_limit: float = 10.0) -> Optional[str]:
        """Delegates recognition to the underlying speech_recognizer."""
        return self.speech_recognizer.recognize(timeout=timeout, phrase_time_limit=phrase_time_limit)

    def speak(self, text: str, wait: bool = True) -> bool:
        """Delegates speech synthesis to the speech_synthesizer."""
        return self.speech_synthesizer.speak(text, wait=wait)

    def detect_wake_word(self, command: str) -> Dict[str, Any]:
        """Delegates wake phrase matching to the wake_word_detector."""
        return self.wake_word_detector.detect_wake_word(command)

    def get_pending_action(self) -> Optional[Dict[str, Any]]:
        """Delegates pending action checks to the session manager."""
        return self.session_manager.get_pending_action()

    def set_pending_action(self, action: str, target: str, destination: Optional[str] = None) -> None:
        """Sets a pending action details."""
        self.session_manager.set_pending_action(action, target, destination)

    def clear_pending_action(self) -> None:
        """Clears the pending action details."""
        self.session_manager.clear_pending_action()

    def set_rate(self, rate: int) -> bool:
        """Delegates speech rate config to the synthesizer."""
        return self.speech_synthesizer.set_rate(rate)

    def set_volume(self, volume: float) -> bool:
        """Delegates speech volume config to the synthesizer."""
        return self.speech_synthesizer.set_volume(volume)

    def set_voice(self, voice_id: str) -> bool:
        """Delegates speaker voice selection to the synthesizer."""
        return self.speech_synthesizer.set_voice(voice_id)

    def get_voices(self) -> Optional[List[Any]]:
        """Returns available voice definitions."""
        return self.speech_synthesizer.get_voices()


# Global VoiceManager singleton instance getter
_voice_manager_instance = None


def get_voice_manager() -> VoiceManager:
    """Retrieves or instantiates the default VoiceManager singleton."""
    global _voice_manager_instance
    if _voice_manager_instance is None:
        _voice_manager_instance = VoiceManager()
    return _voice_manager_instance
