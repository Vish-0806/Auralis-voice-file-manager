"""Auralis Wake Word Subsystem.

Provides the components to listen for and detect wake word activation phrases.
"""

from typing import Any, Dict, List
from voice.wake_word.models import WakeWordConfiguration, WakeWordState, WakeWordEvent
from voice.wake_word.detector import WakeWordDetector
from voice.wake_word.listener import WakeWordListener

# Legacy compatibility exports
from voice.providers.rule_wake_word import DEFAULT_WAKE_PHRASES as WAKE_PHRASES
from voice.manager import get_voice_manager


def detect_wake_word(command: str) -> Dict[str, Any]:
    """Legacy compatibility wrapper for detect_wake_word().

    Args:
        command: The raw voice command text to check.

    Returns:
        Dict[str, Any]: A dictionary containing 'activated' (bool) and 'cleaned_command' (str).
    """
    return get_voice_manager().detect_wake_word(command)


__all__ = [
    "WakeWordConfiguration",
    "WakeWordState",
    "WakeWordEvent",
    "WakeWordDetector",
    "WakeWordListener",
    "WAKE_PHRASES",
    "detect_wake_word",
]
