"""
Speech-to-Text module (Legacy compatibility wrapper).
Delegates to the new VoiceManager.
"""

from typing import Optional
from voice.manager import get_voice_manager


def listen() -> Optional[str]:
    """Legacy compatibility wrapper for listen()."""
    return get_voice_manager().listen()
