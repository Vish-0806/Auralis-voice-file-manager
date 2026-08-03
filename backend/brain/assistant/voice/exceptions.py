"""Voice Orchestration Exception Hierarchy (Phase 13.7).

Defines custom exception classes for voice session lifecycle, speech routing,
wake word management, streaming, and validation errors.
"""


class VoiceRuntimeException(Exception):
    """Base exception class for all Voice Orchestration Runtime errors."""

    pass


class VoiceSessionException(VoiceRuntimeException):
    """Raised when voice session creation, retrieval, or transition fails."""

    pass


class SpeechRoutingException(VoiceRuntimeException):
    """Raised when routing speech input/output between STT, assistant, and TTS fails."""

    pass


class WakeWordException(VoiceRuntimeException):
    """Raised when wake word state management or configuration fails."""

    pass


class VoiceStreamingException(VoiceRuntimeException):
    """Raised when audio or text streaming orchestration encounters an error."""

    pass


class VoiceValidationException(VoiceRuntimeException):
    """Raised when invalid parameters or models are passed to voice components."""

    pass
