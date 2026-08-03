"""Voice Orchestration Subsystem for Auralis (Phase 13.7).

Top-level Voice Orchestration Layer for the Assistant architecture. Coordinates Assistant,
Conversation, Dialogue, Decision, Memory, Response, Execution, and Speech runtimes without implementing
STT/TTS engines, microphone capture, or wake word detection algorithms.
"""

from brain.assistant.voice.exceptions import (
    SpeechRoutingException,
    VoiceRuntimeException,
    VoiceSessionException,
    VoiceStreamingException,
    VoiceValidationException,
    WakeWordException,
)
from brain.assistant.voice.interfaces import (
    ISpeechRouter,
    IVoiceCoordinator,
    IVoiceProvider,
    IVoiceRuntime,
    IVoiceSessionManager,
    IWakeWordManager,
)
from brain.assistant.voice.models import (
    ListeningMode,
    SpeechMode,
    VoiceCapabilities,
    VoiceConfiguration,
    VoiceContext,
    VoiceHealth,
    VoiceInteraction,
    VoiceInteractionType,
    VoiceRequest,
    VoiceResponse,
    VoiceSession,
    VoiceSessionState,
    VoiceState,
    VoiceStatistics,
    VoiceTranscript,
)
from brain.assistant.voice.runtime import (
    get_voice_runtime,
    reset_voice_runtime,
)
from brain.assistant.voice.session_manager import VoiceSessionManager
from brain.assistant.voice.speech_router import SpeechRouter
from brain.assistant.voice.voice_coordinator import VoiceCoordinator
from brain.assistant.voice.voice_provider import VoiceProvider
from brain.assistant.voice.voice_runtime import VoiceRuntime
from brain.assistant.voice.wake_word_manager import WakeWordManager

__all__ = [
    # Enums & Models
    "VoiceState",
    "ListeningMode",
    "SpeechMode",
    "VoiceSessionState",
    "VoiceInteractionType",
    "VoiceTranscript",
    "VoiceContext",
    "VoiceCapabilities",
    "VoiceConfiguration",
    "VoiceRequest",
    "VoiceResponse",
    "VoiceSession",
    "VoiceInteraction",
    "VoiceStatistics",
    "VoiceHealth",
    # Exceptions
    "VoiceRuntimeException",
    "VoiceSessionException",
    "SpeechRoutingException",
    "WakeWordException",
    "VoiceStreamingException",
    "VoiceValidationException",
    # Interfaces
    "IVoiceSessionManager",
    "IWakeWordManager",
    "ISpeechRouter",
    "IVoiceCoordinator",
    "IVoiceProvider",
    "IVoiceRuntime",
    # Managers & Components
    "VoiceSessionManager",
    "WakeWordManager",
    "SpeechRouter",
    "VoiceCoordinator",
    "VoiceProvider",
    "VoiceRuntime",
    # Singleton accessors
    "get_voice_runtime",
    "reset_voice_runtime",
]
