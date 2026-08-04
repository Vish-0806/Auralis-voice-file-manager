"""Comprehensive unit tests for Phase 14.1 Application Bootstrap Runtime Architecture."""

import concurrent.futures
from typing import List
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
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
from backend.application.initialization_manager import (
    DETERMINISTIC_INITIALIZATION_ORDER,
    InitializationManager,
)
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
# 1. Models & Exception Hierarchy Tests
# ============================================================================


def test_application_lifecycle_state_enum():
    """Verify ApplicationLifecycleState enum values."""
    assert ApplicationLifecycleState.UNINITIALIZED.value == "UNINITIALIZED"
    assert ApplicationLifecycleState.BOOTSTRAPPING.value == "BOOTSTRAPPING"
    assert ApplicationLifecycleState.REGISTERING.value == "REGISTERING"
    assert ApplicationLifecycleState.VALIDATING.value == "VALIDATING"
    assert ApplicationLifecycleState.INITIALIZING.value == "INITIALIZING"
    assert ApplicationLifecycleState.READY.value == "READY"
    assert ApplicationLifecycleState.RUNNING.value == "RUNNING"
    assert ApplicationLifecycleState.SHUTDOWN.value == "SHUTDOWN"


def test_application_state_model_immutability():
    """Verify ApplicationState defaults and immutability."""
    state = ApplicationState()
    assert state.status == ApplicationLifecycleState.UNINITIALIZED
    assert state.is_active is False
    assert state.is_healthy is True

    with pytest.raises(ValidationError):
        state.is_active = True  # type: ignore[misc]


def test_application_configuration_model():
    """Verify ApplicationConfiguration model attributes and immutability."""
    config = ApplicationConfiguration(app_name="TestApp", debug=True)
    assert config.app_name == "TestApp"
    assert config.debug is True
    assert config.environment == "production"

    with pytest.raises(ValidationError):
        config.debug = False  # type: ignore[misc]


def test_application_capabilities_model_fields():
    """Verify ApplicationCapabilities defaults and feature flags."""
    caps = ApplicationCapabilities()
    assert caps.voice_enabled is True
    assert caps.ai_reasoning_enabled is True
    assert caps.planning_enabled is True
    assert caps.supports_restart is True
    assert caps.supports_bootstrap is True
    assert caps.supports_runtime_registration is True
    assert caps.supports_health_checks is True
    assert caps.supports_validation is True
    assert caps.supports_shutdown is True


def test_application_health_model():
    """Verify ApplicationHealth model fields."""
    health = ApplicationHealth(is_healthy=True, issues=("issue1",))
    assert health.is_healthy is True
    assert health.issues == ("issue1",)


def test_application_statistics_model():
    """Verify ApplicationStatistics model fields."""
    stats = ApplicationStatistics(total_requests=10, successful_requests=8)
    assert stats.total_requests == 10
    assert stats.successful_requests == 8


def test_exception_hierarchy():
    """Verify exception hierarchy subclassing."""
    assert issubclass(ApplicationBootstrapError, ApplicationException)
    assert issubclass(RuntimeRegistrationError, ApplicationException)
    assert issubclass(InitializationError, ApplicationException)
    assert issubclass(StartupValidationError, ApplicationException)
    assert issubclass(ApplicationShutdownError, ApplicationException)


# ============================================================================
# 2. Runtime Registry Tests
# ============================================================================


def test_runtime_registry_registration_and_lookup():
    """Verify registering, retrieving, and unregistering runtimes in RuntimeRegistry."""
    registry = RuntimeRegistry()
    reg = RuntimeRegistration(name="brain_runtime", version="1.0.0")

    assert registry.register_runtime(reg) is True
    assert registry.contains_runtime("brain_runtime") is True
    assert registry.is_registered("brain_runtime") is True
    assert registry.count() == 1

    retrieved = registry.get_runtime("brain_runtime")
    assert retrieved is not None
    assert retrieved.name == "brain_runtime"

    assert registry.get_registration("brain_runtime") is retrieved
    assert registry.list_registrations() == registry.list_runtimes()

    assert registry.unregister_runtime("brain_runtime") is True
    assert registry.contains_runtime("brain_runtime") is False
    assert registry.count() == 0


def test_runtime_registry_unregister_alias():
    """Verify unregister interface alias."""
    registry = RuntimeRegistry()
    registry.register(RuntimeRegistration(name="test_runtime"))
    assert registry.unregister("test_runtime") is True
    assert registry.unregister("non_existent") is False


def test_runtime_registry_duplicate_detection():
    """Verify duplicate runtime registration raises RuntimeRegistrationError."""
    registry = RuntimeRegistry()
    reg1 = RuntimeRegistration(name="ai_runtime")
    reg2 = RuntimeRegistration(name="ai_runtime", version="2.0.0")

    registry.register_runtime(reg1)
    with pytest.raises(RuntimeRegistrationError):
        registry.register_runtime(reg2)


def test_runtime_registry_order_preservation():
    """Verify RuntimeRegistry preserves insertion order."""
    registry = RuntimeRegistry()
    names = ["brain_runtime", "ai_runtime", "os_runtime"]
    for n in names:
        registry.register_runtime(RuntimeRegistration(name=n))

    runtimes = registry.list_runtimes()
    assert len(runtimes) == 3
    assert [r.name for r in runtimes] == names


def test_runtime_registry_clear_and_stats():
    """Verify clearing registry and retrieving health/statistics."""
    registry = RuntimeRegistry()
    registry.register_runtime(RuntimeRegistration(name="r1", is_active=True))
    registry.register_runtime(RuntimeRegistration(name="r2", is_active=False))

    stats = registry.statistics()
    assert stats.registered_runtimes_count == 2

    health = registry.health()
    assert health.is_healthy is False  # Because r2 is inactive
    assert health.state == ApplicationLifecycleState.DEGRADED

    registry.clear()
    assert registry.count() == 0


def test_runtime_registry_concurrent_registration():
    """Verify thread-safe concurrent registration in RuntimeRegistry."""
    registry = RuntimeRegistry()

    def thread_register(idx: int):
        registry.register_runtime(RuntimeRegistration(name=f"runtime_{idx}"))

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(thread_register, i) for i in range(50)]
        concurrent.futures.wait(futures)

    assert registry.count() == 50


# ============================================================================
# 3. Initialization Manager Tests
# ============================================================================


def test_initialization_manager_deterministic_ordering():
    """Verify InitializationManager initializes components in deterministic order."""
    init_mgr = InitializationManager()
    init_order: List[str] = []

    for name in DETERMINISTIC_INITIALIZATION_ORDER:
        def make_init(n=name):
            def init_fn():
                init_order.append(n)
                return True
            return init_fn
        init_mgr.register_initializer(name, make_init())

    assert init_mgr.initialize_all() is True
    assert init_order == list(DETERMINISTIC_INITIALIZATION_ORDER)
    assert init_mgr.is_initialized() is True
    assert init_mgr.successful_initializations == 1
    assert init_mgr.get_initialized_components() == DETERMINISTIC_INITIALIZATION_ORDER


def test_initialization_manager_reverse_shutdown_ordering():
    """Verify InitializationManager shuts down components in exact reverse order."""
    init_mgr = InitializationManager()
    shutdown_order: List[str] = []

    for name in DETERMINISTIC_INITIALIZATION_ORDER:
        def make_shutdown(n=name):
            def shutdown_fn():
                shutdown_order.append(n)
                return True
            return shutdown_fn
        init_mgr.register_initializer(name, lambda: True, make_shutdown())

    init_mgr.initialize_all()
    assert init_mgr.shutdown_all() is True
    assert shutdown_order == list(reversed(DETERMINISTIC_INITIALIZATION_ORDER))
    assert init_mgr.shutdown_count == 1


def test_initialization_manager_rollback_on_failure():
    """Verify automatic rollback when subsystem initialization fails."""
    init_mgr = InitializationManager()
    rolled_back: List[str] = []

    for idx, name in enumerate(DETERMINISTIC_INITIALIZATION_ORDER):
        if idx == 3:
            def fail_init():
                return False
            init_mgr.register_initializer(name, fail_init)
        else:
            def make_shutdown(n=name):
                def shutdown_fn():
                    rolled_back.append(n)
                    return True
                return shutdown_fn
            init_mgr.register_initializer(name, lambda: True, make_shutdown())

    with pytest.raises(InitializationError):
        init_mgr.initialize_all()

    expected_rolled_back = list(reversed(DETERMINISTIC_INITIALIZATION_ORDER[:3]))
    assert rolled_back == expected_rolled_back
    assert init_mgr.rollback_count == 1
    assert init_mgr.failed_initializations == 1
    assert len(init_mgr.get_initialized_components()) == 0


def test_initialization_manager_restart_all():
    """Verify restart_all triggers shutdown followed by re-initialization."""
    init_mgr = InitializationManager()
    events: List[str] = []

    for name in DETERMINISTIC_INITIALIZATION_ORDER:
        def make_handlers(n=name):
            return (
                lambda: events.append(f"init_{n}") or True,
                lambda: events.append(f"shutdown_{n}") or True,
            )
        i_fn, s_fn = make_handlers(name)
        init_mgr.register_initializer(name, i_fn, s_fn)

    init_mgr.initialize_all()
    events.clear()

    init_mgr.restart_all()
    assert init_mgr.restart_count == 1
    assert events[0].startswith("shutdown_")
    assert events[len(DETERMINISTIC_INITIALIZATION_ORDER)].startswith("init_")


def test_initialization_manager_concurrent_checks():
    """Verify thread safety during concurrent initialization status queries."""
    init_mgr = InitializationManager()

    def query_status():
        return init_mgr.is_initialized(), init_mgr.get_initialized_components()

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(query_status) for _ in range(20)]
        results = [f.result() for f in futures]

    assert len(results) == 20


# ============================================================================
# 4. Startup Validator Tests
# ============================================================================


def test_startup_validator_passes():
    """Verify StartupValidator passes for valid configuration and registry."""
    validator = StartupValidator()
    config = ApplicationConfiguration(app_name="Auralis", version="1.0.0")
    registry = RuntimeRegistry()
    registry.register_runtime(RuntimeRegistration(name="brain_runtime"))

    diag = validator.validate_startup(config, registry)
    assert isinstance(diag, ApplicationDiagnostics)
    assert len(validator.run_all_validations(config)) == 0


def test_startup_validator_empty_registry():
    """Verify StartupValidator fails when registry is empty."""
    validator = StartupValidator()
    config = ApplicationConfiguration()
    registry = RuntimeRegistry()

    with pytest.raises(StartupValidationError):
        validator.validate_startup(config, registry)


def test_startup_validator_inactive_runtime():
    """Verify StartupValidator fails when an inactive runtime is registered."""
    validator = StartupValidator()
    config = ApplicationConfiguration()
    registry = RuntimeRegistry()
    registry.register_runtime(RuntimeRegistration(name="inactive_sys", is_active=False))

    with pytest.raises(StartupValidationError):
        validator.validate_startup(config, registry)


def test_startup_validator_invalid_config():
    """Verify StartupValidator fails when configuration app_name is empty."""
    validator = StartupValidator()
    config = ApplicationConfiguration(app_name="")

    assert validator.validate_configuration(config) is False
    with pytest.raises(StartupValidationError):
        validator.validate_startup(config)


def test_startup_validator_validate_versions_and_health():
    """Verify validate_versions, validate_health, and validate_dependencies."""
    validator = StartupValidator()
    assert validator.validate_versions() is True
    assert validator.validate_dependencies() is True
    assert validator.validate_runtime_dependencies() is True
    assert validator.validate_health(ApplicationHealth(is_healthy=True)) is True
    assert validator.validate_health(ApplicationHealth(is_healthy=False)) is False


# ============================================================================
# 5. Bootstrap Manager Tests
# ============================================================================


def test_bootstrap_manager_successful_boot():
    """Verify successful boot sequence in BootstrapManager."""
    init_mgr = InitializationManager()
    validator = StartupValidator()
    registry = RuntimeRegistry()
    registry.register_runtime(RuntimeRegistration(name="brain_runtime"))

    boot_mgr = BootstrapManager(
        initialization_manager=init_mgr,
        startup_validator=validator,
        runtime_registry=registry,
    )

    state = boot_mgr.boot()
    assert state.status == ApplicationLifecycleState.RUNNING
    assert state.is_active is True
    assert boot_mgr.is_bootstrapped() is True
    assert boot_mgr.boot_success is True
    assert boot_mgr.boot_duration >= 0.0

    stats = boot_mgr.collect_boot_statistics()
    assert stats.metrics["boot_success"] == 1.0
    assert stats.metrics["boot_count"] == 1.0


def test_bootstrap_manager_bootstrap_and_teardown_aliases():
    """Verify bootstrap() and teardown() interface aliases."""
    boot_mgr = BootstrapManager()
    state = boot_mgr.bootstrap(ApplicationConfiguration())
    assert state.status == ApplicationLifecycleState.RUNNING
    assert boot_mgr.get_bootstrap_state().status == ApplicationLifecycleState.RUNNING

    teardown_state = boot_mgr.teardown()
    assert teardown_state.status == ApplicationLifecycleState.SHUTDOWN


def test_bootstrap_manager_validation_failure():
    """Verify BootstrapManager handles validation failures."""
    validator = StartupValidator()
    registry = RuntimeRegistry()  # Empty registry fails validation

    boot_mgr = BootstrapManager(
        startup_validator=validator,
        runtime_registry=registry,
    )

    with pytest.raises(ApplicationBootstrapError):
        boot_mgr.boot()

    assert boot_mgr.boot_failures == 1
    assert boot_mgr.boot_success is False
    assert boot_mgr.get_bootstrap_state().status == ApplicationLifecycleState.FAILED


def test_bootstrap_manager_initialization_failure():
    """Verify BootstrapManager handles subsystem initialization failures."""
    init_mgr = InitializationManager()
    init_mgr.register_initializer("brain_runtime", lambda: False)

    boot_mgr = BootstrapManager(initialization_manager=init_mgr)

    with pytest.raises(ApplicationBootstrapError):
        boot_mgr.boot()

    assert boot_mgr.boot_failures == 1
    assert boot_mgr.boot_success is False


def test_bootstrap_manager_restart_and_shutdown():
    """Verify BootstrapManager restart and shutdown lifecycle."""
    boot_mgr = BootstrapManager()
    boot_mgr.boot()
    assert boot_mgr.is_bootstrapped() is True

    boot_mgr.restart()
    assert boot_mgr.restart_count == 1
    assert boot_mgr.is_bootstrapped() is True

    shutdown_state = boot_mgr.shutdown()
    assert shutdown_state.status == ApplicationLifecycleState.SHUTDOWN
    assert boot_mgr.is_bootstrapped() is False


def test_bootstrap_manager_multiple_boots():
    """Verify calling boot() multiple times safely updates boot count."""
    boot_mgr = BootstrapManager()
    boot_mgr.boot()
    assert boot_mgr.boot_count == 1
    boot_mgr.boot()
    assert boot_mgr.boot_count == 2


# ============================================================================
# 6. Production ApplicationRuntime Tests
# ============================================================================


def test_application_runtime_full_lifecycle_state_transitions():
    """Verify ApplicationRuntime state transitions during initialize()."""
    registry = RuntimeRegistry()
    registry.register_runtime(RuntimeRegistration(name="brain_runtime"))
    app_runtime = ApplicationRuntime(runtime_registry=registry)

    assert app_runtime.status() == ApplicationLifecycleState.UNINITIALIZED

    state = app_runtime.initialize()
    assert state.status == ApplicationLifecycleState.RUNNING
    assert state.is_active is True
    assert app_runtime.status() == ApplicationLifecycleState.RUNNING


def test_application_runtime_start_alias():
    """Verify start() method initializes if not running."""
    registry = RuntimeRegistry()
    registry.register_runtime(RuntimeRegistration(name="brain_runtime"))
    app_runtime = ApplicationRuntime(runtime_registry=registry)

    state = app_runtime.start()
    assert state.status == ApplicationLifecycleState.RUNNING


def test_application_runtime_restart():
    """Verify ApplicationRuntime restart behavior."""
    registry = RuntimeRegistry()
    registry.register_runtime(RuntimeRegistration(name="brain_runtime"))
    app_runtime = ApplicationRuntime(runtime_registry=registry)

    app_runtime.initialize()
    state = app_runtime.restart()
    assert state.status == ApplicationLifecycleState.RUNNING
    stats = app_runtime.statistics()
    assert stats.metrics["restart_count"] >= 1.0


def test_application_runtime_shutdown_and_stop():
    """Verify ApplicationRuntime shutdown and stop."""
    app_runtime = ApplicationRuntime()
    app_runtime.initialize()

    state = app_runtime.shutdown()
    assert state.status == ApplicationLifecycleState.STOPPED
    assert state.is_active is False

    app_runtime.initialize()
    stop_state = app_runtime.stop()
    assert stop_state.status == ApplicationLifecycleState.STOPPED


def test_application_runtime_health_aggregation():
    """Verify ApplicationRuntime health aggregation."""
    registry = RuntimeRegistry()
    registry.register_runtime(RuntimeRegistration(name="r1", is_active=True))
    app_runtime = ApplicationRuntime(runtime_registry=registry)

    app_runtime.initialize()
    health = app_runtime.health()
    assert health.is_healthy is True
    assert health.subsystem_health["r1"] is True
    assert health.subsystem_health["runtime_registry"] is True


def test_application_runtime_statistics_aggregation():
    """Verify ApplicationRuntime statistics metrics aggregation."""
    registry = RuntimeRegistry()
    registry.register_runtime(RuntimeRegistration(name="sys1"))
    app_runtime = ApplicationRuntime(runtime_registry=registry)

    app_runtime.initialize()
    stats = app_runtime.statistics()
    assert stats.registered_runtimes_count == 1
    assert "uptime_seconds" in stats.metrics
    assert "boot_count" in stats.metrics


def test_application_runtime_capabilities():
    """Verify ApplicationCapabilities returned by ApplicationRuntime."""
    app_runtime = ApplicationRuntime()
    caps = app_runtime.capabilities()
    assert caps.supports_restart is True
    assert caps.supports_bootstrap is True
    assert caps.supports_runtime_registration is True
    assert caps.supports_health_checks is True
    assert caps.supports_validation is True
    assert caps.supports_shutdown is True


def test_application_runtime_diagnostics():
    """Verify ApplicationRuntime diagnostics generation."""
    app_runtime = ApplicationRuntime()
    diag = app_runtime.diagnostics()
    assert isinstance(diag, ApplicationDiagnostics)
    assert len(diag.diagnostic_messages) > 0


def test_application_runtime_register_lookup_and_clear():
    """Verify ApplicationRuntime sub-registry delegation."""
    app_runtime = ApplicationRuntime()
    reg = RuntimeRegistration(name="custom_sub")

    assert app_runtime.register_runtime(reg) is True
    assert app_runtime.lookup_runtime("custom_sub") == reg
    app_runtime.clear()
    assert app_runtime.lookup_runtime("custom_sub") is None


def test_application_runtime_boot():
    """Verify ApplicationRuntime boot delegation."""
    registry = RuntimeRegistry()
    registry.register_runtime(RuntimeRegistration(name="sys1"))
    app_runtime = ApplicationRuntime(runtime_registry=registry)

    boot_state = app_runtime.boot()
    assert boot_state.status == ApplicationLifecycleState.RUNNING


def test_application_runtime_validation_failure():
    """Verify ApplicationRuntime handles validation failure gracefully."""
    registry = RuntimeRegistry()
    # Register an inactive runtime to force validation failure
    registry.register_runtime(RuntimeRegistration(name="bad_sys", is_active=False))
    app_runtime = ApplicationRuntime(runtime_registry=registry)

    with pytest.raises(ApplicationBootstrapError):
        app_runtime.initialize()

    assert app_runtime.status() == ApplicationLifecycleState.FAILED


def test_application_runtime_initialization_failure():
    """Verify ApplicationRuntime handles initialization failure."""
    registry = RuntimeRegistry()
    registry.register_runtime(RuntimeRegistration(name="brain_runtime"))
    init_mgr = InitializationManager(runtime_registry=registry)
    init_mgr.register_initializer("brain_runtime", lambda: False)

    app_runtime = ApplicationRuntime(
        runtime_registry=registry, initialization_manager=init_mgr
    )

    with pytest.raises(InitializationError):
        app_runtime.initialize()

    assert app_runtime.status() == ApplicationLifecycleState.FAILED


# ============================================================================
# 7. Production ApplicationProvider Tests
# ============================================================================


def test_application_provider_lifecycle():
    """Verify ApplicationProvider lifecycle operations."""
    registry = RuntimeRegistry()
    registry.register_runtime(RuntimeRegistration(name="sys1"))
    provider = ApplicationProvider(runtime_registry=registry)

    state = provider.initialize()
    assert state.status == ApplicationLifecycleState.RUNNING

    restart_state = provider.restart()
    assert restart_state.status == ApplicationLifecycleState.RUNNING

    shutdown_state = provider.shutdown()
    assert shutdown_state.status == ApplicationLifecycleState.STOPPED


def test_application_provider_boot_and_validate():
    """Verify ApplicationProvider boot and validate methods."""
    registry = RuntimeRegistry()
    registry.register_runtime(RuntimeRegistration(name="sys1"))
    provider = ApplicationProvider(runtime_registry=registry)

    boot_state = provider.boot()
    assert boot_state.status == ApplicationLifecycleState.RUNNING

    diag = provider.validate()
    assert isinstance(diag, ApplicationDiagnostics)


def test_application_provider_runtime_delegation():
    """Verify ApplicationProvider sub-runtime management methods."""
    provider = ApplicationProvider()
    reg = RuntimeRegistration(name="sub_service")

    assert provider.register_runtime(reg) is True
    assert provider.get_runtime("sub_service") == reg
    assert len(provider.list_runtimes()) == 1
    assert provider.unregister_runtime("sub_service") is True
    assert len(provider.list_runtimes()) == 0


def test_application_provider_health_stats_capabilities_diagnostics():
    """Verify ApplicationProvider aggregate inspections."""
    provider = ApplicationProvider()
    provider.initialize()

    assert provider.health().is_healthy is True
    assert "uptime_seconds" in provider.statistics().metrics
    assert provider.capabilities().supports_restart is True
    assert isinstance(provider.diagnostics(), ApplicationDiagnostics)
    assert provider.get_configuration().app_name == "Auralis"
    assert isinstance(provider.get_context(), ApplicationContext)


# ============================================================================
# 8. Lazy Global Runtime Accessor Tests (runtime.py)
# ============================================================================


def test_runtime_py_lazy_singleton_accessors():
    """Verify lazy initialization and management in runtime.py."""
    reset_application_runtime()
    reset_application_provider()

    # Accessors lazily instantiate singletons if None
    rt = get_application_runtime()
    assert isinstance(rt, IApplicationRuntime)

    prov = get_application_provider()
    assert isinstance(prov, IApplicationProvider)

    # Manual setter and reset
    new_rt = ApplicationRuntime()
    set_application_runtime(new_rt)
    assert get_application_runtime() is new_rt

    reset_application_runtime()
    reset_application_provider()


# ============================================================================
# 9. Concurrency Tests
# ============================================================================


def test_application_runtime_concurrent_initialize():
    """Verify thread-safe concurrent initialize calls on ApplicationRuntime."""
    registry = RuntimeRegistry()
    registry.register_runtime(RuntimeRegistration(name="sys1"))
    app_runtime = ApplicationRuntime(runtime_registry=registry)

    def do_init():
        return app_runtime.initialize()

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(do_init) for _ in range(10)]
        results = [f.result() for f in futures]

    assert all(r.status == ApplicationLifecycleState.RUNNING for r in results)


def test_application_runtime_concurrent_restart():
    """Verify thread-safe concurrent restart calls on ApplicationRuntime."""
    registry = RuntimeRegistry()
    registry.register_runtime(RuntimeRegistration(name="sys1"))
    app_runtime = ApplicationRuntime(runtime_registry=registry)
    app_runtime.initialize()

    def do_restart():
        return app_runtime.restart()

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(do_restart) for _ in range(10)]
        results = [f.result() for f in futures]

    assert all(r.status == ApplicationLifecycleState.RUNNING for r in results)


def test_application_runtime_concurrent_shutdown():
    """Verify thread-safe concurrent shutdown calls on ApplicationRuntime."""
    app_runtime = ApplicationRuntime()
    app_runtime.initialize()

    def do_shutdown():
        return app_runtime.shutdown()

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(do_shutdown) for _ in range(10)]
        results = [f.result() for f in futures]

    assert all(r.status == ApplicationLifecycleState.STOPPED for r in results)
