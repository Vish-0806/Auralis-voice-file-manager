"""
Auralis Google Speech Recognizer Provider
Implements speech recognition using Google Speech API.
"""

from typing import Optional
# pyrefly: ignore [missing-import]
import speech_recognition as sr
from utils.logger import get_logger
from voice.interfaces import ISpeechRecognizer
from voice.audio_stream import MicrophoneAudioStream

logger = get_logger(__name__)


class GoogleSpeechRecognizer(ISpeechRecognizer):
    """Wraps Google Speech Recognition engine with dynamic ambient adjustments."""

    def __init__(self, audio_stream: Optional[MicrophoneAudioStream] = None) -> None:
        self.audio_stream = audio_stream or MicrophoneAudioStream()
        self.recognizer = sr.Recognizer()

    def recognize(self, timeout: float = 10.0, phrase_time_limit: float = 10.0) -> Optional[str]:
        """Captures audio from stream and converts to text."""
        try:
            source = self.audio_stream.get_source()
            with source as active_source:
                logger.info("Listening for microphone input...")

                # Adjust recognizer sensitivity to ambient noise
                self.recognizer.adjust_for_ambient_noise(active_source, duration=0.5)

                # Listen for audio with timeout
                audio = self.recognizer.listen(active_source, timeout=timeout, phrase_time_limit=phrase_time_limit)

        except Exception as e:
            logger.error(f"Microphone initialization or capture failure: {str(e)}")
            return None

        logger.info("Processing captured audio...")

        # Convert speech to text using Google Speech Recognition
        try:
            text = self.recognizer.recognize_google(audio)
            text = text.lower()

            logger.info(f"Recognized command: {text}")
            return text

        except sr.UnknownValueError:
            logger.warning("Speech recognition failure: audio could not be understood")
            return None

        except sr.RequestError as e:
            logger.error(f"API/service failure during speech recognition: {str(e)}")
            return None

        except Exception as e:
            logger.error(f"Unexpected speech recognition failure: {str(e)}")
            return None
