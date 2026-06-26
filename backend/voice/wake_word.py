"""
Wake Word Detection module (Legacy compatibility wrapper).
Delegates to the new VoiceManager.
"""

from typing import Any, Dict
from voice.manager import get_voice_manager
from voice.providers.rule_wake_word import DEFAULT_WAKE_PHRASES as WAKE_PHRASES


def detect_wake_word(command: str) -> Dict[str, Any]:
    """Legacy compatibility wrapper for detect_wake_word()."""
    return get_voice_manager().detect_wake_word(command)
