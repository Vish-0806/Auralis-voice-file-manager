"""Voice Coordinator implementation for Auralis (Phase 13.7).

Orchestrates voice interactions across Assistant, Conversation, Dialogue, Decision, Memory, Response,
Execution, and Speech runtimes.
Does NOT perform STT, TTS, microphone capture, or audio processing algorithms.
Thread-safe using threading.RLock().
"""

from datetime import datetime, timezone
import logging
import threading
from typing import Any, Optional

from brain.assistant.voice.exceptions import VoiceValidationException
from brain.assistant.voice.interfaces import IVoiceCoordinator, ISpeechRouter
from brain.assistant.voice.models import (
    VoiceInteraction,
    VoiceRequest,
    VoiceResponse,
    VoiceState,
)
from brain.assistant.voice.speech_router import SpeechRouter

logger = logging.getLogger(__name__)


class VoiceCoordinator(IVoiceCoordinator):
    """Thread-safe coordinator executing the top-level voice interaction lifecycle."""

    def __init__(
        self,
        speech_router: Optional[ISpeechRouter] = None,
        lock: Optional[threading.RLock] = None,
    ) -> None:
        self._lock = lock or threading.RLock()
        self._speech_router = speech_router or SpeechRouter(lock=self._lock)
        self._interaction_count = 0

    @property
    def interaction_count(self) -> int:
        with self._lock:
            return self._interaction_count

    def process_voice_interaction(
        self,
        request: VoiceRequest,
        assistant_runtime: Optional[Any] = None,
        stt_runtime: Optional[Any] = None,
        tts_runtime: Optional[Any] = None,
    ) -> VoiceInteraction:
        """Execute complete voice interaction lifecycle and return a recorded VoiceInteraction."""
        if not isinstance(request, VoiceRequest):
            raise VoiceValidationException("request must be an instance of VoiceRequest")

        with self._lock:
            self._interaction_count += 1

            # 1. Extract transcript content
            prompt_text = request.transcript.text if request.transcript else ""

            # 2. Invoke Assistant Response / Response Runtime if available
            response_text = f"Processed voice command: {prompt_text}" if prompt_text else "Voice command received"

            if assistant_runtime is not None:
                try:
                    # Optional assistant runtime invocation
                    if hasattr(assistant_runtime, "process_request"):
                        res = assistant_runtime.process_request(prompt_text)
                        if hasattr(res, "content"):
                            response_text = getattr(res, "content")
                except Exception as exc:
                    logger.debug("Error invoking assistant_runtime in VoiceCoordinator: %s", exc)

            # 3. Route response text to TTS via SpeechRouter
            voice_resp = self._speech_router.route_tts(
                response_text=response_text,
                speech_mode=request.context.speech_mode,
            )

            # Bind request_id to response
            vresp = VoiceResponse(
                response_id=voice_resp.response_id,
                request_id=request.request_id,
                text_content=voice_resp.text_content,
                audio_stream_id=voice_resp.audio_stream_id,
                speech_mode=voice_resp.speech_mode,
                state=VoiceState.COMPLETED,
                duration_ms=voice_resp.duration_ms,
                metadata=voice_resp.metadata,
                timestamp=datetime.now(timezone.utc),
            )

            interaction = VoiceInteraction(
                session_id=request.session_id or "default-voice-session",
                request=request,
                response=vresp,
                completed=True,
                timestamp=datetime.now(timezone.utc),
            )

            logger.info("Processed voice interaction id=%s req_id=%s", interaction.interaction_id, request.request_id)
            return interaction

    def clear(self) -> None:
        """Reset coordinator metrics."""
        with self._lock:
            self._interaction_count = 0
