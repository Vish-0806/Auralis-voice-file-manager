"""Manages and plays audio cues/chimes for assistant states."""

import platform
from typing import Dict, Optional
from utils.logger import get_logger
from voice.ux.models import AssistantStatus

logger = get_logger(__name__)

# System sound names for Windows
WINDOWS_SOUND_MAP: Dict[AssistantStatus, str] = {
    AssistantStatus.WAKE_DETECTED: "SystemAsterisk",
    AssistantStatus.LISTENING: "SystemQuestion",
    AssistantStatus.PROCESSING: "SystemDefault",
    AssistantStatus.SPEAKING: "",
    AssistantStatus.WAITING: "",
    AssistantStatus.ERROR: "SystemHand",
    AssistantStatus.SLEEPING: "SystemExit",
}


class SoundManager:
    """Manages playing system alert sounds or custom WAV chimes for voice UX."""

    def __init__(self, custom_sounds: Optional[Dict[AssistantStatus, str]] = None) -> None:
        """Initializes the SoundManager.

        Args:
            custom_sounds: Optional dictionary overriding default state-sound mappings.
        """
        self._sound_map = dict(WINDOWS_SOUND_MAP)
        if custom_sounds is not None:
            self._sound_map.update(custom_sounds)

        self._is_windows = platform.system() == "Windows"

    def play_cue(self, status: AssistantStatus) -> None:
        """Plays the audio chime configured for the specified assistant status.

        Args:
            status: The target AssistantStatus state.
        """
        sound_target = self._sound_map.get(status)
        if not sound_target:
            logger.debug("No sound cue configured for status: %s", status.name)
            return

        logger.info("Playing audio cue for status: %s ('%s')", status.name, sound_target)

        # 1. Play on Windows via winsound
        if self._is_windows:
            try:
                import winsound

                # Checks if it's a file path or system alias
                flags = winsound.SND_ASYNC | winsound.SND_NODEFAULT
                if os_path_exists := (os_path_exists_check(sound_target)):
                    flags |= winsound.SND_FILENAME
                else:
                    flags |= winsound.SND_ALIAS

                winsound.PlaySound(sound_target, flags)
            except Exception as e:
                logger.error("Failed to play Windows system sound '%s': %s", sound_target, e)
        
        # 2. Log fallback on non-Windows systems
        else:
            logger.debug("[Sound Fallback Non-Windows] Play sound cue: %s", sound_target)


def os_path_exists_check(path: str) -> bool:
    """Helper to check if string is an existing file path safely."""
    try:
        import os
        return os.path.exists(path)
    except Exception:
        return False
