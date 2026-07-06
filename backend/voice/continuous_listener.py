"""
Continuous Listening module (Legacy compatibility wrapper).
Delegates to the new voice.listener module.
Exposes required imports to support test suite patching.
"""

from voice.speech_to_text import listen
from voice.wake_word import detect_wake_word
from voice.text_to_speech import speak as tts_speak
from ai.command_parser import parse_command
from capabilities.files.file_operations import execute_action


def __getattr__(name: str) -> any:
    """Dynamically resolve ContinuousListener and get_listener from voice.listener to break circular imports."""
    if name in {"ContinuousListener", "get_listener"}:
        import voice.listener as listener
        return getattr(listener, name)
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def __dir__() -> list[str]:
    """Exposes all public symbols in continuous_listener."""
    return [
        "listen",
        "detect_wake_word",
        "tts_speak",
        "parse_command",
        "execute_action",
        "ContinuousListener",
        "get_listener",
    ]
