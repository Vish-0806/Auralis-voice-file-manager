"""Speech Recognition subsystem.

Exposes the modules for microphone capture, audio processing, configuration models,
and speech-to-text translation.
"""

from voice.speech.models import SpeechConfiguration, SpeechRequest, SpeechResult
from voice.speech.microphone import Microphone
from voice.speech.audio_processor import AudioProcessor
from voice.speech.speech_to_text import SpeechToText

__all__ = [
    "SpeechConfiguration",
    "SpeechRequest",
    "SpeechResult",
    "Microphone",
    "AudioProcessor",
    "SpeechToText",
]
