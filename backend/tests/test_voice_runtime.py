"""Unit tests for VoiceRuntimeCoordinator (Phase 9.6)."""

# pyrefly: ignore [missing-import]
import pytest
from brain.voice import (
    VoiceRuntimeCoordinator, VoiceRuntimeStatus,
    VoiceRuntimeHealth, VoiceRuntimeStatistics,
    get_voice_runtime, reset_voice_runtime,
)


@pytest.fixture(autouse=True)
def isolate_runtime() -> None:
    reset_voice_runtime()
    yield
    reset_voice_runtime()


@pytest.fixture
def coordinator() -> VoiceRuntimeCoordinator:
    c = VoiceRuntimeCoordinator()
    c.initialize()
    return c


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------

def test_initialize_sets_ready() -> None:
    c = VoiceRuntimeCoordinator()
    assert c.status == VoiceRuntimeStatus.INITIALIZING
    assert c.initialize() is True
    assert c.status == VoiceRuntimeStatus.READY


def test_shutdown_sets_shutdown(coordinator: VoiceRuntimeCoordinator) -> None:
    assert coordinator.shutdown() is True
    assert coordinator.status == VoiceRuntimeStatus.SHUTDOWN


def test_auto_reinitialize_on_get_orchestrator(coordinator: VoiceRuntimeCoordinator) -> None:
    coordinator.shutdown()
    orc = coordinator.get_orchestrator()
    assert orc is not None
    assert coordinator.status == VoiceRuntimeStatus.READY


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------

def test_start_and_end_session(coordinator: VoiceRuntimeCoordinator) -> None:
    s = coordinator.start_session("s1")
    assert s.session_id == "s1"
    assert "s1" in coordinator.list_sessions()
    
    stats = coordinator.get_statistics()
    assert stats.sessions_started == 1

    coordinator.end_session("s1")
    stats = coordinator.get_statistics()
    assert stats.sessions_ended == 1


# ---------------------------------------------------------------------------
# Health & Statistics
# ---------------------------------------------------------------------------

def test_health_check(coordinator: VoiceRuntimeCoordinator) -> None:
    health = coordinator.health_check()
    assert isinstance(health, VoiceRuntimeHealth)
    assert health.healthy is True
    assert health.status == "READY"
    assert len(health.registered_components) == 5


def test_statistics_recording(coordinator: VoiceRuntimeCoordinator) -> None:
    coordinator.record_command_received()
    coordinator.record_command_completed(pipeline_ms=10.0)
    coordinator.record_confirmation_requested()
    coordinator.record_confirmation_accepted()

    stats = coordinator.get_statistics()
    assert isinstance(stats, VoiceRuntimeStatistics)
    assert stats.commands_received == 1
    assert stats.commands_completed == 1
    assert stats.average_pipeline_ms == 10.0
    assert stats.confirmations_requested == 1
    assert stats.confirmations_accepted == 1


def test_clear_statistics(coordinator: VoiceRuntimeCoordinator) -> None:
    coordinator.record_command_received()
    coordinator.clear()
    stats = coordinator.get_statistics()
    assert stats.commands_received == 0


# ---------------------------------------------------------------------------
# Global Singleton
# ---------------------------------------------------------------------------

def test_get_voice_runtime_singleton() -> None:
    r1 = get_voice_runtime()
    r2 = get_voice_runtime()
    assert r1 is r2
    assert r1.status == VoiceRuntimeStatus.READY


def test_reset_voice_runtime() -> None:
    r1 = get_voice_runtime()
    reset_voice_runtime()
    r2 = get_voice_runtime()
    assert r1 is not r2


# ---------------------------------------------------------------------------
# Thread Safety
# ---------------------------------------------------------------------------

def test_voice_runtime_thread_safety(coordinator: VoiceRuntimeCoordinator) -> None:
    import threading
    healths = []

    def check() -> None:
        healths.append(coordinator.health_check())

    threads = [threading.Thread(target=check) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(healths) == 20
    assert all(h.healthy for h in healths)
