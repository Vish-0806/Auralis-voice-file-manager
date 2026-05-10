"""
Speech-to-Text module using SpeechRecognition library.
Provides microphone-based voice input recognition with ambient noise detection.
"""

import speech_recognition as sr
from utils.logger import get_logger

logger = get_logger(__name__)


def listen():
    """
    Listen to microphone input and convert speech to text.
    
    Features:
    - Detects and adapts to ambient noise
    - Converts recognized speech to lowercase
    - Handles errors gracefully
    
    Returns:
        str: Recognized command text in lowercase, or None on failure
    """
    
    try:
        recognizer = sr.Recognizer()

        try:
            # Use default microphone as audio source
            with sr.Microphone() as source:
                logger.info("Listening for microphone input...")

                # Adjust recognizer sensitivity to ambient noise
                recognizer.adjust_for_ambient_noise(source, duration=0.5)

                # Listen for audio with timeout
                audio = recognizer.listen(source, timeout=10, phrase_time_limit=10)

        except Exception as e:
            logger.error(f"Microphone initialization or capture failure: {str(e)}")
            return None

        logger.info("Processing captured audio...")

        # Convert speech to text using Google Speech Recognition
        try:
            text = recognizer.recognize_google(audio)
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

    except Exception as e:
        logger.error(f"Unexpected microphone/device/runtime failure: {str(e)}")
        return None
