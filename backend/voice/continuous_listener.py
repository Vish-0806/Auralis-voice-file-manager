"""
Continuous Listening module (Legacy compatibility wrapper).
Delegates to the new voice.listener module.
Exposes required imports to support test suite patching.
"""

from voice.speech_to_text import listen
from voice.wake_word import detect_wake_word
from voice.text_to_speech import speak as tts_speak
from ai_engine.command_parser import parse_command
from file_engine.file_operations import execute_action

from voice.listener import ContinuousListener, get_listener
