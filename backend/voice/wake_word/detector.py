"""Wake Word Detector.

Implements the pattern-matching wake word detection logic and publishes events when activated.
"""

import re
import time
from typing import Any, Dict, List, Optional, Callable
from utils.logger import get_logger
from voice.wake_word.models import WakeWordConfiguration, WakeWordEvent

logger = get_logger(__name__)

_PUNCTUATION_RE = re.compile(r"[^\w\s]", re.UNICODE)
_EXTRA_SPACE_RE = re.compile(r"\s{2,}")


class WakeWordDetector:
    """Detects wake phrases and publishes WakeWordDetected events.

    Attributes:
        config (WakeWordConfiguration): Configuration settings for the detector.
        event_bus (Optional[Any]): The system event bus instance to publish events to.
    """

    def __init__(
        self,
        config: Optional[WakeWordConfiguration] = None,
        event_bus: Optional[Any] = None,
    ) -> None:
        """Initializes the WakeWordDetector with config and event bus.

        Args:
            config: Optional configuration options.
            event_bus: Optional central EventBus to publish events.
        """
        self.config = config or WakeWordConfiguration()
        self.event_bus = event_bus
        self._callbacks: List[Callable[[WakeWordEvent], None]] = []
        self._simulated_phrase: Optional[str] = None
        self._simulated_confidence: float = 1.0

    def register_callback(self, callback: Callable[[WakeWordEvent], None]) -> None:
        """Registers a callback to be notified when a wake word is detected.

        Args:
            callback: Callable that takes a WakeWordEvent.
        """
        self._callbacks.append(callback)

    def simulate_wake_word(self, phrase: str, confidence: float = 1.0) -> None:
        """Queues a simulated wake word to be triggered on the next audio processing.

        Args:
            phrase: The phrase to simulate.
            confidence: The confidence score for the simulation.
        """
        self._simulated_phrase = phrase
        self._simulated_confidence = confidence
        logger.info("Queued simulated wake word: '%s'", phrase)

    def _normalize(self, text: str) -> str:
        """Lowercases and cleans up punctuation or extra whitespaces.

        Args:
            text: The text to normalize.

        Returns:
            The cleaned and normalized string.
        """
        if not text:
            return ""
        text = text.lower()
        text = _PUNCTUATION_RE.sub("", text)
        text = _EXTRA_SPACE_RE.sub(" ", text)
        return text.strip()

    def detect_in_text(self, text: str) -> Optional[WakeWordEvent]:
        """Checks if a text string contains a valid wake phrase at the start.

        Args:
            text: The input text to check.

        Returns:
            A WakeWordEvent if a wake phrase was matched, otherwise None.
        """
        if not isinstance(text, str):
            return None

        normalized = self._normalize(text)
        for phrase in self.config.wake_phrases:
            normalized_phrase = self._normalize(phrase)
            if normalized.startswith(normalized_phrase):
                event = WakeWordEvent(
                    phrase=phrase,
                    detected_at=time.time(),
                    confidence=1.0,
                    audio_data_summary="text_input",
                )
                self._publish_and_notify(event)
                return event
        return None

    def process_audio_chunk(self, chunk: bytes) -> Optional[WakeWordEvent]:
        """Processes a single raw audio chunk from the listener.

        Args:
            chunk: Raw PCM audio bytes.

        Returns:
            A WakeWordEvent if a wake word was detected (or simulated), otherwise None.
        """
        # Calculate signal level (RMS) to confirm audio presence
        rms = 0
        try:
            try:
                import audioop
            except ImportError:
                import audioop_lts as audioop
            
            if audioop is not None and len(chunk) > 0:
                rms = audioop.rms(chunk, 2)  # Assuming 16-bit depth (2 bytes/sample)
        except Exception as e:
            logger.debug("Failed to calculate RMS on audio chunk: %s", str(e))

        # Check for simulated wake word injection
        if self._simulated_phrase:
            phrase = self._simulated_phrase
            confidence = self._simulated_confidence
            self._simulated_phrase = None
            
            logger.info("Simulating wake word detection for: '%s'", phrase)
            event = WakeWordEvent(
                phrase=phrase,
                detected_at=time.time(),
                confidence=confidence,
                audio_data_summary=f"simulated_rms_{rms}",
            )
            self._publish_and_notify(event)
            return event

        # No real speech recognition is implemented here
        return None

    def _publish_and_notify(self, event: WakeWordEvent) -> None:
        """Publishes the wake word event to the central event bus and notifies callbacks.

        Args:
            event: The WakeWordEvent to publish.
        """
        logger.info("Wake word detected: '%s' (confidence: %.2f)", event.phrase, event.confidence)

        # Notify local callbacks
        for callback in self._callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error("Error in wake word callback: %s", str(e))

        # Publish to the system event bus if present
        if self.event_bus is not None:
            try:
                from events.models import EventEnvelope
                from events.event_types import SystemEvents
                
                envelope = EventEnvelope(
                    event_type=SystemEvents.WAKE_WORD_DETECTED,
                    sender="wake_word_detector",
                    payload={
                        "phrase": event.phrase,
                        "detected_at": event.detected_at,
                        "confidence": event.confidence,
                        "audio_data_summary": event.audio_data_summary,
                    }
                )
                self.event_bus.publish_envelope(envelope)
                logger.debug("Published WakeWordDetected event to event bus.")
            except Exception as e:
                logger.error("Failed to publish WakeWordDetected event to EventBus: %s", str(e))
