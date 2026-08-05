"""Tests for API Middleware Runtime (Phase 15.3).

Validates immutable models, enums, exception hierarchy, ABC interfaces,
middleware registry, priority ordering, enable/disable state toggles,
pipeline building across stages, middleware executor engine, middleware provider,
middleware runtime coordinator, lazy singletons, and multithreaded concurrency.
"""

from concurrent.futures import ThreadPoolExecutor
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from backend.application.api.middleware import (
    ApiMiddleware,
    DuplicateMiddlewareException,
    IMiddlewareExecutor,
    IMiddlewareProvider,
    IMiddlewareRegistry,
    IMiddlewareRuntime,
    IPipelineManager,
    MiddlewareCapabilities,
    MiddlewareContext,
    MiddlewareDiagnostics,
    MiddlewareException,
    MiddlewareExecution,
    MiddlewareExecutionException,
    MiddlewareExecutor,
    MiddlewareHealth,
    MiddlewareProvider,
    MiddlewareRegistrationException,
    MiddlewareRegistry,
    MiddlewareResult,
    MiddlewareRuntime,
    MiddlewareRuntimeState,
    MiddlewareStage,
    MiddlewareState,
    MiddlewareStatistics,
    PipelineException,
    PipelineManager,
    get_middleware_provider,
    get_middleware_runtime,
    reset_middleware_provider,
    reset_middleware_runtime,
    set_middleware_provider,
    set_middleware_runtime,
)


@pytest.fixture(autouse=True)
def _reset_middleware_singletons():
    """Reset middleware singletons before and after each test."""
    reset_middleware_runtime()
    reset_middleware_provider()
    yield
    reset_middleware_runtime()
    reset_middleware_provider()


# --- Enum Tests ---

def test_enum_middleware_stage():
    """Verify MiddlewareStage enum values."""
    assert MiddlewareStage.BEFORE_REQUEST.value == "BEFORE_REQUEST"
    assert MiddlewareStage.AROUND_REQUEST.value == "AROUND_REQUEST"
    assert MiddlewareStage.AFTER_REQUEST.value == "AFTER_REQUEST"
    assert MiddlewareStage.ERROR_HANDLER.value == "ERROR_HANDLER"
    assert len(MiddlewareStage) == 4


def test_enum_middleware_state():
    """Verify MiddlewareState enum values."""
    assert MiddlewareState.REGISTERED.value == "REGISTERED"
    assert MiddlewareState.ENABLED.value == "ENABLED"
    assert MiddlewareState.DISABLED.value == "DISABLED"
    assert len(MiddlewareState) == 3


def test_enum_middleware_runtime_state():
    """Verify MiddlewareRuntimeState enum values."""
    assert MiddlewareRuntimeState.UNINITIALIZED.value == "UNINITIALIZED"
    assert MiddlewareRuntimeState.INITIALIZING.value == "INITIALIZING"
    assert MiddlewareRuntimeState.READY.value == "READY"
    assert MiddlewareRuntimeState.STOPPING.value == "STOPPING"
    assert MiddlewareRuntimeState.STOPPED.value == "STOPPED"
    assert len(MiddlewareRuntimeState) == 5


# --- Model Immutability Tests ---

def test_model_immutability_api_middleware():
    """Verify ApiMiddleware model defaults and immutability."""
    mw = ApiMiddleware(middleware_id="mw1", name="LoggerMiddleware")
    assert mw.middleware_id == "mw1"
    assert mw.stage == MiddlewareStage.BEFORE_REQUEST
    assert mw.state == MiddlewareState.ENABLED

    with pytest.raises(ValidationError):
        mw.name = "NewName"  # type: ignore[attr-defined]


def test_model_immutability_middleware_context():
    """Verify MiddlewareContext immutability."""
    ctx = MiddlewareContext(context_id="ctx1", route_id="r1")
    assert ctx.context_id == "ctx1"
    assert ctx.route_id == "r1"

    with pytest.raises(ValidationError):
        ctx.context_id = "ctx2"  # type: ignore[attr-defined]


def test_model_immutability_middleware_execution():
    """Verify MiddlewareExecution immutability."""
    exec_record = MiddlewareExecution(
        execution_id="e1", middleware_id="mw1", stage=MiddlewareStage.BEFORE_REQUEST
    )
    assert exec_record.execution_id == "e1"
    assert exec_record.status == "SUCCESS"

    with pytest.raises(ValidationError):
        exec_record.status = "FAILED"  # type: ignore[attr-defined]


def test_model_immutability_middleware_result():
    """Verify MiddlewareResult immutability."""
    res = MiddlewareResult(is_success=True, stage=MiddlewareStage.BEFORE_REQUEST)
    assert res.is_success is True

    with pytest.raises(ValidationError):
        res.is_success = False  # type: ignore[attr-defined]


def test_model_immutability_middleware_capabilities():
    """Verify MiddlewareCapabilities immutability."""
    caps = MiddlewareCapabilities()
    assert caps.supports_priority_ordering is True

    with pytest.raises(ValidationError):
        caps.supports_priority_ordering = False  # type: ignore[attr-defined]


def test_model_immutability_middleware_statistics():
    """Verify MiddlewareStatistics immutability."""
    stats = MiddlewareStatistics()
    assert stats.total_middlewares == 0

    with pytest.raises(ValidationError):
        stats.total_middlewares = 5  # type: ignore[attr-defined]


def test_model_immutability_middleware_health():
    """Verify MiddlewareHealth immutability."""
    health = MiddlewareHealth()
    assert health.is_healthy is True

    with pytest.raises(ValidationError):
        health.is_healthy = False  # type: ignore[attr-defined]


def test_model_immutability_middleware_diagnostics():
    """Verify MiddlewareDiagnostics immutability."""
    diag = MiddlewareDiagnostics()
    assert diag.registered_count == 0

    with pytest.raises(ValidationError):
        diag.registered_count = 10  # type: ignore[attr-defined]


# --- Exception Hierarchy Tests ---

def test_exception_hierarchy():
    """Verify middleware exception hierarchy inheritance."""
    assert issubclass(DuplicateMiddlewareException, MiddlewareRegistrationException)
    assert issubclass(MiddlewareRegistrationException, MiddlewareException)
    assert issubclass(MiddlewareExecutionException, MiddlewareException)
    assert issubclass(PipelineException, MiddlewareException)
    assert issubclass(MiddlewareException, Exception)


# --- Interface Abstraction Tests ---

def test_interfaces_cannot_be_instantiated():
    """Verify abstract base classes raise TypeError on direct instantiation."""
    with pytest.raises(TypeError):
        IMiddlewareRegistry()  # type: ignore[abstract]

    with pytest.raises(TypeError):
        IPipelineManager()  # type: ignore[abstract]

    with pytest.raises(TypeError):
        IMiddlewareExecutor()  # type: ignore[abstract]

    with pytest.raises(TypeError):
        IMiddlewareProvider()  # type: ignore[abstract]

    with pytest.raises(TypeError):
        IMiddlewareRuntime()  # type: ignore[abstract]


# --- MiddlewareRegistry Tests ---

def test_registry_register_and_lookup():
    """Verify registering and looking up middleware."""
    registry = MiddlewareRegistry()
    mw = ApiMiddleware(middleware_id="mw1", name="AuthCheck")
    registered = registry.register(mw)

    assert registered.middleware_id == "mw1"
    assert registry.lookup("mw1") == mw
    assert registry.count() == 1


def test_registry_unregister():
    """Verify unregistering middleware."""
    registry = MiddlewareRegistry()
    mw = ApiMiddleware(middleware_id="mw1", name="AuthCheck")
    registry.register(mw)

    removed = registry.unregister("mw1")
    assert removed == mw
    assert registry.lookup("mw1") is None
    assert registry.count() == 0


def test_registry_contains_and_count():
    """Verify registry contains check and count."""
    registry = MiddlewareRegistry()
    assert registry.contains("mw1") is False
    assert registry.count() == 0

    registry.register(ApiMiddleware(middleware_id="mw1", name="Test"))
    assert registry.contains("mw1") is True
    assert registry.count() == 1


def test_registry_list_middlewares_priority_ordering():
    """Verify priority ordering (lower priority number first)."""
    registry = MiddlewareRegistry()
    mw1 = ApiMiddleware(middleware_id="m1", name="LowPriority", priority=100)
    mw2 = ApiMiddleware(middleware_id="m2", name="HighPriority", priority=10)
    mw3 = ApiMiddleware(middleware_id="m3", name="MediumPriority", priority=50)

    registry.register(mw1)
    registry.register(mw2)
    registry.register(mw3)

    sorted_mws = registry.list_middlewares()
    assert [m.middleware_id for m in sorted_mws] == ["m2", "m3", "m1"]


def test_registry_enable_and_disable():
    """Verify enabling and disabling middleware."""
    registry = MiddlewareRegistry()
    mw = ApiMiddleware(middleware_id="m1", name="Test", state=MiddlewareState.ENABLED)
    registry.register(mw)

    disabled = registry.disable("m1")
    assert disabled is not None
    assert disabled.state == MiddlewareState.DISABLED
    assert registry.lookup("m1").state == MiddlewareState.DISABLED  # type: ignore[union-attr]

    enabled = registry.enable("m1")
    assert enabled is not None
    assert enabled.state == MiddlewareState.ENABLED


def test_registry_clear():
    """Verify clearing registry."""
    registry = MiddlewareRegistry()
    registry.register(ApiMiddleware(middleware_id="m1", name="Test1"))
    registry.register(ApiMiddleware(middleware_id="m2", name="Test2"))
    assert registry.count() == 2

    registry.clear()
    assert registry.count() == 0


def test_registry_duplicate_middleware_id():
    """Verify DuplicateMiddlewareException on duplicate ID."""
    registry = MiddlewareRegistry()
    registry.register(ApiMiddleware(middleware_id="m1", name="Test1"))

    with pytest.raises(DuplicateMiddlewareException):
        registry.register(ApiMiddleware(middleware_id="m1", name="Test2"))


# --- PipelineManager Tests ---

def test_pipeline_build_before_pipeline():
    """Verify building BEFORE_REQUEST pipeline."""
    registry = MiddlewareRegistry()
    m1 = ApiMiddleware(middleware_id="m1", name="B1", stage=MiddlewareStage.BEFORE_REQUEST, priority=20)
    m2 = ApiMiddleware(middleware_id="m2", name="A1", stage=MiddlewareStage.AFTER_REQUEST)
    registry.register(m1)
    registry.register(m2)

    pm = PipelineManager(registry=registry)
    before_p = pm.build_before_pipeline()
    assert len(before_p) == 1
    assert before_p[0].middleware_id == "m1"


def test_pipeline_build_around_pipeline():
    """Verify building AROUND_REQUEST pipeline."""
    registry = MiddlewareRegistry()
    m1 = ApiMiddleware(middleware_id="m1", name="Ar1", stage=MiddlewareStage.AROUND_REQUEST)
    registry.register(m1)

    pm = PipelineManager(registry=registry)
    around_p = pm.build_around_pipeline()
    assert len(around_p) == 1
    assert around_p[0].middleware_id == "m1"


def test_pipeline_build_after_pipeline():
    """Verify building AFTER_REQUEST pipeline."""
    registry = MiddlewareRegistry()
    m1 = ApiMiddleware(middleware_id="m1", name="A1", stage=MiddlewareStage.AFTER_REQUEST)
    registry.register(m1)

    pm = PipelineManager(registry=registry)
    after_p = pm.build_after_pipeline()
    assert len(after_p) == 1
    assert after_p[0].middleware_id == "m1"


def test_pipeline_build_error_pipeline():
    """Verify building ERROR_HANDLER pipeline."""
    registry = MiddlewareRegistry()
    m1 = ApiMiddleware(middleware_id="m1", name="E1", stage=MiddlewareStage.ERROR_HANDLER)
    registry.register(m1)

    pm = PipelineManager(registry=registry)
    err_p = pm.build_error_pipeline()
    assert len(err_p) == 1
    assert err_p[0].middleware_id == "m1"


def test_pipeline_excludes_disabled_middlewares():
    """Verify disabled middlewares are excluded from constructed pipelines."""
    registry = MiddlewareRegistry()
    m1 = ApiMiddleware(middleware_id="m1", name="Enabled", stage=MiddlewareStage.BEFORE_REQUEST, state=MiddlewareState.ENABLED)
    m2 = ApiMiddleware(middleware_id="m2", name="Disabled", stage=MiddlewareStage.BEFORE_REQUEST, state=MiddlewareState.DISABLED)
    registry.register(m1)
    registry.register(m2)

    pm = PipelineManager(registry=registry)
    pipeline = pm.build_before_pipeline()
    assert len(pipeline) == 1
    assert pipeline[0].middleware_id == "m1"


def test_pipeline_respects_priority_order():
    """Verify pipeline respects priority order."""
    registry = MiddlewareRegistry()
    m1 = ApiMiddleware(middleware_id="m1", name="P50", stage=MiddlewareStage.BEFORE_REQUEST, priority=50)
    m2 = ApiMiddleware(middleware_id="m2", name="P10", stage=MiddlewareStage.BEFORE_REQUEST, priority=10)
    m3 = ApiMiddleware(middleware_id="m3", name="P5", stage=MiddlewareStage.BEFORE_REQUEST, priority=5)

    registry.register(m1)
    registry.register(m2)
    registry.register(m3)

    pm = PipelineManager(registry=registry)
    pipeline = pm.build_before_pipeline()
    assert [m.middleware_id for m in pipeline] == ["m3", "m2", "m1"]


# --- MiddlewareExecutor Tests ---

def test_executor_execute_before_stage():
    """Verify execution of BEFORE_REQUEST stage pipeline."""
    registry = MiddlewareRegistry()
    registry.register(ApiMiddleware(middleware_id="m1", name="B1", stage=MiddlewareStage.BEFORE_REQUEST))
    registry.register(ApiMiddleware(middleware_id="m2", name="B2", stage=MiddlewareStage.BEFORE_REQUEST))

    pm = PipelineManager(registry=registry)
    executor = MiddlewareExecutor(pipeline_manager=pm)
    ctx = MiddlewareContext(context_id="c1", path="/v1/test")

    result = executor.execute_stage(MiddlewareStage.BEFORE_REQUEST, ctx)
    assert result.is_success is True
    assert len(result.executions) == 2
    assert result.executions[0].middleware_id == "m1"
    assert result.executions[1].middleware_id == "m2"


def test_executor_execute_around_stage():
    """Verify execution of AROUND_REQUEST stage pipeline."""
    registry = MiddlewareRegistry()
    registry.register(ApiMiddleware(middleware_id="m1", name="Ar1", stage=MiddlewareStage.AROUND_REQUEST))

    pm = PipelineManager(registry=registry)
    executor = MiddlewareExecutor(pipeline_manager=pm)
    ctx = MiddlewareContext(context_id="c1", path="/v1/test")

    result = executor.execute_stage(MiddlewareStage.AROUND_REQUEST, ctx)
    assert result.is_success is True
    assert len(result.executions) == 1


def test_executor_execute_after_stage():
    """Verify execution of AFTER_REQUEST stage pipeline."""
    registry = MiddlewareRegistry()
    registry.register(ApiMiddleware(middleware_id="m1", name="A1", stage=MiddlewareStage.AFTER_REQUEST))

    pm = PipelineManager(registry=registry)
    executor = MiddlewareExecutor(pipeline_manager=pm)
    ctx = MiddlewareContext(context_id="c1", path="/v1/test")

    result = executor.execute_stage(MiddlewareStage.AFTER_REQUEST, ctx)
    assert result.is_success is True
    assert len(result.executions) == 1


def test_executor_execute_error_stage():
    """Verify execution of ERROR_HANDLER stage pipeline."""
    registry = MiddlewareRegistry()
    registry.register(ApiMiddleware(middleware_id="m1", name="Err1", stage=MiddlewareStage.ERROR_HANDLER))

    pm = PipelineManager(registry=registry)
    executor = MiddlewareExecutor(pipeline_manager=pm)
    ctx = MiddlewareContext(context_id="c1", path="/v1/test")

    result = executor.execute_stage(MiddlewareStage.ERROR_HANDLER, ctx)
    assert result.is_success is True
    assert len(result.executions) == 1


def test_executor_empty_pipeline_execution():
    """Verify executing stage with no registered middlewares."""
    executor = MiddlewareExecutor()
    ctx = MiddlewareContext(context_id="c1")

    result = executor.execute_stage(MiddlewareStage.BEFORE_REQUEST, ctx)
    assert result.is_success is True
    assert len(result.executions) == 0


# --- MiddlewareProvider Tests ---

def test_provider_lifecycle():
    """Verify MiddlewareProvider initialize and shutdown transitions."""
    provider = MiddlewareProvider()
    assert provider.health().state == MiddlewareRuntimeState.UNINITIALIZED

    health1 = provider.initialize()
    assert health1.state == MiddlewareRuntimeState.READY
    assert health1.is_healthy is True

    health2 = provider.shutdown()
    assert health2.state == MiddlewareRuntimeState.STOPPED
    assert health2.is_healthy is False


def test_provider_restart():
    """Verify MiddlewareProvider restart cycle."""
    provider = MiddlewareProvider()
    provider.initialize()

    health = provider.restart()
    assert health.state == MiddlewareRuntimeState.READY
    assert provider.statistics().metrics.get("total_restarts") == 1.0


def test_provider_health():
    """Verify MiddlewareProvider health evaluation."""
    provider = MiddlewareProvider()
    assert provider.health().is_healthy is True

    provider.initialize()
    assert provider.health().is_healthy is True

    provider.shutdown()
    assert provider.health().is_healthy is False


def test_provider_statistics():
    """Verify MiddlewareProvider statistics aggregation."""
    registry = MiddlewareRegistry()
    registry.register(ApiMiddleware(middleware_id="m1", name="M1"))
    registry.register(ApiMiddleware(middleware_id="m2", name="M2", state=MiddlewareState.DISABLED))

    provider = MiddlewareProvider(registry=registry)
    provider.initialize()

    stats = provider.statistics()
    assert stats.total_middlewares == 2
    assert stats.enabled_middlewares == 1
    assert stats.disabled_middlewares == 1


def test_provider_capabilities():
    """Verify MiddlewareProvider capabilities snapshot."""
    provider = MiddlewareProvider()
    caps = provider.capabilities()
    assert caps.supports_before_request is True
    assert caps.supports_priority_ordering is True


def test_provider_diagnostics():
    """Verify MiddlewareProvider diagnostics snapshot."""
    registry = MiddlewareRegistry()
    registry.register(ApiMiddleware(middleware_id="m1", name="M1"))

    provider = MiddlewareProvider(registry=registry)
    provider.initialize()

    diag = provider.diagnostics()
    assert diag.registered_count == 1
    assert diag.enabled_count == 1
    assert len(diag.diagnostic_messages) > 0


# --- MiddlewareRuntime Tests ---

def test_runtime_lifecycle_delegation():
    """Verify MiddlewareRuntime delegates lifecycle methods to provider."""
    runtime = MiddlewareRuntime()
    assert runtime.health().state == MiddlewareRuntimeState.UNINITIALIZED

    runtime.initialize()
    assert runtime.health().state == MiddlewareRuntimeState.READY

    runtime.shutdown()
    assert runtime.health().state == MiddlewareRuntimeState.STOPPED


# --- Lazy Singleton Helper Tests ---

def test_lazy_singleton_middleware_runtime():
    """Verify get_middleware_runtime, set_middleware_runtime, and reset_middleware_runtime."""
    r1 = get_middleware_runtime()
    r2 = get_middleware_runtime()
    assert r1 is r2
    assert isinstance(r1, MiddlewareRuntime)

    custom = MiddlewareRuntime()
    set_middleware_runtime(custom)
    assert get_middleware_runtime() is custom

    reset_middleware_runtime()
    r3 = get_middleware_runtime()
    assert r3 is not custom


def test_lazy_singleton_middleware_provider():
    """Verify get_middleware_provider, set_middleware_provider, and reset_middleware_provider."""
    p1 = get_middleware_provider()
    p2 = get_middleware_provider()
    assert p1 is p2
    assert isinstance(p1, MiddlewareProvider)

    custom = MiddlewareProvider()
    set_middleware_provider(custom)
    assert get_middleware_provider() is custom

    reset_middleware_provider()
    p3 = get_middleware_provider()
    assert p3 is not custom


# --- Concurrency Tests ---

def test_concurrent_registry_operations():
    """Verify thread-safety of MiddlewareRegistry under concurrent registration and toggling."""
    registry = MiddlewareRegistry()

    def register_worker(idx: int):
        mw = ApiMiddleware(
            middleware_id=f"m_{idx}",
            name=f"Middleware_{idx}",
            priority=idx % 10,
        )
        registry.register(mw)
        if idx % 2 == 0:
            registry.disable(f"m_{idx}")

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(register_worker, i) for i in range(40)]
        for f in futures:
            f.result()

    assert registry.count() == 40


def test_concurrent_executor_operations():
    """Verify thread-safety of MiddlewareExecutor under concurrent stage executions."""
    registry = MiddlewareRegistry()
    registry.register(ApiMiddleware(middleware_id="m1", name="Shared1", stage=MiddlewareStage.BEFORE_REQUEST))
    registry.register(ApiMiddleware(middleware_id="m2", name="Shared2", stage=MiddlewareStage.BEFORE_REQUEST))

    pm = PipelineManager(registry=registry)
    executor = MiddlewareExecutor(pipeline_manager=pm)

    def execute_worker(idx: int):
        ctx = MiddlewareContext(context_id=f"c_{idx}")
        return executor.execute_stage(MiddlewareStage.BEFORE_REQUEST, ctx)

    with ThreadPoolExecutor(max_workers=10) as executor_pool:
        futures = [executor_pool.submit(execute_worker, i) for i in range(50)]
        results = [f.result() for f in futures]

    assert len(results) == 50
    assert all(r.is_success for r in results)
