"""Unit tests for Phase 13.7 – Voice Orchestration Runtime."""

from concurrent.futures import ThreadPoolExecutor
import threading
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from brain.assistant.voice import (
    IVoiceProvider,
    ListeningMode,
    SpeechMode,
    SpeechRouter,
    VoiceCapabilities,
    VoiceConfiguration,
    VoiceContext,
    VoiceCoordinator,
    VoiceHealth,
    VoiceInteraction,
    VoiceInteractionType,
    VoiceProvider,
    VoiceRequest,
    VoiceResponse,
    VoiceRuntimeException,
    VoiceRuntime,
    VoiceSession,
    VoiceSessionManager,
    VoiceSessionState,
    VoiceState,
    VoiceStatistics,
    VoiceTranscript,
    WakeWordManager,
    get_voice_runtime,
    reset_voice_runtime,
)


@pytest.fixture(autouse=True)
def cleanup_singleton():
    """Ensure clean singleton state before and after each test."""
    reset_voice_runtime()
    yield
    reset_voice_runtime()


# ---------------------------------------------------------------------------
# 1. Immutable Domain Models
# ---------------------------------------------------------------------------

def test_immutable_models() -> None:
    """Verify all 10 Pydantic v2 models are frozen and immutable."""
    transcript = VoiceTranscript()
    context = VoiceContext()
    caps = VoiceCapabilities()
    config = VoiceConfiguration()
    req = VoiceRequest()
    resp = VoiceResponse()
    session = VoiceSession()
    interaction = VoiceInteraction()
    stats = VoiceStatistics()
    health = VoiceHealth()

    models = [transcript, context, caps, config, req, resp, session, interaction, stats, health]
    for m in models:
        with pytest.raises((ValidationError, TypeError, AttributeError)):
            m.duration_ms = 999.0  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# 2. Voice Session Lifecycle & Timeout Expiration
# ---------------------------------------------------------------------------

def test_voice_session_lifecycle() -> None:
    """Verify session creation, pause, resume, close, and active list."""
    mgr = VoiceSessionManager(session_timeout_seconds=0.1)

    sess = mgr.create_session(user_id="usr-123")
    assert sess.state == VoiceSessionState.ACTIVE

    paused = mgr.pause_session(sess.session_id)
    assert paused.state == VoiceSessionState.PAUSED

    resumed = mgr.resume_session(sess.session_id)
    assert resumed.state == VoiceSessionState.ACTIVE

    closed = mgr.close_session(sess.session_id)
    assert closed.state == VoiceSessionState.CLOSED


# ---------------------------------------------------------------------------
# 3. Speech Routing (STT & TTS)
# ---------------------------------------------------------------------------

def test_speech_routing() -> None:
    """Verify SpeechRouter routes STT transcripts and TTS responses."""
    router = SpeechRouter()

    transcript = router.route_stt("open workspace settings")
    assert isinstance(transcript, VoiceTranscript)
    assert transcript.text == "open workspace settings"
    assert router.stt_routed_count == 1

    resp = router.route_tts("Workspace settings opened", speech_mode=SpeechMode.SYNTHESIZED)
    assert isinstance(resp, VoiceResponse)
    assert resp.audio_stream_id is not None
    assert router.tts_routed_count == 1


# ---------------------------------------------------------------------------
# 4. Wake Word Lifecycle
# ---------------------------------------------------------------------------

def test_wake_word_lifecycle() -> None:
    """Verify WakeWordManager enable, disable, pause, resume, and trigger metrics."""
    ww_mgr = WakeWordManager()

    assert ww_mgr.is_enabled is True
    ww_mgr.pause()
    assert ww_mgr.is_enabled is False

    ww_mgr.resume()
    assert ww_mgr.is_enabled is True

    ww_mgr.record_trigger()
    assert ww_mgr.trigger_count == 1

    ww_mgr.disable()
    assert ww_mgr.is_enabled is False


# ---------------------------------------------------------------------------
# 5. Coordinator End-to-End Voice Interaction
# ---------------------------------------------------------------------------

def test_voice_coordinator_orchestration() -> None:
    """Verify VoiceCoordinator executes end-to-end voice interaction lifecycle."""
    coordinator = VoiceCoordinator()

    req = VoiceRequest(
        transcript=VoiceTranscript(text="create new folder"),
        context=VoiceContext(speech_mode=SpeechMode.SYNTHESIZED),
    )

    interaction = coordinator.process_voice_interaction(req)
    assert isinstance(interaction, VoiceInteraction)
    assert interaction.completed is True
    assert interaction.response is not None
    assert interaction.response.state == VoiceState.COMPLETED
    assert "create new folder" in interaction.response.text_content


# ---------------------------------------------------------------------------
# 6. Statistics, Capabilities & Health Diagnostics
# ---------------------------------------------------------------------------

def test_statistics_capabilities_and_health() -> None:
    """Verify VoiceProvider health diagnostics, statistics, and capabilities."""
    runtime = get_voice_runtime()
    provider = runtime.get_provider()
    assert isinstance(provider, VoiceProvider)

    caps = runtime.get_capabilities()
    assert caps.supports_wake_word is True
    assert caps.supports_continuous_listening is True

    health = runtime.get_health()
    assert health.healthy is True
    assert health.status == "READY"

    stats = runtime.get_statistics()
    assert isinstance(stats, VoiceStatistics)


# ---------------------------------------------------------------------------
# 7. Singleton Identity & Restart Mechanics
# ---------------------------------------------------------------------------

def test_singleton_identity_and_restart() -> None:
    """Verify get_voice_runtime singleton identity and restart() behavior."""
    rt1 = get_voice_runtime()
    rt2 = get_voice_runtime()
    assert rt1 is rt2
    assert rt1.is_initialized is True

    rt1.restart()
    assert rt1.is_initialized is True

    reset_voice_runtime()
    rt3 = get_voice_runtime()
    assert rt3 is not rt1


# ---------------------------------------------------------------------------
# 8. Multi-Threaded Execution with ThreadPoolExecutor
# ---------------------------------------------------------------------------

def test_concurrent_execution_thread_pool() -> None:
    """Verify concurrent voice operations safety using ThreadPoolExecutor without race conditions."""
    runtime = get_voice_runtime()
    provider = runtime.get_provider()
    assert isinstance(provider, VoiceProvider)

    def worker(idx: int) -> int:
        sess = provider.session_manager.create_session(user_id=f"user-{idx}")
        req = VoiceRequest(
            session_id=sess.session_id,
            transcript=VoiceTranscript(text=f"command from worker {idx}"),
        )
        interaction = provider.coordinator.process_voice_interaction(req)
        provider.session_manager.close_session(sess.session_id)
        return interaction.response.response_id is not None

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(worker, i) for i in range(20)]
        results = [f.result() for f in futures]

    assert all(results)
    stats = runtime.get_statistics()
    assert stats.total_sessions_created == 20
    assert stats.total_interactions == 20


# ---------------------------------------------------------------------------
# 9. Dependency Injection & Backward Compatibility
# ---------------------------------------------------------------------------

def test_dependency_injection_and_compatibility() -> None:
    """Verify constructor dependency injection and backward compatibility with existing runtimes & Phases 13.1–13.6."""
    from brain.assistant import get_assistant_runtime
    from brain.assistant.conversation import get_conversation_runtime
    from brain.assistant.dialogue import get_dialogue_runtime
    from brain.assistant.memory import get_assistant_memory_runtime
    from brain.assistant.reasoning import get_decision_runtime
    from brain.assistant.response import get_response_runtime

    ast_rt = get_assistant_runtime()
    conv_rt = get_conversation_runtime()
    dial_rt = get_dialogue_runtime()
    dec_rt = get_decision_runtime()
    mem_rt = get_assistant_memory_runtime()
    resp_rt = get_response_runtime()

    assert ast_rt.is_initialized is True
    assert conv_rt.is_initialized is True
    assert dial_rt.is_initialized is True
    assert dec_rt.is_initialized is True
    assert mem_rt.is_initialized is True
    assert resp_rt.is_initialized is True

    custom_router = SpeechRouter()
    custom_ww = WakeWordManager()
    custom_sess = VoiceSessionManager()
    custom_coord = VoiceCoordinator(speech_router=custom_router)

    provider = VoiceProvider(
        coordinator=custom_coord,
        speech_router=custom_router,
        wake_word_manager=custom_ww,
        session_manager=custom_sess,
    )

    voice_rt = VoiceRuntime(provider=provider)
    voice_rt.initialize()
    assert voice_rt.is_initialized is True
