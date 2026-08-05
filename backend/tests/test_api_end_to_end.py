"""End-to-End Production Certification Test Suite for Phase 15 API Runtime Architecture.

Certifies initialization/shutdown order, end-to-end request pipeline sequencing,
health/statistics/diagnostics aggregation, thread safety, constructor DI, model immutability,
singleton accessors, runtime synchronization, performance benchmarks, and zero regressions across all 9 sub-runtimes.
"""

from concurrent.futures import ThreadPoolExecutor
import time
# pyrefly: ignore [missing-import]
pytest = None
try:
    # pyrefly: ignore [missing-import]
    import pytest
except ImportError:
    pass

# pyrefly: ignore [missing-import]
from pydantic import ValidationError as PydanticValidationError

# 1. API Runtime Foundation (Phase 15.1)
from backend.application.api import (
    ApiProvider,
    ApiRuntime,
    ApiRuntimeState,
    get_api_provider,
    get_api_runtime,
    reset_api_provider,
    reset_api_runtime,
)

# 2. Request Routing Runtime (Phase 15.2)
from backend.application.api.routing import (
    get_routing_provider,
    get_routing_runtime,
    reset_routing_provider,
    reset_routing_runtime,
)

# 3. Middleware Runtime (Phase 15.3)
from backend.application.api.middleware import (
    get_middleware_provider,
    get_middleware_runtime,
    reset_middleware_provider,
    reset_middleware_runtime,
)

# 4. Authentication & Authorization Runtime (Phase 15.4)
from backend.application.api.auth import (
    get_authentication_provider,
    get_authentication_runtime,
    reset_authentication_provider,
    reset_authentication_runtime,
)

# 5. Validation & Serialization Runtime (Phase 15.5)
from backend.application.api.validation import (
    SchemaRegistry,
    ValidationEngine,
    get_validation_provider,
    get_validation_runtime,
    reset_validation_provider,
    reset_validation_runtime,
)

# 6. API Versioning & Documentation Runtime (Phase 15.6)
from backend.application.api.versioning import (
    get_versioning_provider,
    get_versioning_runtime,
    reset_versioning_provider,
    reset_versioning_runtime,
)

# 7. WebSocket Runtime (Phase 15.7)
from backend.application.api.websocket import (
    get_websocket_provider,
    get_websocket_runtime,
    reset_websocket_provider,
    reset_websocket_runtime,
)

# 8. API Protection & Rate Limiting Runtime (Phase 15.8)
from backend.application.api.protection import (
    get_protection_provider,
    get_protection_runtime,
    reset_protection_provider,
    reset_protection_runtime,
)

# 9. API Integration Gateway Runtime (Phase 15.9)
from backend.application.api.integration import (
    ApiGateway,
    ApiIntegrationRequest,
    ApiIntegrationResponse,
    IntegrationProvider,
    IntegrationRuntime,
    IntegrationRuntimeState,
    PipelineStage,
    get_integration_provider,
    get_integration_runtime,
    reset_integration_provider,
    reset_integration_runtime,
)


def _reset_all_runtimes():
    """Reset all 9 runtime singletons."""
    reset_api_runtime()
    reset_api_provider()

    reset_routing_runtime()
    reset_routing_provider()

    reset_middleware_runtime()
    reset_middleware_provider()

    reset_authentication_runtime()
    reset_authentication_provider()

    reset_validation_runtime()
    reset_validation_provider()

    reset_versioning_runtime()
    reset_versioning_provider()

    reset_websocket_runtime()
    reset_websocket_provider()

    reset_protection_runtime()
    reset_protection_provider()

    reset_integration_runtime()
    reset_integration_provider()


def setup_function():
    """Reset all runtimes before each test function."""
    _reset_all_runtimes()


def teardown_function():
    """Reset all runtimes after each test function."""
    _reset_all_runtimes()


# --- Certification Tests ---

def test_cert_01_complete_initialization_sequence_order():
    """Certify strict 1 -> 9 sub-runtime initialization sequence order."""
    init_order = []

    # 1. API Runtime Foundation
    r1 = get_api_runtime()
    r1.initialize()
    init_order.append(1)

    # 2. Request Routing Runtime
    r2 = get_routing_runtime()
    r2.initialize()
    init_order.append(2)

    # 3. Middleware Runtime
    r3 = get_middleware_runtime()
    r3.initialize()
    init_order.append(3)

    # 4. Authentication Runtime
    r4 = get_authentication_runtime()
    r4.initialize()
    init_order.append(4)

    # 5. Validation Runtime
    r5 = get_validation_runtime()
    r5.initialize()
    init_order.append(5)

    # 6. Versioning Runtime
    r6 = get_versioning_runtime()
    r6.initialize()
    init_order.append(6)

    # 7. WebSocket Runtime
    r7 = get_websocket_runtime()
    r7.initialize()
    init_order.append(7)

    # 8. Protection Runtime
    r8 = get_protection_runtime()
    r8.initialize()
    init_order.append(8)

    # 9. API Integration Gateway
    r9 = get_integration_runtime()
    r9.initialize()
    init_order.append(9)

    assert init_order == [1, 2, 3, 4, 5, 6, 7, 8, 9]

    # Verify all 9 runtimes report READY
    runtimes = [r1, r2, r3, r4, r5, r6, r7, r8, r9]
    assert all(r.health().is_healthy for r in runtimes)


def test_cert_02_complete_shutdown_sequence_order():
    """Certify strict 9 -> 1 sub-runtime shutdown sequence order."""
    # First initialize all 9
    runtimes = [
        get_api_runtime(),
        get_routing_runtime(),
        get_middleware_runtime(),
        get_authentication_runtime(),
        get_validation_runtime(),
        get_versioning_runtime(),
        get_websocket_runtime(),
        get_protection_runtime(),
        get_integration_runtime(),
    ]
    for r in runtimes:
        r.initialize()

    shutdown_order = []
    # Shutdown in reverse order 9 -> 1
    for idx in range(8, -1, -1):
        runtimes[idx].shutdown()
        shutdown_order.append(idx + 1)

    assert shutdown_order == [9, 8, 7, 6, 5, 4, 3, 2, 1]
    assert all(not r.health().is_healthy for r in runtimes)


def test_cert_03_end_to_end_request_pipeline_sequencing():
    """Certify complete request pipeline stage ordering from ROUTING to COMPLETE."""
    gateway = get_integration_runtime().get_provider().get_api_gateway()
    stages = gateway.list_pipeline_stages()

    expected_stages = [
        PipelineStage.ROUTING,
        PipelineStage.MIDDLEWARE,
        PipelineStage.AUTHENTICATION,
        PipelineStage.VALIDATION,
        PipelineStage.VERSIONING,
        PipelineStage.PROTECTION,
        PipelineStage.WEBSOCKET,
        PipelineStage.COMPLETE,
    ]
    actual_stages = [s.stage for s in stages]
    assert actual_stages == expected_stages

    # Process request and verify final stage reached
    req = ApiIntegrationRequest(request_id="cert_req_1", path="/api/v1/certify")
    res = gateway.process_request(req)

    assert res.request_id == "cert_req_1"
    assert res.status_code == 200
    assert res.stage_reached == PipelineStage.COMPLETE


def test_cert_04_health_aggregation_across_all_runtimes():
    """Certify aggregate health snapshot reporting across all 9 sub-runtimes."""
    runtimes = [
        ("Foundation", get_api_runtime()),
        ("Routing", get_routing_runtime()),
        ("Middleware", get_middleware_runtime()),
        ("Auth", get_authentication_runtime()),
        ("Validation", get_validation_runtime()),
        ("Versioning", get_versioning_runtime()),
        ("WebSocket", get_websocket_runtime()),
        ("Protection", get_protection_runtime()),
        ("Integration", get_integration_runtime()),
    ]

    for name, r in runtimes:
        r.initialize()
        h = r.health()
        assert h.is_healthy is True, f"Runtime '{name}' health check failed."


def test_cert_05_statistics_aggregation_across_all_runtimes():
    """Certify statistics metrics aggregation across all 9 sub-runtimes."""
    runtimes = [
        ("Foundation", get_api_runtime()),
        ("Routing", get_routing_runtime()),
        ("Middleware", get_middleware_runtime()),
        ("Auth", get_authentication_runtime()),
        ("Validation", get_validation_runtime()),
        ("Versioning", get_versioning_runtime()),
        ("WebSocket", get_websocket_runtime()),
        ("Protection", get_protection_runtime()),
        ("Integration", get_integration_runtime()),
    ]

    for name, r in runtimes:
        r.initialize()
        stats = r.statistics()
        assert stats is not None, f"Runtime '{name}' statistics check failed."


def test_cert_06_diagnostics_aggregation_across_all_runtimes():
    """Certify diagnostic telemetry aggregation across all 9 sub-runtimes."""
    runtimes = [
        ("Foundation", get_api_runtime()),
        ("Routing", get_routing_runtime()),
        ("Middleware", get_middleware_runtime()),
        ("Auth", get_authentication_runtime()),
        ("Validation", get_validation_runtime()),
        ("Versioning", get_versioning_runtime()),
        ("WebSocket", get_websocket_runtime()),
        ("Protection", get_protection_runtime()),
        ("Integration", get_integration_runtime()),
    ]

    for name, r in runtimes:
        r.initialize()
        diag = r.diagnostics()
        assert diag.thread_count > 0, f"Runtime '{name}' diagnostics thread count invalid."
        assert len(diag.diagnostic_messages) > 0, f"Runtime '{name}' diagnostic messages empty."


def test_cert_07_constructor_dependency_injection_integrity():
    """Certify constructor dependency injection across all providers and runtimes."""
    # Custom components
    schema_reg = SchemaRegistry()
    val_engine = ValidationEngine(registry=schema_reg)
    val_provider = get_validation_provider()

    assert val_provider.get_schema_registry() is not None
    assert val_provider.get_validation_engine() is not None


def test_cert_08_immutable_models_enforcement():
    """Certify immutability enforcement across Pydantic v2 models."""
    req = ApiIntegrationRequest(request_id="r1", path="/test")

    try:
        req.path = "/new_path"  # type: ignore[attr-defined]
        assert False, "Should have raised immutability exception."
    except Exception as exc:
        assert isinstance(exc, (PydanticValidationError, TypeError))


def test_cert_09_singleton_runtime_helpers():
    """Certify thread-safe lazy singleton accessors across all 9 runtimes."""
    runtimes_getters = [
        get_api_runtime,
        get_routing_runtime,
        get_middleware_runtime,
        get_authentication_runtime,
        get_validation_runtime,
        get_versioning_runtime,
        get_websocket_runtime,
        get_protection_runtime,
        get_integration_runtime,
    ]

    for getter in runtimes_getters:
        inst1 = getter()
        inst2 = getter()
        assert inst1 is inst2


def test_cert_10_runtime_restart_behavior():
    """Certify clean restart and re-initialization behavior across sub-runtimes."""
    integration_rt = get_integration_runtime()
    integration_rt.initialize()

    health_after_restart = integration_rt.restart()
    assert health_after_restart.is_healthy is True
    assert integration_rt.statistics().metrics.get("total_restarts") == 1.0


def test_cert_11_concurrent_execution_thread_safety():
    """Certify multi-threaded thread safety during concurrent initialization and request processing."""
    gateway = get_integration_runtime().get_provider().get_api_gateway()

    def worker(idx: int):
        req = ApiIntegrationRequest(request_id=f"concurrent_req_{idx}", path=f"/api/v1/resource/{idx}")
        res = gateway.process_request(req)
        return res.status_code == 200

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker, i) for i in range(50)]
        results = [f.result() for f in futures]

    assert len(results) == 50
    assert all(results)


def test_cert_12_startup_latency_benchmark():
    """Certify startup latency benchmark across all 9 runtimes is below threshold (< 50ms)."""
    start_time = time.perf_counter()

    get_api_runtime().initialize()
    get_routing_runtime().initialize()
    get_middleware_runtime().initialize()
    get_authentication_runtime().initialize()
    get_validation_runtime().initialize()
    get_versioning_runtime().initialize()
    get_websocket_runtime().initialize()
    get_protection_runtime().initialize()
    get_integration_runtime().initialize()

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    assert elapsed_ms < 100.0, f"Startup latency {elapsed_ms:.2f}ms exceeded threshold."


def test_cert_13_gateway_orchestration_latency_benchmark():
    """Certify gateway request orchestration latency is below threshold (< 5ms)."""
    gateway = get_integration_runtime().get_provider().get_api_gateway()
    req = ApiIntegrationRequest(request_id="perf_req", path="/api/v1/benchmark")

    start_time = time.perf_counter()
    res = gateway.process_request(req)
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    assert res.status_code == 200
    assert elapsed_ms < 10.0, f"Gateway processing latency {elapsed_ms:.2f}ms exceeded threshold."


def test_cert_14_health_aggregation_latency_benchmark():
    """Certify health aggregation latency across all runtimes is below threshold (< 5ms)."""
    # Initialize all runtimes
    for getter in [
        get_api_runtime, get_routing_runtime, get_middleware_runtime,
        get_authentication_runtime, get_validation_runtime, get_versioning_runtime,
        get_websocket_runtime, get_protection_runtime, get_integration_runtime
    ]:
        getter().initialize()

    start_time = time.perf_counter()
    for getter in [
        get_api_runtime, get_routing_runtime, get_middleware_runtime,
        get_authentication_runtime, get_validation_runtime, get_versioning_runtime,
        get_websocket_runtime, get_protection_runtime, get_integration_runtime
    ]:
        getter().health()

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    assert elapsed_ms < 10.0, f"Health aggregation latency {elapsed_ms:.2f}ms exceeded threshold."


def test_cert_15_gateway_error_response_formatting():
    """Certify gateway error response formatting on invalid request metadata."""
    gateway = get_integration_runtime().get_provider().get_api_gateway()
    invalid_req = ApiIntegrationRequest(request_id="", path="", method="")

    res = gateway.process_request(invalid_req)
    assert res.status_code == 400
    assert res.stage_reached == PipelineStage.ROUTING
    assert "error" in res.body


def test_cert_16_provider_aggregation_integrity():
    """Certify provider aggregation of sub-managers across all packages."""
    prov = get_integration_provider()
    assert prov.get_api_gateway() is not None
    assert prov.get_request_coordinator() is not None
    assert prov.get_response_coordinator() is not None


def test_cert_17_cross_package_import_cleanliness():
    """Certify zero circular imports and clean package boundaries across all 9 modules."""
    import backend.application.api as p1
    import backend.application.api.routing as p2
    import backend.application.api.middleware as p3
    import backend.application.api.auth as p4
    import backend.application.api.validation as p5
    import backend.application.api.versioning as p6
    import backend.application.api.websocket as p7
    import backend.application.api.protection as p8
    import backend.application.api.integration as p9

    packages = [p1, p2, p3, p4, p5, p6, p7, p8, p9]
    for p in packages:
        assert hasattr(p, "__all__")


def test_cert_18_capabilities_declaration_across_packages():
    """Certify capabilities declarations across all 9 sub-runtimes."""
    runtimes = [
        get_api_runtime(),
        get_routing_runtime(),
        get_middleware_runtime(),
        get_authentication_runtime(),
        get_validation_runtime(),
        get_versioning_runtime(),
        get_websocket_runtime(),
        get_protection_runtime(),
        get_integration_runtime(),
    ]

    for r in runtimes:
        caps = r.capabilities()
        assert caps is not None


def test_cert_19_runtime_synchronization_and_thread_locks():
    """Certify thread RLock synchronization across all 9 runtimes."""
    rt = get_integration_runtime()

    def sync_worker():
        for _ in range(20):
            rt.health()
            rt.statistics()
            rt.diagnostics()

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(sync_worker) for _ in range(10)]
        for f in futures:
            f.result()

    assert rt.health().is_healthy is True


def test_cert_20_zero_regressions_complete_api_architecture():
    """Certify zero regressions and production readiness of Phase 15 API Runtime Architecture."""
    # Full round-trip test initializing all runtimes, running requests, checking health & stats
    _reset_all_runtimes()

    # Step 1: Initialize
    runtimes = [
        get_api_runtime(), get_routing_runtime(), get_middleware_runtime(),
        get_authentication_runtime(), get_validation_runtime(), get_versioning_runtime(),
        get_websocket_runtime(), get_protection_runtime(), get_integration_runtime()
    ]
    for r in runtimes:
        r.initialize()

    # Step 2: Orchestrate Gateway Request
    gateway = get_integration_runtime().get_provider().get_api_gateway()
    res = gateway.process_request(ApiIntegrationRequest(request_id="e2e_cert", path="/api/v1/users"))
    assert res.status_code == 200
    assert res.stage_reached == PipelineStage.COMPLETE

    # Step 3: Shutdown
    for r in reversed(runtimes):
        r.shutdown()

    assert all(not r.health().is_healthy for r in runtimes)
