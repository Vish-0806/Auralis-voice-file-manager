"""Tests for Phase 14.1 Application Bootstrap Runtime Architecture."""

import pytest
from pydantic import ValidationError

from backend.application.application_provider import ApplicationProvider
from backend.application.application_runtime import ApplicationRuntime
from backend.application.bootstrap_manager import BootstrapManager
from backend.application.exceptions import (
    ApplicationBootstrapError,
    ApplicationException,
    ApplicationShutdownError,
    InitializationError,
    RuntimeRegistrationError,
    StartupValidationError,
)
from backend.application.initialization_manager import InitializationManager
from backend.application.interfaces import (
    IApplicationProvider,
    IApplicationRuntime,
    IBootstrapManager,
    IInitializationManager,
    IRuntimeRegistry,
    IStartupValidator,
)
from backend.application.models import (
    ApplicationCapabilities,
    ApplicationConfiguration,
    ApplicationContext,
    ApplicationDiagnostics,
    ApplicationHealth,
    ApplicationLifecycleState,
    ApplicationState,
    ApplicationStatistics,
    RuntimeRegistration,
)
from backend.application.runtime import (
    get_application_provider,
    get_application_runtime,
    reset_application_provider,
    reset_application_runtime,
    set_application_provider,
    set_application_runtime,
)
from backend.application.runtime_registry import RuntimeRegistry
from backend.application.startup_validator import StartupValidator


# ============================================================================
# 1. Models Tests
# ============================================================================


def test_application_lifecycle_state_enum():
    """Verify ApplicationLifecycleState enum members."""
    assert ApplicationLifecycleState.UNINITIALIZED.value == "UNINITIALIZED"
    assert ApplicationLifecycleState.RUNNING.value == "RUNNING"
    assert ApplicationLifecycleState.SHUTDOWN.value == "SHUTDOWN"


def test_application_state_model_immutability():
    """Verify ApplicationState defaults and immutability."""
    state = ApplicationState()
    assert state.status == ApplicationLifecycleState.UNINITIALIZED
    assert state.is_active is False
    assert state.is_healthy is True

    with pytest.raises(ValidationError):
        # Pydantic v2 frozen model mutation raises ValidationError
        state.is_active = True  # type: ignore[misc]


def test_application_configuration_model():
    """Verify ApplicationConfiguration model attributes and immutability."""
    config = ApplicationConfiguration(app_name="TestApp", debug=True)
    assert config.app_name == "TestApp"
    assert config.debug is True
    assert config.environment == "production"

    with pytest.raises(ValidationError):
        config.debug = False  # type: ignore[misc]


def test_application_capabilities_model():
    """Verify ApplicationCapabilities defaults."""
    caps = ApplicationCapabilities()
    assert caps.voice_enabled is True
    assert caps.ai_reasoning_enabled is True
    assert caps.planning_enabled is True


def test_application_health_model():
    """Verify ApplicationHealth attributes."""
    health = ApplicationHealth(is_healthy=True, issues=("issue1",))
    assert health.is_healthy is True
    assert health.issues == ("issue1",)


def test_application_statistics_model():
    """Verify ApplicationStatistics attributes."""
    stats = ApplicationStatistics(total_requests=10, successful_requests=8)
    assert stats.total_requests == 10
    assert stats.successful_requests == 8


def test_application_context_model():
    """Verify ApplicationContext attributes."""
    ctx = ApplicationContext(app_id="app-123", working_directory="/tmp")
    assert ctx.app_id == "app-123"
    assert ctx.working_directory == "/tmp"


def test_runtime_registration_model():
    """Verify RuntimeRegistration attributes."""
    reg = RuntimeRegistration(name="voice_engine", version="2.0.0")
    assert reg.name == "voice_engine"
    assert reg.version == "2.0.0"
    assert reg.is_active is True


def test_application_diagnostics_model():
    """Verify ApplicationDiagnostics attributes."""
    diag = ApplicationDiagnostics(memory_usage_mb=128.5, cpu_usage_percent=12.3)
    assert diag.memory_usage_mb == 128.5
    assert diag.cpu_usage_percent == 12.3


# ============================================================================
# 2. Exception Hierarchy Tests
# ============================================================================


def test_exception_hierarchy():
    """Verify exception hierarchy subclassing."""
    assert issubclass(ApplicationBootstrapError, ApplicationException)
    assert issubclass(RuntimeRegistrationError, ApplicationException)
    assert issubclass(InitializationError, ApplicationException)
    assert issubclass(StartupValidationError, ApplicationException)
    assert issubclass(ApplicationShutdownError, ApplicationException)


def test_exception_raising():
    """Verify raising custom exceptions."""
    with pytest.raises(ApplicationBootstrapError):
        raise ApplicationBootstrapError("Bootstrap failure")


# ============================================================================
# 3. Interfaces Verification Tests
# ============================================================================


def test_interface_abc_instantiation_raises():
    """Verify ABC interfaces cannot be instantiated directly."""
    with pytest.raises(TypeError):
        IApplicationRuntime()  # type: ignore[abstract]
    with pytest.raises(TypeError):
        IApplicationProvider()  # type: ignore[abstract]
    with pytest.raises(TypeError):
        IBootstrapManager()  # type: ignore[abstract]
    with pytest.raises(TypeError):
        IRuntimeRegistry()  # type: ignore[abstract]
    with pytest.raises(TypeError):
        IInitializationManager()  # type: ignore[abstract]
    with pytest.raises(TypeError):
        IStartupValidator()  # type: ignore[abstract]


# ============================================================================
# 4. Component Skeleton Tests (NotImplementedError enforcement)
# ============================================================================


def test_bootstrap_manager_skeleton():
    """Verify BootstrapManager skeleton methods raise NotImplementedError."""
    mgr = BootstrapManager()
    assert isinstance(mgr, IBootstrapManager)
    config = ApplicationConfiguration()

    with pytest.raises(NotImplementedError):
        mgr.bootstrap(config)
    with pytest.raises(NotImplementedError):
        mgr.teardown()
    with pytest.raises(NotImplementedError):
        mgr.is_bootstrapped()
    with pytest.raises(NotImplementedError):
        mgr.get_bootstrap_state()


def test_runtime_registry_skeleton():
    """Verify RuntimeRegistry skeleton methods raise NotImplementedError."""
    reg = RuntimeRegistry()
    assert isinstance(reg, IRuntimeRegistry)
    record = RuntimeRegistration(name="test")

    with pytest.raises(NotImplementedError):
        reg.register(record)
    with pytest.raises(NotImplementedError):
        reg.unregister("test")
    with pytest.raises(NotImplementedError):
        reg.get_registration("test")
    with pytest.raises(NotImplementedError):
        reg.list_registrations()
    with pytest.raises(NotImplementedError):
        reg.is_registered("test")
    with pytest.raises(NotImplementedError):
        reg.clear()


def test_initialization_manager_skeleton():
    """Verify InitializationManager skeleton methods raise NotImplementedError."""
    mgr = InitializationManager()
    assert isinstance(mgr, IInitializationManager)
    ctx = ApplicationContext()

    with pytest.raises(NotImplementedError):
        mgr.initialize_all(ctx)
    with pytest.raises(NotImplementedError):
        mgr.is_initialized()
    with pytest.raises(NotImplementedError):
        mgr.get_initialized_components()


def test_startup_validator_skeleton():
    """Verify StartupValidator skeleton methods raise NotImplementedError."""
    val = StartupValidator()
    assert isinstance(val, IStartupValidator)
    config = ApplicationConfiguration()

    with pytest.raises(NotImplementedError):
        val.validate_environment()
    with pytest.raises(NotImplementedError):
        val.validate_configuration(config)
    with pytest.raises(NotImplementedError):
        val.validate_runtime_dependencies()
    with pytest.raises(NotImplementedError):
        val.run_all_validations(config)


def test_application_provider_skeleton():
    """Verify ApplicationProvider skeleton methods raise NotImplementedError."""
    provider = ApplicationProvider()
    assert isinstance(provider, IApplicationProvider)

    with pytest.raises(NotImplementedError):
        provider.get_runtime()
    with pytest.raises(NotImplementedError):
        provider.get_configuration()
    with pytest.raises(NotImplementedError):
        provider.get_context()
    with pytest.raises(NotImplementedError):
        provider.get_capabilities()


def test_application_runtime_skeleton():
    """Verify ApplicationRuntime skeleton methods raise NotImplementedError."""
    runtime = ApplicationRuntime()
    assert isinstance(runtime, IApplicationRuntime)

    with pytest.raises(NotImplementedError):
        runtime.initialize()
    with pytest.raises(NotImplementedError):
        runtime.start()
    with pytest.raises(NotImplementedError):
        runtime.stop()
    with pytest.raises(NotImplementedError):
        runtime.shutdown()
    with pytest.raises(NotImplementedError):
        runtime.get_state()
    with pytest.raises(NotImplementedError):
        runtime.get_health()
    with pytest.raises(NotImplementedError):
        runtime.get_statistics()
    with pytest.raises(NotImplementedError):
        runtime.get_diagnostics()
    with pytest.raises(NotImplementedError):
        runtime.get_context()
    with pytest.raises(NotImplementedError):
        runtime.get_capabilities()


# ============================================================================
# 5. Global Runtime Accessor Tests
# ============================================================================


def test_runtime_singleton_accessors():
    """Verify runtime get/set/reset functions."""
    reset_application_runtime()

    with pytest.raises(ApplicationBootstrapError):
        get_application_runtime()

    dummy_runtime = ApplicationRuntime()
    set_application_runtime(dummy_runtime)
    assert get_application_runtime() is dummy_runtime

    reset_application_runtime()
    with pytest.raises(ApplicationBootstrapError):
        get_application_runtime()


def test_provider_singleton_accessors():
    """Verify provider get/set/reset functions."""
    reset_application_provider()

    with pytest.raises(ApplicationBootstrapError):
        get_application_provider()

    dummy_provider = ApplicationProvider()
    set_application_provider(dummy_provider)
    assert get_application_provider() is dummy_provider

    reset_application_provider()
    with pytest.raises(ApplicationBootstrapError):
        get_application_provider()
