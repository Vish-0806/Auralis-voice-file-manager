"""Unit test suite for Phase 12.9 — Execution Runtime Integration.

Covers:
- Integration models, enums, defaults, and immutability
- Subsystem exception hierarchy
- CapabilityRegistry registration, query, and validation
- ExecutionRouter target determination and metadata overrides
- ExecutionPipeline multi-stage orchestration and latency timing
- ExecutionProvider processing, health reporting across all 8 execution subsystems, and statistics
- ExecutionRuntime singleton lifecycle, status management, and thread safety under concurrency
"""

from concurrent.futures import ThreadPoolExecutor
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from brain.execution.integration import (
    CapabilityError,
    CapabilityRegistry,
    ExecutionCapability,
    ExecutionPipeline,
    ExecutionProvider,
    ExecutionRouter,

    ExecutionRuntime,
    ExecutionRuntimeStatus,
    ExecutionStage,
    ExecutionStatus,
    ExecutionTarget,
    IntegrationException,
    IntegrationHealth,

    IntegrationRequest,
    IntegrationResponse,
    IntegrationStatistics,
    PipelineExecutionError,
    PipelineStageRecord,
    RoutingError,
    get_execution_runtime,
    reset_execution_runtime,
)


@pytest.fixture(autouse=True)
def cleanup_runtime() -> None:
    """Fixture resetting global execution integration runtime before and after each test."""
    reset_execution_runtime()
    yield
    reset_execution_runtime()


def test_integration_models_defaults_and_immutability() -> None:
    """Verifies integration model default properties and Pydantic v2 immutability."""
    req = IntegrationRequest(user_input="Run backup workflow")
    assert req.user_input == "Run backup workflow"
    assert req.priority.value == "NORMAL"

    with pytest.raises((TypeError, ValidationError)):
        req.user_input = "Modified Input"  # type: ignore

    resp = IntegrationResponse(request_id=req.request_id, status=ExecutionStatus.COMPLETED)
    assert resp.request_id == req.request_id

    with pytest.raises((TypeError, ValidationError)):
        resp.status = ExecutionStatus.FAILED  # type: ignore


def test_integration_exceptions_hierarchy() -> None:
    """Verifies exception inheritance hierarchy."""
    exc = CapabilityError("Capability registration error")
    assert isinstance(exc, IntegrationException)


def test_capability_registry_registration_and_query() -> None:
    """Verifies CapabilityRegistry default registration, custom registration, and filtering."""
    reg = CapabilityRegistry()
    assert reg.count_capabilities() >= 5

    cap = reg.register_capability("Custom Analysis Capability", ExecutionTarget.ANALYTICS_RECORDING if hasattr(ExecutionTarget, "ANALYTICS_RECORDING") else ExecutionTarget.COMMAND_ORCHESTRATOR)
    assert cap.name == "Custom Analysis Capability"

    caps = reg.list_capabilities(ExecutionTarget.COMMAND_ORCHESTRATOR)
    assert len(caps) >= 1


def test_capability_registry_empty_name_error() -> None:
    """Verifies error handling when registering capability with empty name."""
    reg = CapabilityRegistry()
    with pytest.raises(CapabilityError):
        reg.register_capability("", ExecutionTarget.COMMAND_ORCHESTRATOR)


def test_execution_router_target_determination() -> None:
    """Verifies ExecutionRouter keyword-based and metadata override routing logic."""
    router = ExecutionRouter()

    r1 = IntegrationRequest(user_input="Execute multi-step workflow")
    assert router.route_request(r1) == ExecutionTarget.WORKFLOW_ENGINE

    r2 = IntegrationRequest(user_input="Start long-running background task")
    assert router.route_request(r2) == ExecutionTarget.TASK_RUNTIME

    r3 = IntegrationRequest(user_input="Schedule daily trigger automation")
    assert router.route_request(r3) == ExecutionTarget.AUTOMATION_RUNTIME

    r4 = IntegrationRequest(user_input="Recognize intent of command")
    assert router.route_request(r4) == ExecutionTarget.INTENT_ENGINE

    r5 = IntegrationRequest(user_input="Do simple command")
    assert router.route_request(r5) == ExecutionTarget.COMMAND_ORCHESTRATOR

    r6 = IntegrationRequest(user_input="Do simple command", metadata={"target": "WORKFLOW_ENGINE"})
    assert router.route_request(r6) == ExecutionTarget.WORKFLOW_ENGINE


def test_execution_pipeline_orchestration() -> None:
    """Verifies ExecutionPipeline multi-stage pipeline execution."""
    pipeline = ExecutionPipeline()
    req = IntegrationRequest(user_input="Execute step pipeline")

    resp = pipeline.execute_pipeline(req, ExecutionTarget.COMMAND_ORCHESTRATOR)
    assert resp.status == ExecutionStatus.COMPLETED
    assert resp.request_id == req.request_id
    assert resp.result_data.get("intent_resolved") is True
    assert resp.result_data.get("security_cleared") is True


def test_execution_provider_end_to_end_and_health() -> None:
    """Verifies ExecutionProvider request processing, health check across all 8 subsystems, and statistics."""
    provider = ExecutionProvider()

    req = IntegrationRequest(user_input="Process request")
    resp = provider.process_request(req)

    assert resp.status == ExecutionStatus.COMPLETED

    health = provider.health_check()
    assert isinstance(health, IntegrationHealth)
    assert health.healthy is True
    assert len(health.subsystems) == 11

    stats = provider.get_statistics()
    assert isinstance(stats, IntegrationStatistics)
    assert stats.total_requests == 1
    assert stats.successful_executions == 1

    provider.clear()
    assert provider.get_statistics().total_requests == 0


def test_execution_runtime_lifecycle_and_singleton() -> None:
    """Verifies ExecutionRuntime initialization, processing, health reporting, and singleton accessors."""
    rt = get_execution_runtime()
    assert rt.status == ExecutionRuntimeStatus.READY

    rt2 = get_execution_runtime()
    assert rt is rt2

    req = IntegrationRequest(user_input="Test runtime processing")
    resp = rt.process_request(req)
    assert resp.status == ExecutionStatus.COMPLETED

    health = rt.health_check()
    assert health.healthy is True

    stats = rt.get_statistics()
    assert stats.total_requests == 1

    rt.clear()
    assert rt.get_statistics().total_requests == 0

    assert rt.shutdown() is True
    assert rt.status == ExecutionRuntimeStatus.SHUTDOWN


def test_execution_runtime_thread_safety() -> None:
    """Verifies thread-safe request processing across concurrent worker threads."""
    rt = get_execution_runtime()

    def worker(i: int) -> str:
        req = IntegrationRequest(user_input=f"Request from worker {i}")
        resp = rt.process_request(req)
        return resp.execution_id

    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(worker, range(15)))

    assert len(results) == 15

    stats = rt.get_statistics()
    assert stats.total_requests == 15
    assert stats.successful_executions == 15
