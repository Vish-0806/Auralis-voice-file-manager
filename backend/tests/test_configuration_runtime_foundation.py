"""Comprehensive unit tests for Phase 14.3.1 Configuration Runtime Foundation."""

import concurrent.futures
from typing import Tuple
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from backend.application.config.configuration_provider import ConfigurationProvider
from backend.application.config.configuration_runtime import ConfigurationRuntime
from backend.application.config.exceptions import (
    ConfigurationException,
    ConfigurationInitializationError,
    ConfigurationProfileError,
    ConfigurationProviderError,
    ConfigurationSourceError,
    ConfigurationValidationError,
)
from backend.application.config.interfaces import (
    IConfigurationDiagnostics,
    IConfigurationManager,
    IConfigurationProvider,
    IConfigurationRuntime,
    IConfigurationValidator,
)
from backend.application.config.models import (
    ConfigurationCapabilities,
    ConfigurationContext,
    ConfigurationDiagnostics,
    ConfigurationHealth,
    ConfigurationProfile,
    ConfigurationProfileType,
    ConfigurationRuntimeState,
    ConfigurationSource,
    ConfigurationSourceType,
    ConfigurationState,
    ConfigurationStatistics,
)
from backend.application.config.runtime import (
    get_configuration_provider,
    get_configuration_runtime,
    reset_configuration_provider,
    reset_configuration_runtime,
    set_configuration_provider,
    set_configuration_runtime,
)


# ============================================================================
# 1. Models & Enum Tests
# ============================================================================


def test_configuration_runtime_state_enum():
    """Verify ConfigurationRuntimeState enum values."""
    assert ConfigurationRuntimeState.UNINITIALIZED.value == "UNINITIALIZED"
    assert ConfigurationRuntimeState.INITIALIZING.value == "INITIALIZING"
    assert ConfigurationRuntimeState.READY.value == "READY"
    assert ConfigurationRuntimeState.STOPPING.value == "STOPPING"
    assert ConfigurationRuntimeState.STOPPED.value == "STOPPED"


def test_configuration_source_type_enum():
    """Verify ConfigurationSourceType enum values."""
    assert ConfigurationSourceType.ENVIRONMENT.value == "ENVIRONMENT"
    assert ConfigurationSourceType.DOTENV.value == "DOTENV"
    assert ConfigurationSourceType.JSON.value == "JSON"
    assert ConfigurationSourceType.YAML.value == "YAML"
    assert ConfigurationSourceType.MEMORY.value == "MEMORY"
    assert ConfigurationSourceType.REMOTE.value == "REMOTE"


def test_configuration_profile_type_enum():
    """Verify ConfigurationProfileType enum values."""
    assert ConfigurationProfileType.DEVELOPMENT.value == "DEVELOPMENT"
    assert ConfigurationProfileType.TESTING.value == "TESTING"
    assert ConfigurationProfileType.STAGING.value == "STAGING"
    assert ConfigurationProfileType.PRODUCTION.value == "PRODUCTION"


def test_configuration_models_immutability():
    """Verify Pydantic v2 model immutability with ConfigDict(frozen=True)."""
    state = ConfigurationState(state=ConfigurationRuntimeState.READY)
    assert state.state == ConfigurationRuntimeState.READY

    with pytest.raises(ValidationError):
        state.state = ConfigurationRuntimeState.STOPPED  # type: ignore[misc]


def test_configuration_capabilities_defaults():
    """Verify ConfigurationCapabilities default flags."""
    caps = ConfigurationCapabilities()
    assert caps.supports_dotenv is True
    assert caps.supports_json is True
    assert caps.supports_yaml is True
    assert caps.supports_environment_override is True
    assert caps.supports_hot_reload is True
    assert caps.supports_secret_masking is True


def test_configuration_health_and_statistics_models():
    """Verify ConfigurationHealth and ConfigurationStatistics model attributes."""
    health = ConfigurationHealth(is_healthy=True, state=ConfigurationRuntimeState.READY)
    assert health.is_healthy is True
    assert health.state == ConfigurationRuntimeState.READY

    stats = ConfigurationStatistics(total_properties_loaded=10, reload_count=2)
    assert stats.total_properties_loaded == 10
    assert stats.reload_count == 2


def test_configuration_context_and_profile_models():
    """Verify ConfigurationContext and ConfigurationProfile models."""
    context = ConfigurationContext(app_name="AuralisTest", environment=ConfigurationProfileType.TESTING)
    assert context.app_name == "AuralisTest"
    assert context.environment == ConfigurationProfileType.TESTING

    profile = ConfigurationProfile(profile_type=ConfigurationProfileType.PRODUCTION, profile_name="prod")
    assert profile.profile_type == ConfigurationProfileType.PRODUCTION
    assert profile.profile_name == "prod"


def test_configuration_source_model():
    """Verify ConfigurationSource model."""
    source = ConfigurationSource(source_type=ConfigurationSourceType.JSON, source_name="app_config")
    assert source.source_type == ConfigurationSourceType.JSON
    assert source.source_name == "app_config"


def test_configuration_diagnostics_model():
    """Verify ConfigurationDiagnostics model initialization."""
    diag = ConfigurationDiagnostics(
        state=ConfigurationRuntimeState.READY,
        active_profile_name="development",
        active_sources_count=2,
    )
    assert diag.state == ConfigurationRuntimeState.READY
    assert diag.active_profile_name == "development"
    assert diag.active_sources_count == 2


# ============================================================================
# 2. Exception Hierarchy Tests
# ============================================================================


def test_configuration_exception_hierarchy():
    """Verify ConfigurationException subclass hierarchy."""
    assert issubclass(ConfigurationInitializationError, ConfigurationException)
    assert issubclass(ConfigurationValidationError, ConfigurationException)
    assert issubclass(ConfigurationProviderError, ConfigurationException)
    assert issubclass(ConfigurationProfileError, ConfigurationException)
    assert issubclass(ConfigurationSourceError, ConfigurationException)


# ============================================================================
# 3. ABC Interfaces Tests
# ============================================================================


def test_configuration_interfaces_instantiation_raises():
    """Verify direct instantiation of ABC interfaces raises TypeError."""
    with pytest.raises(TypeError):
        IConfigurationDiagnostics()  # type: ignore[abstract]
    with pytest.raises(TypeError):
        IConfigurationValidator()  # type: ignore[abstract]
    with pytest.raises(TypeError):
        IConfigurationManager()  # type: ignore[abstract]
    with pytest.raises(TypeError):
        IConfigurationProvider()  # type: ignore[abstract]
    with pytest.raises(TypeError):
        IConfigurationRuntime()  # type: ignore[abstract]


# ============================================================================
# 4. ConfigurationProvider Tests
# ============================================================================


def test_configuration_provider_initialization_and_shutdown():
    """Verify ConfigurationProvider lifecycle state transitions."""
    provider = ConfigurationProvider()
    assert provider.health().state == ConfigurationRuntimeState.UNINITIALIZED

    state_ready = provider.initialize()
    assert state_ready == ConfigurationRuntimeState.READY
    assert provider.health().is_healthy is True

    state_stopped = provider.shutdown()
    assert state_stopped == ConfigurationRuntimeState.STOPPED


def test_configuration_provider_restart():
    """Verify ConfigurationProvider restart functionality."""
    provider = ConfigurationProvider()
    provider.initialize()
    restart_state = provider.restart()
    assert restart_state == ConfigurationRuntimeState.READY


def test_configuration_provider_health_reporting():
    """Verify ConfigurationProvider health reporting for READY and STOPPED states."""
    provider = ConfigurationProvider()
    assert provider.health().is_healthy is True

    provider.initialize()
    assert provider.health().is_healthy is True

    provider.shutdown()
    assert provider.health().is_healthy is False
    assert provider.health().state == ConfigurationRuntimeState.STOPPED


def test_configuration_provider_statistics():
    """Verify ConfigurationProvider statistics metric snapshot."""
    provider = ConfigurationProvider()
    stats = provider.statistics()
    assert isinstance(stats, ConfigurationStatistics)
    assert "reload_count" in stats.metrics


def test_configuration_provider_capabilities():
    """Verify ConfigurationProvider capabilities declarations."""
    provider = ConfigurationProvider()
    caps = provider.capabilities()
    assert isinstance(caps, ConfigurationCapabilities)
    assert caps.supports_dotenv is True


def test_configuration_provider_diagnostics():
    """Verify ConfigurationProvider diagnostics model generation."""
    provider = ConfigurationProvider()
    diag = provider.diagnostics()
    assert isinstance(diag, ConfigurationDiagnostics)
    assert diag.active_profile_name == "development"


def test_configuration_provider_get_context():
    """Verify ConfigurationProvider get_context snapshot."""
    context = ConfigurationContext(app_name="CustomApp", environment=ConfigurationProfileType.STAGING)
    provider = ConfigurationProvider(config_context=context)

    ctx = provider.get_context()
    assert ctx.app_name == "CustomApp"
    assert ctx.environment == ConfigurationProfileType.STAGING


# ============================================================================
# 5. ConfigurationRuntime Lifecycle & Delegation Tests
# ============================================================================


def test_configuration_runtime_lifecycle():
    """Verify ConfigurationRuntime lifecycle transitions."""
    runtime = ConfigurationRuntime()
    assert runtime.health().state == ConfigurationRuntimeState.UNINITIALIZED

    ready_state = runtime.initialize()
    assert ready_state == ConfigurationRuntimeState.READY
    assert runtime.health().is_healthy is True

    restart_state = runtime.restart()
    assert restart_state == ConfigurationRuntimeState.READY

    stopped_state = runtime.shutdown()
    assert stopped_state == ConfigurationRuntimeState.STOPPED


def test_configuration_runtime_delegation():
    """Verify ConfigurationRuntime delegation of health, statistics, capabilities, diagnostics, context."""
    provider = ConfigurationProvider()
    runtime = ConfigurationRuntime(provider=provider)

    assert runtime.health().is_healthy is True
    assert isinstance(runtime.statistics(), ConfigurationStatistics)
    assert isinstance(runtime.capabilities(), ConfigurationCapabilities)
    assert isinstance(runtime.diagnostics(), ConfigurationDiagnostics)
    assert isinstance(runtime.context(), ConfigurationContext)


def test_constructor_dependency_injection_provider():
    """Verify ConfigurationRuntime constructor accepts custom provider."""
    custom_context = ConfigurationContext(app_name="InjectedApp")
    custom_provider = ConfigurationProvider(config_context=custom_context)
    runtime = ConfigurationRuntime(provider=custom_provider)

    assert runtime.context().app_name == "InjectedApp"
    assert runtime.provider is custom_provider


# ============================================================================
# 6. Runtime Lazy Singleton Accessors Tests
# ============================================================================


def test_configuration_runtime_lazy_singletons():
    """Verify get_configuration_runtime, set_configuration_runtime, reset_configuration_runtime."""
    reset_configuration_runtime()
    reset_configuration_provider()

    runtime = get_configuration_runtime()
    assert isinstance(runtime, IConfigurationRuntime)

    custom_runtime = ConfigurationRuntime()
    set_configuration_runtime(custom_runtime)
    assert get_configuration_runtime() is custom_runtime

    reset_configuration_runtime()
    reset_configuration_provider()


def test_configuration_provider_lazy_singletons():
    """Verify get_configuration_provider, set_configuration_provider, reset_configuration_provider."""
    reset_configuration_runtime()
    reset_configuration_provider()

    provider = get_configuration_provider()
    assert isinstance(provider, IConfigurationProvider)

    custom_provider = ConfigurationProvider()
    set_configuration_provider(custom_provider)
    assert get_configuration_provider() is custom_provider

    reset_configuration_runtime()
    reset_configuration_provider()


# ============================================================================
# 7. Concurrent Multithreaded Tests
# ============================================================================


def test_concurrent_configuration_runtime_init_shutdown():
    """Verify thread-safe concurrent initialize and shutdown on ConfigurationRuntime."""
    runtime = ConfigurationRuntime()

    def do_init_shutdown():
        runtime.initialize()
        return runtime.shutdown()

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(do_init_shutdown) for _ in range(10)]
        results = [f.result() for f in futures]

    assert all(r == ConfigurationRuntimeState.STOPPED for r in results)


def test_concurrent_configuration_provider_restart():
    """Verify thread-safe concurrent restart calls on ConfigurationProvider."""
    provider = ConfigurationProvider()

    def do_restart():
        return provider.restart()

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(do_restart) for _ in range(10)]
        results = [f.result() for f in futures]

    assert all(r == ConfigurationRuntimeState.READY for r in results)
