"""Unit tests for ConversationRuntimeCoordinator (Phase 9.1.6)."""

from concurrent.futures import ThreadPoolExecutor
import time
# pyrefly: ignore [missing-import]
import pytest

from brain.conversation.context_manager import ConversationContextConfig, ConversationContextManager
from brain.conversation.conversation_session import ConversationSessionConfig, ConversationSessionManager, ConversationTurn
from brain.conversation.recovery import ConversationRecoveryConfig, ConversationRecoveryManager, ConversationRecoveryStatus
from brain.conversation.reference_resolver import ConversationReferenceResolver, ReferenceResolverConfig
from brain.conversation.runtime import (
    ConversationRuntimeCoordinator,
    get_conversation_runtime,
    reset_conversation_runtime,
)
from brain.conversation.summarizer import ConversationSummarizer, ConversationSummaryConfig


@pytest.fixture(autouse=True)
def auto_reset_runtime() -> None:
    """Fixture to ensure runtime singleton is reset before and after every test."""
    reset_conversation_runtime()
    yield
    reset_conversation_runtime()


def test_initialization() -> None:
    """Verifies runtime initialization and status flags."""
    coordinator = ConversationRuntimeCoordinator()
    assert coordinator.is_initialized is False
    assert coordinator.is_shutdown is False

    res = coordinator.initialize()
    assert res is True
    assert coordinator.is_initialized is True
    assert coordinator.is_shutdown is False


def test_singleton_registration() -> None:
    """Verifies get_conversation_runtime returns a global singleton instance."""
    rt1 = get_conversation_runtime()
    rt2 = get_conversation_runtime()

    assert rt1 is rt2
    assert rt1.is_initialized is True


def test_duplicate_initialization() -> None:
    """Verifies initialization is idempotent and duplicate initialization is handled cleanly."""
    coordinator = ConversationRuntimeCoordinator()
    coordinator.initialize()

    res = coordinator.initialize()
    assert res is True
    assert coordinator.is_initialized is True


def test_shutdown() -> None:
    """Verifies runtime shutdown procedure."""
    coordinator = ConversationRuntimeCoordinator()
    coordinator.initialize()

    res = coordinator.shutdown()
    assert res is True
    assert coordinator.is_shutdown is True
    assert coordinator.is_initialized is False


def test_health_checks() -> None:
    """Verifies health check reporting structure and status."""
    coordinator = ConversationRuntimeCoordinator()
    coordinator.initialize()

    health = coordinator.health_check()
    assert health["overall_status"] == "HEALTHY"
    assert len(health["registered_services"]) == 5
    assert health["active_sessions"] == 0
    assert health["active_contexts"] == 0
    assert health["active_summaries"] == 0
    assert health["pending_recoveries"] == 0
    assert health["thread_safety_status"] == "PROTECTED"


def test_runtime_statistics() -> None:
    """Verifies runtime statistics diagnostics generation."""
    coordinator = ConversationRuntimeCoordinator()
    coordinator.initialize()

    stats = coordinator.runtime_statistics()
    assert stats["service_count"] == 5
    assert len(stats["registered_components"]) == 5
    assert "session_statistics" in stats
    assert "context_statistics" in stats
    assert "summary_statistics" in stats
    assert "recovery_statistics" in stats
    assert stats["uptime"] >= 0.0


def test_dependency_injection() -> None:
    """Verifies passing custom manager instances to constructor."""
    custom_session_mgr = ConversationSessionManager()
    coordinator = ConversationRuntimeCoordinator(session_manager=custom_session_mgr)

    assert coordinator.session_manager is custom_session_mgr


def test_service_lookup() -> None:
    """Verifies access to all 5 registered conversation managers."""
    coordinator = ConversationRuntimeCoordinator()

    assert isinstance(coordinator.session_manager, ConversationSessionManager)
    assert isinstance(coordinator.context_manager, ConversationContextManager)
    assert isinstance(coordinator.reference_resolver, ConversationReferenceResolver)
    assert isinstance(coordinator.summarizer, ConversationSummarizer)
    assert isinstance(coordinator.recovery_manager, ConversationRecoveryManager)


def test_startup_integration() -> None:
    """Simulates application startup integration."""
    rt = get_conversation_runtime()
    assert rt.is_initialized is True
    health = rt.health_check()
    assert health["overall_status"] == "HEALTHY"


def test_shutdown_integration() -> None:
    """Simulates application shutdown integration."""
    rt = get_conversation_runtime()
    rt.shutdown()

    health = rt.health_check()
    assert health["overall_status"] == "SHUTDOWN"


def test_diagnostics() -> None:
    """Verifies detailed breakdown in runtime statistics."""
    coordinator = ConversationRuntimeCoordinator()
    coordinator.initialize()

    coordinator.session_manager.create_session(user_id="u1", session_id="s1")
    coordinator.context_manager.create_context("s1")

    stats = coordinator.runtime_statistics()
    assert stats["session_statistics"]["active_sessions"] == 1
    assert stats["context_statistics"]["total_contexts"] == 1


def test_active_sessions() -> None:
    """Verifies active session count tracking in health checks."""
    coordinator = ConversationRuntimeCoordinator()
    coordinator.initialize()

    coordinator.session_manager.create_session("u1", session_id="s1")
    coordinator.session_manager.create_session("u2", session_id="s2")

    health = coordinator.health_check()
    assert health["active_sessions"] == 2


def test_active_contexts() -> None:
    """Verifies active context count tracking in health checks."""
    coordinator = ConversationRuntimeCoordinator()
    coordinator.initialize()

    coordinator.context_manager.create_context("s1")

    health = coordinator.health_check()
    assert health["active_contexts"] == 1


def test_summaries() -> None:
    """Verifies active summary count tracking in health checks."""
    coordinator = ConversationRuntimeCoordinator()
    coordinator.initialize()

    turns = [ConversationTurn(turn_id="t1", role="user", content="Hi")]
    coordinator.summarizer.create_summary("s1", turns)

    health = coordinator.health_check()
    assert health["active_summaries"] == 1


def test_recovery_services() -> None:
    """Verifies pending recovery count tracking in health checks."""
    coordinator = ConversationRuntimeCoordinator()
    coordinator.initialize()

    coordinator.recovery_manager.create_recovery_record("s1")

    health = coordinator.health_check()
    assert health["pending_recoveries"] == 1


def test_thread_safety() -> None:
    """Verifies thread safety during concurrent initialization, health checks, and statistics generation."""
    coordinator = ConversationRuntimeCoordinator()

    def worker(idx: int) -> None:
        coordinator.initialize()
        coordinator.health_check()
        coordinator.runtime_statistics()

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker, i) for i in range(50)]
        for f in futures:
            f.result()

    assert coordinator.is_initialized is True


def test_repeated_shutdown() -> None:
    """Verifies calling shutdown multiple times is safe and returns True."""
    coordinator = ConversationRuntimeCoordinator()
    coordinator.initialize()

    assert coordinator.shutdown() is True
    assert coordinator.shutdown() is True
    assert coordinator.is_shutdown is True


def test_repeated_startup() -> None:
    """Verifies re-initializing runtime after shutdown works cleanly."""
    coordinator = ConversationRuntimeCoordinator()
    coordinator.initialize()
    coordinator.shutdown()

    res = coordinator.initialize()
    assert res is True
    assert coordinator.is_initialized is True
    assert coordinator.is_shutdown is False


def test_configuration() -> None:
    """Verifies custom configuration objects are passed to internal managers."""
    session_cfg = ConversationSessionConfig(maximum_sessions=10)
    context_cfg = ConversationContextConfig(maximum_contexts=10)

    coordinator = ConversationRuntimeCoordinator(
        session_config=session_cfg, context_config=context_cfg
    )

    assert coordinator.session_manager.config.maximum_sessions == 10
    assert coordinator.context_manager.config.maximum_contexts == 10


def test_graceful_failures() -> None:
    """Verifies operations on uninitialized runtime handle status gracefully."""
    coordinator = ConversationRuntimeCoordinator()
    # Uninitialized coordinator health check returns NOT_INITIALIZED
    health = coordinator.health_check()
    assert health["overall_status"] == "NOT_INITIALIZED"


def test_runtime_reset() -> None:
    """Verifies reset_conversation_runtime resets global singleton instance."""
    rt1 = get_conversation_runtime()
    reset_conversation_runtime()
    rt2 = get_conversation_runtime()

    assert rt1 is not rt2


def test_service_availability() -> None:
    """Verifies all 5 conversation services are available and operational."""
    rt = get_conversation_runtime()

    session = rt.session_manager.create_session("u1")
    context = rt.context_manager.create_context(session.session_id)
    cand = rt.reference_resolver.register_entity("e1", display_name="Doc 1")
    summary = rt.summarizer.create_summary(session.session_id, [])
    recovery = rt.recovery_manager.create_recovery_record(session.session_id)

    assert session is not None
    assert context is not None
    assert cand is not None
    assert summary is not None
    assert recovery is not None


def test_lifecycle() -> None:
    """Verifies complete runtime lifecycle: startup -> usage -> health -> shutdown."""
    coordinator = ConversationRuntimeCoordinator()

    # Startup
    coordinator.initialize()
    assert coordinator.is_initialized is True

    # Usage
    s = coordinator.session_manager.create_session("user1")
    coordinator.context_manager.create_context(s.session_id)

    # Health & Stats
    health = coordinator.health_check()
    assert health["overall_status"] == "HEALTHY"
    stats = coordinator.runtime_statistics()
    assert stats["session_statistics"]["active_sessions"] == 1

    # Shutdown
    coordinator.shutdown()
    assert coordinator.is_shutdown is True


def test_backward_compatibility() -> None:
    """Verifies no breaking changes to existing brain conversation package imports."""
    from brain.conversation import (
        ConversationContext,
        ConversationRecoveryRecord,
        ConversationReferenceResolver,
        ConversationSession,
        ConversationSessionStatus,
        ConversationSummarizer,
        ConversationTurn,
        get_conversation_runtime,
    )

    rt = get_conversation_runtime()
    assert rt is not None
