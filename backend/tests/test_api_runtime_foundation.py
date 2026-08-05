"""Tests for API Runtime Foundation (Phase 15.1).

Validates immutable models, enums, exception hierarchy, ABC interfaces,
provider lifecycle, runtime lifecycle, health, statistics, capabilities,
diagnostics, lazy singletons, constructor DI, and thread concurrency.
"""

from concurrent.futures import ThreadPoolExecutor
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from backend.application.api import (
    ApiCapabilities,
    ApiConfiguration,
    ApiContext,
    ApiDiagnostics,
    ApiHealth,
    ApiInitializationException,
    ApiProvider,
    ApiProviderException,
    ApiRuntime,
    ApiRuntimeException,
    ApiRuntimeState,
    ApiState,
    ApiStatistics,
    ApiValidationException,
    IApiProvider,
    IApiRuntime,
    get_api_provider,
    get_api_runtime,
    reset_api_provider,
    reset_api_runtime,
    set_api_provider,
    set_api_runtime,
)


@pytest.fixture(autouse=True)
def _reset_singletons():
    """Reset singletons before and after each test."""
    reset_api_runtime()
    reset_api_provider()
    yield
    reset_api_runtime()
    reset_api_provider()


# --- Enum Tests ---

def test_api_runtime_state_enum_values():
    """Verify ApiRuntimeState enum members and string values."""
    assert ApiRuntimeState.UNINITIALIZED.value == "UNINITIALIZED"
    assert ApiRuntimeState.INITIALIZING.value == "INITIALIZING"
    assert ApiRuntimeState.READY.value == "READY"
    assert ApiRuntimeState.STOPPING.value == "STOPPING"
    assert ApiRuntimeState.STOPPED.value == "STOPPED"
    assert len(ApiRuntimeState) == 5


# --- Model Immutability & Defaults Tests ---

def test_api_state_immutability():
    """Verify ApiState model defaults and immutability."""
    state = ApiState()
    assert state.status == ApiRuntimeState.UNINITIALIZED
    assert state.is_active is False
    assert state.is_healthy is True

    with pytest.raises(ValidationError):
        state.is_active = True  # type: ignore[attr-defined]


def test_api_capabilities_immutability():
    """Verify ApiCapabilities model defaults and immutability."""
    caps = ApiCapabilities()
    assert caps.supports_initialize is True
    assert caps.supports_shutdown is True
    assert caps.supports_restart is True
    assert caps.supports_health_checks is True

    with pytest.raises(ValidationError):
        caps.supports_initialize = False  # type: ignore[attr-defined]


def test_api_health_immutability():
    """Verify ApiHealth model defaults and immutability."""
    health = ApiHealth()
    assert health.is_healthy is True
    assert health.state == ApiRuntimeState.UNINITIALIZED

    with pytest.raises(ValidationError):
        health.is_healthy = False  # type: ignore[attr-defined]


def test_api_statistics_immutability():
    """Verify ApiStatistics model defaults and immutability."""
    stats = ApiStatistics()
    assert stats.total_initializations == 0
    assert stats.total_restarts == 0
    assert stats.total_shutdowns == 0

    with pytest.raises(ValidationError):
        stats.total_initializations = 5  # type: ignore[attr-defined]


def test_api_context_immutability():
    """Verify ApiContext model defaults and immutability."""
    ctx = ApiContext(api_id="test_api")
    assert ctx.api_id == "test_api"
    assert ctx.environment == "production"

    with pytest.raises(ValidationError):
        ctx.api_id = "new_api"  # type: ignore[attr-defined]


def test_api_configuration_immutability():
    """Verify ApiConfiguration model defaults and immutability."""
    config = ApiConfiguration(title="Custom API")
    assert config.title == "Custom API"
    assert config.version == "1.0.0"

    with pytest.raises(ValidationError):
        config.title = "Changed API"  # type: ignore[attr-defined]


def test_api_diagnostics_immutability():
    """Verify ApiDiagnostics model defaults and immutability."""
    diag = ApiDiagnostics()
    assert diag.state == ApiRuntimeState.UNINITIALIZED

    with pytest.raises(ValidationError):
        diag.state = ApiRuntimeState.READY  # type: ignore[attr-defined]


# --- Exception Hierarchy Tests ---

def test_exception_hierarchy():
    """Verify exception hierarchy inheritance."""
    assert issubclass(ApiInitializationException, ApiRuntimeException)
    assert issubclass(ApiProviderException, ApiRuntimeException)
    assert issubclass(ApiValidationException, ApiRuntimeException)
    assert issubclass(ApiRuntimeException, Exception)


# --- Interface Abstraction Tests ---

def test_interfaces_cannot_be_instantiated():
    """Verify IApiRuntime and IApiProvider cannot be directly instantiated."""
    with pytest.raises(TypeError):
        IApiRuntime()  # type: ignore[abstract]

    with pytest.raises(TypeError):
        IApiProvider()  # type: ignore[abstract]


# --- Provider Lifecycle & Functionality Tests ---

def test_provider_initialization():
    """Verify ApiProvider initialize transitions to READY."""
    provider = ApiProvider()
    assert provider.health().state == ApiRuntimeState.UNINITIALIZED

    state = provider.initialize()
    assert state.status == ApiRuntimeState.READY
    assert state.is_active is True
    assert state.is_healthy is True
    assert state.initialized_at is not None


def test_provider_double_initialization():
    """Verify ApiProvider handle repeated initialize gracefully."""
    provider = ApiProvider()
    state1 = provider.initialize()
    state2 = provider.initialize()
    assert state1.status == ApiRuntimeState.READY
    assert state2.status == ApiRuntimeState.READY
    assert provider.statistics().total_initializations == 1


def test_provider_shutdown():
    """Verify ApiProvider shutdown transitions to STOPPED."""
    provider = ApiProvider()
    provider.initialize()
    state = provider.shutdown()

    assert state.status == ApiRuntimeState.STOPPED
    assert state.is_active is False
    assert state.stopped_at is not None
    assert provider.statistics().total_shutdowns == 1


def test_provider_double_shutdown():
    """Verify ApiProvider repeated shutdown calls."""
    provider = ApiProvider()
    provider.initialize()
    provider.shutdown()
    state = provider.shutdown()

    assert state.status == ApiRuntimeState.STOPPED
    assert provider.statistics().total_shutdowns == 1


def test_provider_restart():
    """Verify ApiProvider restart cycle."""
    provider = ApiProvider()
    provider.initialize()

    state = provider.restart()
    assert state.status == ApiRuntimeState.READY
    assert state.is_active is True
    stats = provider.statistics()
    assert stats.total_restarts == 1
    assert stats.total_initializations == 2
    assert stats.total_shutdowns == 1


def test_provider_health():
    """Verify ApiProvider health assessment when READY vs STOPPED."""
    provider = ApiProvider()
    health_uninit = provider.health()
    assert health_uninit.is_healthy is True

    provider.initialize()
    health_ready = provider.health()
    assert health_ready.is_healthy is True
    assert health_ready.state == ApiRuntimeState.READY

    provider.shutdown()
    health_stopped = provider.health()
    assert health_stopped.is_healthy is False
    assert len(health_stopped.issues) > 0


def test_provider_statistics():
    """Verify ApiProvider statistics tracking."""
    provider = ApiProvider()
    provider.initialize()

    stats = provider.statistics()
    assert stats.total_initializations == 1
    assert stats.active_time_seconds >= 0.0
    assert "uptime_seconds" in stats.metrics


def test_provider_capabilities():
    """Verify ApiProvider capabilities accessor."""
    caps = ApiCapabilities(custom_capabilities={"custom_feat": True})
    provider = ApiProvider(capabilities=caps)
    retrieved = provider.capabilities()

    assert retrieved.supports_initialize is True
    assert retrieved.custom_capabilities.get("custom_feat") is True


def test_provider_diagnostics():
    """Verify ApiProvider diagnostics snapshot."""
    provider = ApiProvider()
    provider.initialize()
    diag = provider.diagnostics()

    assert diag.state == ApiRuntimeState.READY
    assert diag.thread_count > 0
    assert len(diag.diagnostic_messages) > 0


# --- Runtime Lifecycle & Delegation Tests ---

def test_runtime_initialization_delegation():
    """Verify ApiRuntime initialize delegates to provider."""
    runtime = ApiRuntime()
    state = runtime.initialize()

    assert state.status == ApiRuntimeState.READY
    assert state.is_active is True
    assert runtime.health().state == ApiRuntimeState.READY


def test_runtime_shutdown_delegation():
    """Verify ApiRuntime shutdown delegates to provider."""
    runtime = ApiRuntime()
    runtime.initialize()
    state = runtime.shutdown()

    assert state.status == ApiRuntimeState.STOPPED
    assert state.is_active is False


def test_runtime_restart_delegation():
    """Verify ApiRuntime restart delegates to provider."""
    runtime = ApiRuntime()
    runtime.initialize()
    state = runtime.restart()

    assert state.status == ApiRuntimeState.READY
    assert runtime.statistics().total_restarts == 1


def test_runtime_health_stats_capabilities_diagnostics():
    """Verify ApiRuntime delegation for health, statistics, capabilities, diagnostics."""
    runtime = ApiRuntime()
    runtime.initialize()

    assert runtime.health().is_healthy is True
    assert runtime.statistics().total_initializations == 1
    assert runtime.capabilities().supports_initialize is True
    assert runtime.diagnostics().state == ApiRuntimeState.READY


# --- Dependency Injection Tests ---

def test_constructor_dependency_injection():
    """Verify constructor DI in ApiRuntime and ApiProvider."""
    custom_config = ApiConfiguration(title="Custom Injected API")
    provider = ApiProvider(config=custom_config)
    runtime = ApiRuntime(provider=provider)

    assert runtime.get_provider() is provider
    state = runtime.initialize()
    assert state.metadata.get("title") == "Custom Injected API"


# --- Lazy Singleton Helper Tests ---

def test_lazy_singleton_runtime_helpers():
    """Verify get_api_runtime, set_api_runtime, and reset_api_runtime."""
    r1 = get_api_runtime()
    r2 = get_api_runtime()
    assert r1 is r2
    assert isinstance(r1, ApiRuntime)

    custom_runtime = ApiRuntime()
    set_api_runtime(custom_runtime)
    assert get_api_runtime() is custom_runtime

    reset_api_runtime()
    r3 = get_api_runtime()
    assert r3 is not custom_runtime


def test_lazy_singleton_provider_helpers():
    """Verify get_api_provider, set_api_provider, and reset_api_provider."""
    p1 = get_api_provider()
    p2 = get_api_provider()
    assert p1 is p2
    assert isinstance(p1, ApiProvider)

    custom_provider = ApiProvider()
    set_api_provider(custom_provider)
    assert get_api_provider() is custom_provider

    reset_api_provider()
    p3 = get_api_provider()
    assert p3 is not custom_provider


# --- Concurrency Tests ---

def test_concurrent_provider_operations():
    """Verify thread safety of ApiProvider under concurrent operations."""
    provider = ApiProvider()

    def worker(idx: int):
        if idx % 3 == 0:
            provider.initialize()
        elif idx % 3 == 1:
            provider.health()
        else:
            provider.statistics()

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker, i) for i in range(30)]
        for f in futures:
            f.result()

    assert provider.health().state == ApiRuntimeState.READY


def test_concurrent_runtime_operations():
    """Verify thread safety of ApiRuntime under concurrent operations."""
    runtime = ApiRuntime()

    def worker(idx: int):
        if idx % 4 == 0:
            runtime.initialize()
        elif idx % 4 == 1:
            runtime.health()
        elif idx % 4 == 2:
            runtime.diagnostics()
        else:
            runtime.statistics()

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker, i) for i in range(40)]
        for f in futures:
            f.result()

    assert runtime.health().state == ApiRuntimeState.READY
