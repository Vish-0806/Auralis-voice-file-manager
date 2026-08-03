"""Abstract Interfaces for Voice Orchestration Runtime (Phase 13.7).

Defines Python ABC abstract interfaces for voice session management, wake word control,
speech routing, voice coordination, provider aggregation, and top-level runtime orchestration.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from brain.assistant.voice.models import (
    ListeningMode,
    SpeechMode,
    VoiceCapabilities,
    VoiceConfiguration,
    VoiceContext,
    VoiceHealth,
    VoiceInteraction,
    VoiceRequest,
    VoiceResponse,
    VoiceSession,
    VoiceSessionState,
    VoiceStatistics,
    VoiceTranscript,
)


class IVoiceSessionManager(ABC):
    """Abstract interface for managing voice session lifecycles."""

    @abstractmethod
    def create_session(
        self,
        user_id: Optional[str] = None,
        listening_mode: ListeningMode = ListeningMode.PUSH_TO_TALK,
        speech_mode: SpeechMode = SpeechMode.SYNTHESIZED,
    ) -> VoiceSession:
        """Create and register a new VoiceSession."""
        pass

    @abstractmethod
    def get_session(self, session_id: str) -> Optional[VoiceSession]:
        """Retrieve an active VoiceSession by ID."""
        pass

    @abstractmethod
    def pause_session(self, session_id: str) -> VoiceSession:
        """Pause an active VoiceSession."""
        pass

    @abstractmethod
    def resume_session(self, session_id: str) -> VoiceSession:
        """Resume a paused VoiceSession."""
        pass

    @abstractmethod
    def close_session(self, session_id: str) -> VoiceSession:
        """Close and terminate a VoiceSession."""
        pass

    @abstractmethod
    def list_active_sessions(self) -> List[VoiceSession]:
        """List all active voice sessions."""
        pass


class IWakeWordManager(ABC):
    """Abstract interface for managing wake word orchestration states."""

    @abstractmethod
    def enable(self) -> bool:
        """Enable wake word orchestration."""
        pass

    @abstractmethod
    def disable(self) -> bool:
        """Disable wake word orchestration."""
        pass

    @abstractmethod
    def pause(self) -> bool:
        """Pause wake word orchestration."""
        pass

    @abstractmethod
    def resume(self) -> bool:
        """Resume wake word orchestration."""
        pass

    @property
    @abstractmethod
    def is_enabled(self) -> bool:
        """Check if wake word orchestration is enabled."""
        pass


class ISpeechRouter(ABC):
    """Abstract interface for routing speech input/output between STT, Assistant, and TTS runtimes."""

    @abstractmethod
    def route_stt(self, audio_data: Any) -> VoiceTranscript:
        """Route audio data to STT runtime and return a VoiceTranscript."""
        pass

    @abstractmethod
    def route_tts(self, response_text: str, speech_mode: SpeechMode = SpeechMode.SYNTHESIZED) -> VoiceResponse:
        """Route assistant response text to TTS runtime and return a VoiceResponse."""
        pass


class IVoiceCoordinator(ABC):
    """Abstract interface for coordinating voice interactions across all assistant and speech runtimes."""

    @abstractmethod
    def process_voice_interaction(
        self,
        request: VoiceRequest,
        assistant_runtime: Optional[Any] = None,
        stt_runtime: Optional[Any] = None,
        tts_runtime: Optional[Any] = None,
    ) -> VoiceInteraction:
        """Execute complete voice interaction lifecycle and return a recorded VoiceInteraction."""
        pass


class IVoiceProvider(ABC):
    """Abstract interface aggregating coordinator, speech router, wake word manager, and session manager."""

    @property
    @abstractmethod
    def coordinator(self) -> IVoiceCoordinator:
        """Get the voice coordinator."""
        pass

    @property
    @abstractmethod
    def speech_router(self) -> ISpeechRouter:
        """Get the speech router."""
        pass

    @property
    @abstractmethod
    def wake_word_manager(self) -> IWakeWordManager:
        """Get the wake word manager."""
        pass

    @property
    @abstractmethod
    def session_manager(self) -> IVoiceSessionManager:
        """Get the voice session manager."""
        pass

    @abstractmethod
    def get_capabilities(self) -> VoiceCapabilities:
        """Get voice orchestration capabilities."""
        pass

    @abstractmethod
    def get_health(self) -> VoiceHealth:
        """Get diagnostic health report."""
        pass

    @abstractmethod
    def get_statistics(self) -> VoiceStatistics:
        """Get aggregated voice statistics."""
        pass

    @abstractmethod
    def initialize(self) -> None:
        """Initialize provider resources."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown provider resources."""
        pass

    @property
    @abstractmethod
    def is_initialized(self) -> bool:
        """Check if provider is initialized."""
        pass


class IVoiceRuntime(ABC):
    """Abstract interface for top-level Voice Orchestration Runtime orchestration."""

    @abstractmethod
    def initialize(self) -> None:
        """Initialize voice runtime."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown voice runtime."""
        pass

    @abstractmethod
    def restart(self) -> None:
        """Restart voice runtime."""
        pass

    @abstractmethod
    def get_health(self) -> VoiceHealth:
        """Get overall health status."""
        pass

    @abstractmethod
    def get_statistics(self) -> VoiceStatistics:
        """Get runtime performance statistics."""
        pass

    @abstractmethod
    def get_capabilities(self) -> VoiceCapabilities:
        """Get voice capabilities."""
        pass

    @property
    @abstractmethod
    def is_initialized(self) -> bool:
        """Check if runtime is initialized."""
        pass
