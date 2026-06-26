"""
Text-to-Speech module (Legacy compatibility wrapper).
Delegates to the new VoiceManager.
"""

from typing import Any, List, Optional
from voice.manager import get_voice_manager


def speak(text: str, wait: bool = True) -> bool:
    """Legacy compatibility wrapper for speak()."""
    return get_voice_manager().speak(text, wait=wait)


def set_rate(rate: int) -> bool:
    """Legacy compatibility wrapper for set_rate()."""
    return get_voice_manager().set_rate(rate)


def set_volume(volume: float) -> bool:
    """Legacy compatibility wrapper for set_volume()."""
    return get_voice_manager().set_volume(volume)


def set_voice(voice_id: str) -> bool:
    """Legacy compatibility wrapper for set_voice()."""
    return get_voice_manager().set_voice(voice_id)


def get_voices() -> Optional[List[Any]]:
    """Legacy compatibility wrapper for get_voices()."""
    return get_voice_manager().get_voices()


__all__ = ["speak", "set_rate", "set_volume", "set_voice", "get_voices"]
