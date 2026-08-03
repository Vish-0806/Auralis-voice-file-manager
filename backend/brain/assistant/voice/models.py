"""Voice Orchestration Data Models for Auralis (Phase 13.7).

Defines immutable Pydantic v2 domain models and enums representing voice sessions,
requests, responses, transcripts, contexts, capabilities, statistics, health, configurations,
and interactions using ConfigDict(frozen=True).
"""

from datetime import datetime, timezone
from enum import Enum
import uuid
from typing import Any, Dict, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


class VoiceState(str, Enum):
    """Overall operational state of the voice orchestrator."""

    IDLE = "IDLE"
    LISTENING = "LISTENING"
    PROCESSING = "PROCESSING"
    SPEAKING = "SPEAKING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"


class ListeningMode(str, Enum):
    """Listening modes supported by the voice subsystem."""

    PUSH_TO_TALK = "PUSH_TO_TALK"
    CONTINUOUS = "CONTINUOUS"
    CONVERSATION = "CONVERSATION"
    WAKE_WORD = "WAKE_WORD"


class SpeechMode(str, Enum):
    """Speech output synthesis modes."""

    SYNTHESIZED = "SYNTHESIZED"
    STREAMED = "STREAMED"
    MUTED = "MUTED"
    PASSTHROUGH = "PASSTHROUGH"


class VoiceSessionState(str, Enum):
    """Lifecycle state of a voice session."""

    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    CLOSED = "CLOSED"
    EXPIRED = "EXPIRED"


class VoiceInteractionType(str, Enum):
    """Categories of voice interactions."""

    COMMAND = "COMMAND"
    DIALOGUE = "DIALOGUE"
    QUERY = "QUERY"
    NOTIFICATION = "NOTIFICATION"


class VoiceTranscript(BaseModel):
    """Immutable transcript produced by Speech-to-Text routing."""

    model_config = ConfigDict(frozen=True)

    transcript_id: str = Field(default_factory=lambda: f"tr-{uuid.uuid4().hex[:8]}")
    text: str = ""
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    is_final: bool = True
    language: str = "en-US"
    duration_ms: float = 0.0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VoiceContext(BaseModel):
    """Immutable snapshot of environmental context for voice operations."""

    model_config = ConfigDict(frozen=True)

    session_id: Optional[str] = None
    user_id: Optional[str] = None
    listening_mode: ListeningMode = ListeningMode.PUSH_TO_TALK
    speech_mode: SpeechMode = SpeechMode.SYNTHESIZED
    active_device_id: Optional[str] = None
    ambient_noise_level_db: float = 0.0
    custom_variables: Dict[str, Any] = Field(default_factory=dict)


class VoiceCapabilities(BaseModel):
    """Immutable specification of voice orchestration capabilities."""

    model_config = ConfigDict(frozen=True)

    supports_wake_word: bool = True
    supports_continuous_listening: bool = True
    supports_streaming_tts: bool = True
    supports_push_to_talk: bool = True
    supported_languages: List[str] = Field(default_factory=lambda: ["en-US"])
    max_session_duration_seconds: int = 3600


class VoiceConfiguration(BaseModel):
    """Immutable runtime configuration parameters for the voice orchestrator."""

    model_config = ConfigDict(frozen=True)

    listening_mode: ListeningMode = ListeningMode.PUSH_TO_TALK
    speech_mode: SpeechMode = SpeechMode.SYNTHESIZED
    wake_word_enabled: bool = True
    wake_word_phrase: str = "hey auralis"
    session_timeout_seconds: float = 300.0
    auto_tts_reply: bool = True


class VoiceRequest(BaseModel):
    """Immutable voice request structure for initiating a voice interaction."""

    model_config = ConfigDict(frozen=True)

    request_id: str = Field(default_factory=lambda: f"vreq-{uuid.uuid4().hex[:8]}")
    session_id: Optional[str] = None
    transcript: VoiceTranscript = Field(default_factory=VoiceTranscript)
    context: VoiceContext = Field(default_factory=VoiceContext)
    interaction_type: VoiceInteractionType = VoiceInteractionType.COMMAND
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class VoiceResponse(BaseModel):
    """Immutable voice response output from voice orchestration."""

    model_config = ConfigDict(frozen=True)

    response_id: str = Field(default_factory=lambda: f"vresp-{uuid.uuid4().hex[:8]}")
    request_id: str = ""
    text_content: str = ""
    audio_stream_id: Optional[str] = None
    speech_mode: SpeechMode = SpeechMode.SYNTHESIZED
    state: VoiceState = VoiceState.COMPLETED
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class VoiceSession(BaseModel):
    """Immutable voice session container tracking interaction lifecycle."""

    model_config = ConfigDict(frozen=True)

    session_id: str = Field(default_factory=lambda: f"vsess-{uuid.uuid4().hex[:8]}")
    user_id: Optional[str] = None
    state: VoiceSessionState = VoiceSessionState.ACTIVE
    listening_mode: ListeningMode = ListeningMode.PUSH_TO_TALK
    speech_mode: SpeechMode = SpeechMode.SYNTHESIZED
    interaction_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_active_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VoiceInteraction(BaseModel):
    """Immutable record of an individual voice request-response turn."""

    model_config = ConfigDict(frozen=True)

    interaction_id: str = Field(default_factory=lambda: f"vint-{uuid.uuid4().hex[:8]}")
    session_id: str = ""
    request: VoiceRequest = Field(default_factory=VoiceRequest)
    response: Optional[VoiceResponse] = None
    completed: bool = False
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class VoiceStatistics(BaseModel):
    """Immutable statistics metrics for voice orchestration."""

    model_config = ConfigDict(frozen=True)

    total_sessions_created: int = 0
    active_sessions: int = 0
    total_interactions: int = 0
    speech_to_text_routed: int = 0
    text_to_speech_routed: int = 0
    wake_word_triggers: int = 0
    average_pipeline_latency_ms: float = 0.0
    uptime_seconds: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VoiceHealth(BaseModel):
    """Immutable diagnostic health report of the voice orchestration subsystem."""

    model_config = ConfigDict(frozen=True)

    status: str = "READY"
    healthy: bool = True
    subsystems: Dict[str, bool] = Field(default_factory=dict)
    statistics: Dict[str, Any] = Field(default_factory=dict)
    detected_issues: List[str] = Field(default_factory=list)
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)
