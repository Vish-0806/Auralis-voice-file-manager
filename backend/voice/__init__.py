"""
Auralis Voice Package
Contains speech recognition, wake word detection, and text-to-speech functionality.
"""

from voice.listener import ContinuousListener, get_listener
from voice.manager import VoiceManager, get_voice_manager

# Legacy direct functions for backward compatibility
from voice.speech_to_text import listen
from voice.text_to_speech import speak
from voice.wake_word import detect_wake_word

__all__ = [
    "ContinuousListener",
    "get_listener",
    "VoiceManager",
    "get_voice_manager",
    "listen",
    "speak",
    "detect_wake_word",
]
