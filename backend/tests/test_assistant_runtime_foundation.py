"""Unit tests for Phase 13.1 – Assistant Runtime Foundation."""

import threading
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from brain.assistant import (
    AssistantCapabilities,
    AssistantConfiguration,
    AssistantContext,
    AssistantException,
    AssistantHealth,
    AssistantInitializationError,
    AssistantProvider,
    AssistantRuntime,
    AssistantSession,
    AssistantSessionError,
    AssistantState,
    AssistantStateEnum,
    AssistantStatistics,
    AssistantStatus,
    IAssistantHealthMonitor,
    IAssistantProvider,
    IAssistantRuntime,
    IAssistantSessionManager,
    IAssistantStatisticsCollector,
    get_assistant_runtime,
    reset_assistant_runtime,
)


@pytest.fixture(autouse=True)
def cleanup_singleton():
    """Ensure clean singleton state before and after each test."""
    reset_assistant_runtime()
    yield
    reset_assistant_runtime()


# ---------------------------------------------------------------------------
# 1. Immutable Domain Models
# ---------------------------------------------------------------------------

def test_immutable_models() -> None:
    """Verify that all 8 Pydantic v2 models are frozen and immutable."""
    state = AssistantState()
    status = AssistantStatus()
    capabilities = AssistantCapabilities()
    stats = AssistantStatistics()
    health = AssistantHealth()
    context = AssistantContext()
    session = AssistantSession()
    config = AssistantConfiguration()

    models = [state, status, capabilities, stats, health, context, session, config]
    for model in models:
        with pytest.raises((ValidationError, TypeError, AttributeError)):
            model.healthy = False  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# 2. Exception Hierarchy
# ---------------------------------------------------------------------------

def test_exception_hierarchy() -> None:
    """Verify exception inheritance tree."""
    from brain.assistant.exceptions import (
        AssistantConfigurationError,
        AssistantInitializationError,
        AssistantRuntimeError,
        AssistantSessionError,
    )

    init_err = AssistantInitializationError("init failed")
    rt_err = AssistantRuntimeError("runtime failed")
    cfg_err = AssistantConfigurationError("config failed")
    sess_err = AssistantSessionError("session failed")

    for err in [init_err, rt_err, cfg_err, sess_err]:
        assert isinstance(err, AssistantException)
        assert isinstance(err, Exception)


# ---------------------------------------------------------------------------
# 3. Runtime Lifecycle
# ---------------------------------------------------------------------------

def test_runtime_lifecycle() -> None:
    """Verify initialize, shutdown, restart, and state transitions."""
    runtime = AssistantRuntime()
    assert not runtime.is_initialized
    assert runtime.state.state == AssistantStateEnum.UNINITIALIZED

    runtime.initialize()
    assert runtime.is_initialized
    assert runtime.state.state == AssistantStateEnum.READY

    status = runtime.get_status()
    assert status.healthy
    assert status.provider_count == 1

    runtime.shutdown()
    assert not runtime.is_initialized
    assert runtime.state.state == AssistantStateEnum.STOPPED

    runtime.restart()
    assert runtime.is_initialized
    assert runtime.state.state == AssistantStateEnum.READY


# ---------------------------------------------------------------------------
# 4. Provider Initialization
# ---------------------------------------------------------------------------

def test_provider_initialization() -> None:
    """Verify AssistantProvider lifecycle and capability inspection."""
    provider = AssistantProvider()
    assert not provider.is_initialized

    provider.initialize()
    assert provider.is_initialized

    capabilities = provider.get_capabilities()
    assert isinstance(capabilities, AssistantCapabilities)
    assert capabilities.brain_integration
    assert capabilities.ai_integration

    provider.shutdown()
    assert not provider.is_initialized


# ---------------------------------------------------------------------------
# 5. Singleton Identity
# ---------------------------------------------------------------------------

def test_singleton_identity() -> None:
    """Verify singleton accessor identity and reset mechanics."""
    rt1 = get_assistant_runtime()
    rt2 = get_assistant_runtime()

    assert rt1 is rt2
    assert rt1.is_initialized

    reset_assistant_runtime()
    rt3 = get_assistant_runtime()

    assert rt3 is not rt1
    assert rt3.is_initialized


# ---------------------------------------------------------------------------
# 6. Thread Safety
# ---------------------------------------------------------------------------

def test_thread_safety() -> None:
    """Verify concurrent thread safety for runtime operations."""
    runtime = get_assistant_runtime()
    provider = runtime.get_provider()
    assert isinstance(provider, AssistantProvider)

    errors = []

    def worker(idx: int) -> None:
        try:
            for _ in range(20):
                provider.record_request(duration_ms=10.0, success=True)
                provider.create_session()
                _ = runtime.get_status()
                _ = runtime.get_health()
                _ = runtime.get_statistics()
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0
    stats = runtime.get_statistics()
    assert stats.total_requests == 200
    assert stats.successful_requests == 200


# ---------------------------------------------------------------------------
# 7. Health Reporting
# ---------------------------------------------------------------------------

def test_health_reporting() -> None:
    """Verify diagnostic health reporting."""
    runtime = get_assistant_runtime()
    health = runtime.get_health()

    assert isinstance(health, AssistantHealth)
    assert health.healthy
    assert health.status == "READY"
    assert "session_manager" in health.subsystems
    assert health.subsystems["session_manager"] is True


# ---------------------------------------------------------------------------
# 8. Statistics Reporting
# ---------------------------------------------------------------------------

def test_statistics_reporting() -> None:
    """Verify statistics tracking and clear functionality."""
    runtime = get_assistant_runtime()
    provider = runtime.get_provider()
    assert isinstance(provider, AssistantProvider)

    provider.record_request(duration_ms=50.0, success=True)
    provider.record_request(duration_ms=150.0, success=False)

    stats = runtime.get_statistics()
    assert stats.total_requests == 2
    assert stats.successful_requests == 1
    assert stats.failed_requests == 1
    assert stats.average_latency_ms == 100.0

    runtime.clear()
    stats_cleared = runtime.get_statistics()
    assert stats_cleared.total_requests == 0


# ---------------------------------------------------------------------------
# 9. Dependency Injection
# ---------------------------------------------------------------------------

def test_dependency_injection() -> None:
    """Verify constructor dependency injection for custom runtimes and monitors."""

    class MockBrainRuntime:
        def __init__(self):
            self.initialized = False
        def initialize(self):
            self.initialized = True
        def shutdown(self):
            self.initialized = False

    class MockHealthMonitor(IAssistantHealthMonitor):
        def check_health(self) -> AssistantHealth:
            return AssistantHealth(status="CUSTOM_HEALTHY", healthy=True)

    mock_brain = MockBrainRuntime()
    mock_health = MockHealthMonitor()

    provider = AssistantProvider(
        brain_runtime=mock_brain,
        health_monitor=mock_health,
    )
    runtime = AssistantRuntime(provider=provider)
    runtime.initialize()

    assert mock_brain.initialized
    health = runtime.get_health()
    assert health.status == "CUSTOM_HEALTHY"


# ---------------------------------------------------------------------------
# 10. Backward Compatibility
# ---------------------------------------------------------------------------

def test_backward_compatibility() -> None:
    """Verify Phase 9 AssistantRuntime compatibility is undisturbed."""
    from brain.runtime import AssistantRuntime as Phase9AssistantRuntime

    legacy_rt = Phase9AssistantRuntime()
    assert legacy_rt.initialize() is True
    assert legacy_rt.is_initialized is True
    res = legacy_rt.process_request("hello brain")
    assert res.success is True
    assert legacy_rt.shutdown() is True
