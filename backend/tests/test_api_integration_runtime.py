"""Tests for API Integration Gateway Runtime (Phase 15.9).

Validates immutable models, enums, exception hierarchy, ABC interfaces,
gateway orchestration, request coordination, response coordination,
provider lifecycle, runtime coordinator, lazy singletons, and multithreaded concurrency.
"""

from concurrent.futures import ThreadPoolExecutor
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError as PydanticValidationError

from backend.application.api.integration import (
    ApiGateway,
    ApiIntegrationException,
    ApiIntegrationRequest,
    ApiIntegrationResponse,
    ApiPipelineStage,
    ApiRequestContext,
    ApiResponseContext,
    IApiGateway,
    IIntegrationProvider,
    IIntegrationRuntime,
    IRequestCoordinator,
    IResponseCoordinator,
    IntegrationCapabilities,
    IntegrationDiagnostics,
    IntegrationHealth,
    IntegrationProvider,
    IntegrationRuntime,
    IntegrationRuntimeState,
    IntegrationStatistics,
    PipelineExecutionException,
    PipelineStage,
    RequestCoordinationException,
    RequestCoordinator,
    ResponseCoordinationException,
    ResponseCoordinator,
    get_integration_provider,
    get_integration_runtime,
    reset_integration_provider,
    reset_integration_runtime,
    set_integration_provider,
    set_integration_runtime,
)


@pytest.fixture(autouse=True)
def _reset_integration_singletons():
    """Reset integration singletons before and after each test."""
    reset_integration_runtime()
    reset_integration_provider()
    yield
    reset_integration_runtime()
    reset_integration_provider()


# --- Enum Tests ---

def test_enum_pipeline_stage():
    """Verify PipelineStage enum values."""
    assert PipelineStage.ROUTING.value == "ROUTING"
    assert PipelineStage.MIDDLEWARE.value == "MIDDLEWARE"
    assert PipelineStage.AUTHENTICATION.value == "AUTHENTICATION"
    assert PipelineStage.VALIDATION.value == "VALIDATION"
    assert PipelineStage.VERSIONING.value == "VERSIONING"
    assert PipelineStage.PROTECTION.value == "PROTECTION"
    assert PipelineStage.WEBSOCKET.value == "WEBSOCKET"
    assert PipelineStage.COMPLETE.value == "COMPLETE"
    assert len(PipelineStage) == 8


def test_enum_integration_runtime_state():
    """Verify IntegrationRuntimeState enum values."""
    assert IntegrationRuntimeState.UNINITIALIZED.value == "UNINITIALIZED"
    assert IntegrationRuntimeState.INITIALIZING.value == "INITIALIZING"
    assert IntegrationRuntimeState.READY.value == "READY"
    assert IntegrationRuntimeState.STOPPING.value == "STOPPING"
    assert IntegrationRuntimeState.STOPPED.value == "STOPPED"
    assert len(IntegrationRuntimeState) == 5


# --- Model Immutability Tests ---

def test_model_immutability_api_pipeline_stage():
    """Verify ApiPipelineStage defaults and immutability."""
    stage = ApiPipelineStage(stage_id="s1", stage=PipelineStage.ROUTING)
    assert stage.stage_id == "s1"
    assert stage.is_enabled is True

    with pytest.raises((PydanticValidationError, TypeError)):
        stage.is_enabled = False  # type: ignore[attr-defined]


def test_model_immutability_api_integration_request():
    """Verify ApiIntegrationRequest defaults and immutability."""
    req = ApiIntegrationRequest(request_id="r1", path="/api/v1/resource")
    assert req.request_id == "r1"
    assert req.method == "GET"

    with pytest.raises((PydanticValidationError, TypeError)):
        req.method = "POST"  # type: ignore[attr-defined]


def test_model_immutability_api_integration_response():
    """Verify ApiIntegrationResponse defaults and immutability."""
    res = ApiIntegrationResponse(response_id="res1", request_id="r1")
    assert res.response_id == "res1"
    assert res.status_code == 200

    with pytest.raises((PydanticValidationError, TypeError)):
        res.status_code = 500  # type: ignore[attr-defined]


def test_model_immutability_api_request_context():
    """Verify ApiRequestContext defaults and immutability."""
    req = ApiIntegrationRequest(request_id="r1", path="/api")
    ctx = ApiRequestContext(context_id="ctx1", request=req)
    assert ctx.context_id == "ctx1"
    assert ctx.current_stage == PipelineStage.ROUTING

    with pytest.raises((PydanticValidationError, TypeError)):
        ctx.current_stage = PipelineStage.COMPLETE  # type: ignore[attr-defined]


def test_model_immutability_api_response_context():
    """Verify ApiResponseContext defaults and immutability."""
    res = ApiIntegrationResponse(response_id="res1", request_id="r1")
    ctx = ApiResponseContext(context_id="ctx1", response=res)
    assert ctx.context_id == "ctx1"

    with pytest.raises((PydanticValidationError, TypeError)):
        ctx.execution_time_ms = 10.0  # type: ignore[attr-defined]


def test_model_immutability_capabilities():
    """Verify IntegrationCapabilities defaults and immutability."""
    caps = IntegrationCapabilities()
    assert caps.supports_gateway_orchestration is True

    with pytest.raises((PydanticValidationError, TypeError)):
        caps.supports_gateway_orchestration = False  # type: ignore[attr-defined]


def test_model_immutability_statistics():
    """Verify IntegrationStatistics defaults and immutability."""
    stats = IntegrationStatistics()
    assert stats.total_requests_processed == 0

    with pytest.raises((PydanticValidationError, TypeError)):
        stats.total_requests_processed = 5  # type: ignore[attr-defined]


def test_model_immutability_health():
    """Verify IntegrationHealth defaults and immutability."""
    health = IntegrationHealth()
    assert health.is_healthy is True

    with pytest.raises((PydanticValidationError, TypeError)):
        health.is_healthy = False  # type: ignore[attr-defined]


def test_model_immutability_diagnostics():
    """Verify IntegrationDiagnostics defaults and immutability."""
    diag = IntegrationDiagnostics()
    assert diag.active_gateways_count == 0

    with pytest.raises((PydanticValidationError, TypeError)):
        diag.active_gateways_count = 10  # type: ignore[attr-defined]


# --- Exception Hierarchy Tests ---

def test_exception_hierarchy():
    """Verify exception hierarchy inheritance."""
    assert issubclass(RequestCoordinationException, ApiIntegrationException)
    assert issubclass(ResponseCoordinationException, ApiIntegrationException)
    assert issubclass(PipelineExecutionException, ApiIntegrationException)
    assert issubclass(ApiIntegrationException, Exception)


# --- Interface Abstraction Tests ---

def test_interfaces_cannot_be_instantiated():
    """Verify abstract base classes raise TypeError on direct instantiation."""
    with pytest.raises(TypeError):
        IApiGateway()  # type: ignore[abstract]

    with pytest.raises(TypeError):
        IRequestCoordinator()  # type: ignore[abstract]

    with pytest.raises(TypeError):
        IResponseCoordinator()  # type: ignore[abstract]

    with pytest.raises(TypeError):
        IIntegrationProvider()  # type: ignore[abstract]

    with pytest.raises(TypeError):
        IIntegrationRuntime()  # type: ignore[abstract]


# --- RequestCoordinator Tests ---

def test_request_coordinator_coordinate_success():
    """Verify successful request coordination."""
    coord = RequestCoordinator()
    req = ApiIntegrationRequest(request_id="r1", path="/api/v1/test", method="GET")

    ctx = coord.coordinate_request(req)
    assert ctx.request == req
    assert ctx.current_stage == PipelineStage.ROUTING


def test_request_coordinator_validate_metadata_valid():
    """Verify valid request metadata."""
    coord = RequestCoordinator()
    req = ApiIntegrationRequest(request_id="r1", path="/path", method="POST")
    assert coord.validate_request_metadata(req) is True


def test_request_coordinator_validate_metadata_invalid_id():
    """Verify invalid request metadata when request_id is empty."""
    coord = RequestCoordinator()
    req = ApiIntegrationRequest(request_id=" ", path="/path", method="GET")
    assert coord.validate_request_metadata(req) is False


def test_request_coordinator_validate_metadata_invalid_path():
    """Verify invalid request metadata when path is empty."""
    coord = RequestCoordinator()
    req = ApiIntegrationRequest(request_id="r1", path="", method="GET")
    assert coord.validate_request_metadata(req) is False


def test_request_coordinator_validate_metadata_invalid_method():
    """Verify invalid request metadata when method is empty."""
    coord = RequestCoordinator()
    req = ApiIntegrationRequest(request_id="r1", path="/path", method="")
    assert coord.validate_request_metadata(req) is False


def test_request_coordinator_coordinate_invalid_exception():
    """Verify RequestCoordinationException on invalid request."""
    coord = RequestCoordinator()
    req = ApiIntegrationRequest(request_id="", path="", method="")

    with pytest.raises(RequestCoordinationException):
        coord.coordinate_request(req)


# --- ResponseCoordinator Tests ---

def test_response_coordinator_coordinate_response():
    """Verify response coordination and context encapsulation."""
    coord = ResponseCoordinator()
    res = ApiIntegrationResponse(response_id="res1", request_id="r1", status_code=200)

    ctx = coord.coordinate_response(res, execution_time_ms=12.5)
    assert ctx.response == res
    assert ctx.execution_time_ms == 12.5
    assert ctx.diagnostics.get("status_code") == 200


def test_response_coordinator_format_error_response():
    """Verify formatting an immutable error response."""
    coord = ResponseCoordinator()
    err_res = coord.format_error_response(
        request_id="r1",
        error_message="Unauthorized access",
        status_code=401,
        stage=PipelineStage.AUTHENTICATION,
    )

    assert err_res.request_id == "r1"
    assert err_res.status_code == 401
    assert err_res.stage_reached == PipelineStage.AUTHENTICATION
    assert err_res.body == {"error": "Unauthorized access", "stage": "AUTHENTICATION"}


# --- ApiGateway Tests ---

def test_gateway_list_pipeline_stages():
    """Verify listing configured pipeline stages in order."""
    gateway = ApiGateway()
    stages = gateway.list_pipeline_stages()

    assert len(stages) == 8
    orders = [s.order for s in stages]
    assert orders == sorted(orders)


def test_gateway_process_request_success():
    """Verify gateway processing a valid request through pipeline."""
    gateway = ApiGateway()
    req = ApiIntegrationRequest(request_id="r1", path="/api/v1/users", method="GET")

    res = gateway.process_request(req)
    assert res.request_id == "r1"
    assert res.status_code == 200
    assert res.stage_reached == PipelineStage.COMPLETE


def test_gateway_process_request_invalid_metadata():
    """Verify gateway handling invalid request metadata with 400 error response."""
    gateway = ApiGateway()
    req = ApiIntegrationRequest(request_id="", path="", method="")

    res = gateway.process_request(req)
    assert res.status_code == 400
    assert res.stage_reached == PipelineStage.ROUTING


def test_gateway_get_statistics():
    """Verify gateway statistics tracking."""
    gateway = ApiGateway()
    req = ApiIntegrationRequest(request_id="r1", path="/api/v1/test")

    gateway.process_request(req)
    stats = gateway.get_gateway_statistics()

    assert stats.total_requests_processed == 1
    assert stats.successful_requests == 1
    assert stats.failed_requests == 0


# --- Provider & Runtime Tests ---

def test_provider_lifecycle():
    """Verify IntegrationProvider initialize and shutdown transitions."""
    provider = IntegrationProvider()
    assert provider.health().state == IntegrationRuntimeState.UNINITIALIZED

    health1 = provider.initialize()
    assert health1.state == IntegrationRuntimeState.READY
    assert health1.is_healthy is True

    health2 = provider.shutdown()
    assert health2.state == IntegrationRuntimeState.STOPPED
    assert health2.is_healthy is False


def test_provider_restart():
    """Verify IntegrationProvider restart cycle."""
    provider = IntegrationProvider()
    provider.initialize()

    health = provider.restart()
    assert health.state == IntegrationRuntimeState.READY
    assert provider.statistics().metrics.get("total_restarts") == 1.0


def test_provider_health_stats_caps_diag():
    """Verify health, statistics, capabilities, and diagnostics from provider."""
    provider = IntegrationProvider()
    provider.initialize()

    assert provider.health().is_healthy is True
    assert provider.capabilities().supports_gateway_orchestration is True
    assert provider.diagnostics().active_gateways_count == 1


def test_runtime_lifecycle_delegation():
    """Verify IntegrationRuntime delegates lifecycle calls to provider."""
    runtime = IntegrationRuntime()
    assert runtime.health().state == IntegrationRuntimeState.UNINITIALIZED

    runtime.initialize()
    assert runtime.health().state == IntegrationRuntimeState.READY

    runtime.shutdown()
    assert runtime.health().state == IntegrationRuntimeState.STOPPED


def test_constructor_dependency_injection():
    """Verify Constructor DI in IntegrationProvider and IntegrationRuntime."""
    req_coord = RequestCoordinator()
    res_coord = ResponseCoordinator()
    gateway = ApiGateway(request_coordinator=req_coord, response_coordinator=res_coord)

    provider = IntegrationProvider(
        api_gateway=gateway,
        request_coordinator=req_coord,
        response_coordinator=res_coord,
    )
    runtime = IntegrationRuntime(provider=provider)

    assert runtime.get_provider().get_api_gateway() is gateway
    assert runtime.get_provider().get_request_coordinator() is req_coord
    assert runtime.get_provider().get_response_coordinator() is res_coord


# --- Lazy Singleton Helper Tests ---

def test_lazy_singleton_integration_runtime():
    """Verify get_integration_runtime, set_integration_runtime, and reset_integration_runtime."""
    r1 = get_integration_runtime()
    r2 = get_integration_runtime()
    assert r1 is r2
    assert isinstance(r1, IntegrationRuntime)

    custom = IntegrationRuntime()
    set_integration_runtime(custom)
    assert get_integration_runtime() is custom

    reset_integration_runtime()
    r3 = get_integration_runtime()
    assert r3 is not custom


def test_lazy_singleton_integration_provider():
    """Verify get_integration_provider, set_integration_provider, and reset_integration_provider."""
    p1 = get_integration_provider()
    p2 = get_integration_provider()
    assert p1 is p2
    assert isinstance(p1, IntegrationProvider)

    custom = IntegrationProvider()
    set_integration_provider(custom)
    assert get_integration_provider() is custom

    reset_integration_provider()
    p3 = get_integration_provider()
    assert p3 is not custom


# --- Additional Utility Tests ---

def test_request_headers_params_body_preservation():
    """Verify headers, params, and body are preserved across coordination."""
    coord = RequestCoordinator()
    req = ApiIntegrationRequest(
        request_id="r1",
        path="/api/search",
        method="POST",
        headers={"Authorization": "Bearer token"},
        params={"q": "voice"},
        body={"filter": "active"},
    )
    ctx = coord.coordinate_request(req)
    assert ctx.request.headers == {"Authorization": "Bearer token"}
    assert ctx.request.params == {"q": "voice"}
    assert ctx.request.body == {"filter": "active"}


def test_response_status_code_body_preservation():
    """Verify response status code and body are preserved across coordination."""
    coord = ResponseCoordinator()
    res = ApiIntegrationResponse(
        response_id="res1",
        request_id="r1",
        status_code=201,
        body={"id": 123},
    )
    ctx = coord.coordinate_response(res, execution_time_ms=5.0)
    assert ctx.response.status_code == 201
    assert ctx.response.body == {"id": 123}


def test_error_response_stage_reached():
    """Verify format_error_response preserves stage_reached."""
    coord = ResponseCoordinator()
    res = coord.format_error_response("r1", "Validation error", 422, PipelineStage.VALIDATION)
    assert res.stage_reached == PipelineStage.VALIDATION
    assert res.status_code == 422


def test_gateway_multiple_requests_statistics():
    """Verify gateway statistics over multiple requests."""
    gateway = ApiGateway()
    for i in range(5):
        gateway.process_request(ApiIntegrationRequest(request_id=f"r_{i}", path=f"/p_{i}"))

    # Process 2 invalid requests
    gateway.process_request(ApiIntegrationRequest(request_id="", path=""))
    gateway.process_request(ApiIntegrationRequest(request_id="", path=""))

    stats = gateway.get_gateway_statistics()
    assert stats.total_requests_processed == 7
    assert stats.successful_requests == 5
    assert stats.failed_requests == 2


def test_provider_health_details():
    """Verify provider health details map."""
    provider = IntegrationProvider()
    provider.initialize()
    health = provider.health()

    assert "processed_requests" in health.details
    assert "successful_requests" in health.details
    assert "failed_requests" in health.details


def test_provider_diagnostics_messages():
    """Verify provider diagnostics messages format."""
    provider = IntegrationProvider()
    provider.initialize()
    diag = provider.diagnostics()

    assert len(diag.diagnostic_messages) > 0
    assert "Status: READY" in diag.diagnostic_messages[0]


def test_custom_capabilities_support():
    """Verify custom capabilities dictionary in IntegrationCapabilities."""
    caps = IntegrationCapabilities(custom_capabilities={"gRPC": True})
    assert caps.custom_capabilities.get("gRPC") is True


def test_provider_getters():
    """Verify provider getter accessors."""
    provider = IntegrationProvider()
    assert isinstance(provider.get_api_gateway(), ApiGateway)
    assert isinstance(provider.get_request_coordinator(), RequestCoordinator)
    assert isinstance(provider.get_response_coordinator(), ResponseCoordinator)


def test_runtime_get_provider():
    """Verify runtime get_provider accessor."""
    runtime = IntegrationRuntime()
    assert isinstance(runtime.get_provider(), IntegrationProvider)


def test_request_coordinator_telemetry():
    """Verify request coordinator telemetry counter."""
    coord = RequestCoordinator()
    coord.coordinate_request(ApiIntegrationRequest(request_id="r1", path="/a"))
    coord.coordinate_request(ApiIntegrationRequest(request_id="r2", path="/b"))

    telemetry = coord.get_coordinator_telemetry()
    assert telemetry.get("total_requests_coordinated") == 2


def test_response_coordinator_telemetry():
    """Verify response coordinator telemetry counter."""
    coord = ResponseCoordinator()
    res = ApiIntegrationResponse(response_id="res1", request_id="r1")
    coord.coordinate_response(res)

    telemetry = coord.get_coordinator_telemetry()
    assert telemetry.get("total_responses_coordinated") == 1


def test_pipeline_stage_ordering():
    """Verify pipeline stage order values."""
    gateway = ApiGateway()
    stages = gateway.list_pipeline_stages()
    stage_names = [s.stage for s in stages]

    expected = [
        PipelineStage.ROUTING,
        PipelineStage.MIDDLEWARE,
        PipelineStage.AUTHENTICATION,
        PipelineStage.VALIDATION,
        PipelineStage.VERSIONING,
        PipelineStage.PROTECTION,
        PipelineStage.WEBSOCKET,
        PipelineStage.COMPLETE,
    ]
    assert stage_names == expected


# --- Concurrency Tests ---

def test_concurrent_gateway_request_processing():
    """Verify thread-safety of ApiGateway under concurrent request processing."""
    gateway = ApiGateway()

    def gateway_worker(idx: int):
        req = ApiIntegrationRequest(request_id=f"r_{idx}", path=f"/api/resource/{idx}")
        res = gateway.process_request(req)
        return res.status_code == 200

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(gateway_worker, i) for i in range(50)]
        results = [f.result() for f in futures]

    assert len(results) == 50
    assert all(results)

    stats = gateway.get_gateway_statistics()
    assert stats.total_requests_processed == 50
    assert stats.successful_requests == 50


def test_concurrent_request_coordination():
    """Verify thread-safety of RequestCoordinator under concurrent coordination calls."""
    coord = RequestCoordinator()

    def coord_worker(idx: int):
        req = ApiIntegrationRequest(request_id=f"r_{idx}", path=f"/path/{idx}")
        return coord.coordinate_request(req).request.request_id == f"r_{idx}"

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(coord_worker, i) for i in range(50)]
        results = [f.result() for f in futures]

    assert len(results) == 50
    assert all(results)


def test_concurrent_response_coordination():
    """Verify thread-safety of ResponseCoordinator under concurrent coordination calls."""
    coord = ResponseCoordinator()

    def res_worker(idx: int):
        res = ApiIntegrationResponse(response_id=f"res_{idx}", request_id=f"r_{idx}")
        return coord.coordinate_response(res, execution_time_ms=float(idx)).execution_time_ms == float(idx)

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(res_worker, i) for i in range(50)]
        results = [f.result() for f in futures]

    assert len(results) == 50
    assert all(results)


def test_gateway_pipeline_execution_counter():
    """Verify gateway total_pipeline_executions counter."""
    gateway = ApiGateway()
    gateway.process_request(ApiIntegrationRequest(request_id="r1", path="/a"))
    gateway.process_request(ApiIntegrationRequest(request_id="r2", path="/b"))

    stats = gateway.get_gateway_statistics()
    assert stats.total_pipeline_executions == 2


def test_concurrent_provider_restarts():
    """Verify provider stability under concurrent restart requests."""
    provider = IntegrationProvider()
    provider.initialize()

    def restart_worker(idx: int):
        return provider.restart().is_healthy

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(restart_worker, i) for i in range(10)]
        results = [f.result() for f in futures]

    assert all(results)
    assert provider.health().is_healthy is True


def test_pipeline_stage_disabled_check():
    """Verify pipeline stages can be listed and filtered by is_enabled."""
    gateway = ApiGateway()
    stages = gateway.list_pipeline_stages()
    enabled_stages = [s for s in stages if s.is_enabled]

    assert len(enabled_stages) == 8

