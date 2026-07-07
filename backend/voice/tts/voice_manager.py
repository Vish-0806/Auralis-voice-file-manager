"""Manages available voices and profiles across speech engines."""

from typing import Any, Dict, List, Optional
from utils.logger import get_logger

logger = get_logger(__name__)

# List of standard Microsoft Edge Neural TTS voices (popular locales)
EDGE_NEURAL_VOICES: List[Dict[str, Any]] = [
    {
        "id": "en-US-AriaNeural",
        "name": "Aria (Female) - English (US)",
        "gender": "Female",
        "language": "en-US",
    },
    {
        "id": "en-US-GuyNeural",
        "name": "Guy (Male) - English (US)",
        "gender": "Male",
        "language": "en-US",
    },
    {
        "id": "en-GB-SoniaNeural",
        "name": "Sonia (Female) - English (UK)",
        "gender": "Female",
        "language": "en-GB",
    },
    {
        "id": "en-GB-RyanNeural",
        "name": "Ryan (Male) - English (UK)",
        "gender": "Male",
        "language": "en-GB",
    },
    {
        "id": "en-IN-NeerjaNeural",
        "name": "Neerja (Female) - English (India)",
        "gender": "Female",
        "language": "en-IN",
    },
    {
        "id": "en-IN-PrabhatNeural",
        "name": "Prabhat (Male) - English (India)",
        "gender": "Male",
        "language": "en-IN",
    },
]


class VoiceManager:
    """Manages system voice loading, defaults, and custom profiles."""

    def __init__(self) -> None:
        """Initializes the VoiceManager and registers default profiles."""
        self._profiles: Dict[str, Dict[str, Any]] = {}
        self._register_default_profiles()

    def _register_default_profiles(self) -> None:
        """Registers basic default voice profiles."""
        self.register_profile(
            "default_edge",
            {
                "engine": "edge-tts",
                "voice_id": "en-US-AriaNeural",
                "rate": 150,
                "volume": 1.0,
            },
        )
        self.register_profile(
            "default_pyttsx3",
            {
                "engine": "pyttsx3",
                "voice_id": None,  # Uses system default
                "rate": 150,
                "volume": 1.0,
            },
        )

    def list_voices(self, engine: str) -> List[Dict[str, Any]]:
        """Lists available voice identifiers and metadata for a specific engine.

        Args:
            engine: The target engine ("edge-tts" or "pyttsx3").

        Returns:
            A list of voice details dictionaries.
        """
        engine_name = engine.lower().strip()

        if engine_name == "edge-tts":
            # Check if edge-tts is installed and try dynamically loading online list
            try:
                import edge_tts
                # Simply return our rich static list for speed and reliability,
                # but log availability of local Edge-TTS package.
                logger.debug("Edge-TTS package is available.")
            except ImportError:
                logger.debug("Edge-TTS package not installed. Using static voice profiles.")
            return EDGE_NEURAL_VOICES

        if engine_name == "pyttsx3":
            try:
                import pyttsx3
                temp_engine = pyttsx3.init()
                py_voices = temp_engine.getProperty("voices")
                voices_list = []
                for voice in py_voices:
                    voices_list.append({
                        "id": getattr(voice, "id", None),
                        "name": getattr(voice, "name", None),
                        "gender": getattr(voice, "gender", None),
                        "language": getattr(voice, "languages", []),
                    })
                return voices_list
            except Exception as e:
                logger.error("Failed to query pyttsx3 voices: %s", e)
                return []

        logger.warning("Unsupported engine requested: %s", engine)
        return []

    def get_default_voice(self, engine: str) -> Optional[str]:
        """Gets the default voice identifier for the requested engine.

        Args:
            engine: The target engine.

        Returns:
            A default voice ID string, or None.
        """
        engine_name = engine.lower().strip()
        if engine_name == "edge-tts":
            return "en-US-AriaNeural"
        elif engine_name == "pyttsx3":
            # For pyttsx3, returning None triggers the library's internal default
            return None
        return None

    def register_profile(self, name: str, profile_config: Dict[str, Any]) -> None:
        """Saves a custom voice configuration profile.

        Args:
            name: A unique name for the voice profile.
            profile_config: A dictionary representing configuration parameters.
        """
        logger.info("Registering voice profile: %s", name)
        self._profiles[name] = profile_config

    def get_profile(self, name: str) -> Optional[Dict[str, Any]]:
        """Retrieves a saved custom voice configuration profile.

        Args:
            name: The name of the profile.

        Returns:
            The profile config dictionary or None.
        """
        return self._profiles.get(name)
