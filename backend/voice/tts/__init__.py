"""Text-to-Speech synthesis subsystem.

Exposes TTS configuration models, voice managers, audio outputs, and synthesis engines.
"""

from voice.tts.models import TTSConfiguration, SpeechResponse
from voice.tts.voice_manager import VoiceManager
from voice.tts.audio_output import AudioOutput
from voice.tts.text_to_speech import TextToSpeech

__all__ = [
    "TTSConfiguration",
    "SpeechResponse",
    "VoiceManager",
    "AudioOutput",
    "TextToSpeech",
]
