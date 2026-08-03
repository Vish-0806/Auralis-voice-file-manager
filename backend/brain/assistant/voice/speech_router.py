"""Speech Router implementation for Auralis (Phase 13.7).

Routes speech input to STT runtime and assistant output to TTS runtime across
Push-To-Talk, Continuous Listening, Conversation, and Wake Word modes without speech engines or networking calls.
Thread-safe using threading.RLock().
"""

from datetime import datetime, timezone
import logging
import threading
from typing import Any, Optional

from brain.assistant.voice.exceptions import SpeechRoutingException
from brain.assistant.voice.interfaces import ISpeechRouter
from brain.assistant.voice.models import (
    SpeechMode,
    VoiceResponse,
    VoiceState,
    VoiceTranscript,
)

logger = logging.getLogger(__name__)


class SpeechRouter(ISpeechRouter):
    """Thread-safe speech input/output router delegating between STT, Assistant, and TTS runtimes."""

    def __init__(self, lock: Optional[threading.RLock] = None) -> None:
        self._lock = lock or threading.RLock()

        # Metrics
        self._stt_routed = 0
        self._tts_routed = 0

    @property
    def stt_routed_count(self) -> int:
        with self._lock:
            return self._stt_routed

    @property
    def tts_routed_count(self) -> int:
        with self._lock:
            return self._tts_routed

    def route_stt(self, audio_data: Any) -> VoiceTranscript:
        """Route input audio data or raw text payload to STT runtime and return VoiceTranscript."""
        with self._lock:
            self._stt_routed += 1

            if isinstance(audio_data, str):
                text_content = audio_data
            elif hasattr(audio_data, "text"):
                text_content = getattr(audio_data, "text")
            else:
                text_content = str(audio_data) if audio_data is not None else ""

            transcript = VoiceTranscript(
                text=text_content,
                confidence=1.0 if text_content else 0.0,
                is_final=True,
                language="en-US",
                timestamp=datetime.now(timezone.utc),
            )

            logger.info("Routed STT text='%s' (total_stt=%d)", text_content, self._stt_routed)
            return transcript

    def route_tts(
        self,
        response_text: str,
        speech_mode: SpeechMode = SpeechMode.SYNTHESIZED,
    ) -> VoiceResponse:
        """Route assistant response text to TTS runtime and return VoiceResponse."""
        with self._lock:
            self._tts_routed += 1

            audio_stream: Optional[str] = None
            if speech_mode in (SpeechMode.SYNTHESIZED, SpeechMode.STREAMED):
                audio_stream = f"astream-{self._tts_routed}"

            response = VoiceResponse(
                request_id="",
                text_content=response_text or "",
                audio_stream_id=audio_stream,
                speech_mode=speech_mode,
                state=VoiceState.COMPLETED,
                duration_ms=0.0,
                timestamp=datetime.now(timezone.utc),
            )

            logger.info("Routed TTS mode=%s text_len=%d (total_tts=%d)", speech_mode, len(response_text), self._tts_routed)
            return response

    def clear(self) -> None:
        """Reset routing statistics."""
        with self._lock:
            self._stt_routed = 0
            self._tts_routed = 0
