"""Unit tests for Phase 13.9 – Assistant Runtime Integration Layer."""

from concurrent.futures import ThreadPoolExecutor
import threading
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from brain.assistant.integration import (
    AssistantCoordinator,
    AssistantExecutionSummary,
    AssistantIntegrationCapabilities,
    AssistantIntegrationContext,
    AssistantIntegrationException,
    AssistantIntegrationHealth,
    AssistantIntegrationProvider,
    AssistantIntegrationRequest,
    AssistantIntegrationResponse,
    AssistantIntegrationRuntime,
    AssistantIntegrationSession,
    AssistantIntegrationState,
    AssistantIntegrationStatistics,
    AssistantMode,
    AssistantRuntimeSnapshot,
    HealthAggregator,
    IAssistantIntegrationProvider,
    IntegrationStage,
    IntegrationState,
    IntegrationStatus,
    PipelineCoordinator,
    PipelineState,
    RuntimeRegistry,
    get_assistant_integration_runtime,
    reset_assistant_integration_runtime,
)


@pytest.fixture(autouse=True)
def cleanup_singleton():
    """Ensure clean singleton state before and after each test."""
    reset_assistant_integration_runtime()
    yield
    reset_assistant_integration_runtime()


# ---------------------------------------------------------------------------
# 1. Immutable Domain Models
# ---------------------------------------------------------------------------

def test_immutable_models() -> None:
    """Verify all 10 Pydantic v2 models are frozen and immutable."""
    summary = AssistantExecutionSummary()
    snapshot = AssistantRuntimeSnapshot()
    context = AssistantIntegrationContext()
    req = AssistantIntegrationRequest()
    resp = AssistantIntegrationResponse()
    state = AssistantIntegrationState()
    session = AssistantIntegrationSession()
    caps = AssistantIntegrationCapabilities()
    stats = AssistantIntegrationStatistics()
    health = AssistantIntegrationHealth()

    models = [summary, snapshot, context, req, resp, state, session, caps, stats, health]
    for m in models:
        with pytest.raises((ValidationError, TypeError, AttributeError)):
            m.status = IntegrationStatus.FAILED  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# 2. Runtime Registration & Capability Discovery
# ---------------------------------------------------------------------------

def test_runtime_registration_and_lookup() -> None:
    """Verify RuntimeRegistry registers runtimes, looks them up, and checks availability."""
    reg = RuntimeRegistry()

    class DummyRuntime:
        is_initialized = True

    dummy = DummyRuntime()
    reg.register_runtime("dummy_rt", dummy, version="1.2.0", capabilities=["cap1", "cap2"])

    assert reg.get_runtime("dummy_rt") is dummy
    assert reg.is_available("dummy_rt") is True

    snapshots = reg.list_snapshots()
    assert len(snapshots) == 1
    assert snapshots[0].runtime_name == "dummy_rt"
    assert snapshots[0].version == "1.2.0"
    assert "cap1" in snapshots[0].capabilities


# ---------------------------------------------------------------------------
# 3. Pipeline Stage Ordering & Summary Collection
# ---------------------------------------------------------------------------

def test_pipeline_coordinator_stage_ordering() -> None:
    """Verify PipelineCoordinator executes pipeline stages in correct sequence."""
    pipeline = PipelineCoordinator()
    reg = RuntimeRegistry()
    req = AssistantIntegrationRequest(user_prompt="test pipeline")

    summaries = pipeline.execute_pipeline(req, reg)

    assert len(summaries) == 8  # Conversation -> Dialogue -> Decision -> Memory -> Execution -> Response -> Voice -> Proactive
    stages = [s.stage for s in summaries]
    assert stages[0] == IntegrationStage.CONVERSATION
    assert stages[1] == IntegrationStage.DIALOGUE
    assert stages[2] == IntegrationStage.DECISION
    assert stages[3] == IntegrationStage.MEMORY
    assert stages[4] == IntegrationStage.EXECUTION
    assert stages[5] == IntegrationStage.RESPONSE
    assert stages[6] == IntegrationStage.VOICE
    assert stages[7] == IntegrationStage.PROACTIVE


# ---------------------------------------------------------------------------
# 4. Health Aggregation Across Runtimes
# ---------------------------------------------------------------------------

def test_health_aggregation() -> None:
    """Verify HealthAggregator aggregates diagnostic reports and calculates availability percentage."""
    agg = HealthAggregator()
    reg = RuntimeRegistry()

    health = agg.aggregate_health(reg)
    assert isinstance(health, AssistantIntegrationHealth)
    assert health.availability_percentage >= 0.0
    assert len(health.subsystem_health) == 12  # All 12 sub-runtimes inspected


# ---------------------------------------------------------------------------
# 5. Coordinator Integration Request Handling
# ---------------------------------------------------------------------------

def test_assistant_coordinator_handling() -> None:
    """Verify AssistantCoordinator synthesizes unified AssistantIntegrationResponse."""
    coord = AssistantCoordinator()
    reg = RuntimeRegistry()
    pipeline = PipelineCoordinator()

    req = AssistantIntegrationRequest(user_prompt="organize files")
    response = coord.handle_request(req, reg, pipeline)

    assert isinstance(response, AssistantIntegrationResponse)
    assert response.status == IntegrationStatus.SUCCESS
    assert response.request_id == req.request_id
    assert "organize files" in response.assistant_reply
    assert len(response.execution_summaries) == 8


# ---------------------------------------------------------------------------
# 6. Statistics, Capabilities & Diagnostics
# ---------------------------------------------------------------------------

def test_statistics_capabilities_and_health() -> None:
    """Verify AssistantIntegrationProvider exposes health, capabilities, and metrics statistics."""
    runtime = get_assistant_integration_runtime()
    provider = runtime.get_provider()
    assert isinstance(provider, AssistantIntegrationProvider)

    req = AssistantIntegrationRequest(user_prompt="test request")
    _ = provider.handle_request(req)

    stats = runtime.get_statistics()
    assert stats.total_requests_handled == 1
    assert stats.successful_requests == 1
    assert stats.pipeline_executions == 1

    health = runtime.get_health()
    assert health.healthy is True

    caps = runtime.get_capabilities()
    assert caps.supports_full_pipeline is True
    assert len(caps.available_runtimes) >= 1


# ---------------------------------------------------------------------------
# 7. Singleton Identity & Restart Mechanics
# ---------------------------------------------------------------------------

def test_singleton_identity_and_restart() -> None:
    """Verify get_assistant_integration_runtime singleton identity and restart() behavior."""
    rt1 = get_assistant_integration_runtime()
    rt2 = get_assistant_integration_runtime()
    assert rt1 is rt2
    assert rt1.is_initialized is True

    rt1.restart()
    assert rt1.is_initialized is True

    reset_assistant_integration_runtime()
    rt3 = get_assistant_integration_runtime()
    assert rt3 is not rt1


# ---------------------------------------------------------------------------
# 8. Concurrent Execution with ThreadPoolExecutor
# ---------------------------------------------------------------------------

def test_concurrent_execution_thread_pool() -> None:
    """Verify concurrent request processing using ThreadPoolExecutor without race conditions."""
    runtime = get_assistant_integration_runtime()
    provider = runtime.get_provider()
    assert isinstance(provider, AssistantIntegrationProvider)

    def worker(idx: int) -> bool:
        req = AssistantIntegrationRequest(user_prompt=f"Worker request {idx}")
        res = provider.handle_request(req)
        return res.status == IntegrationStatus.SUCCESS

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(worker, i) for i in range(20)]
        results = [f.result() for f in futures]

    assert all(results)
    stats = runtime.get_statistics()
    assert stats.total_requests_handled == 20
    assert stats.successful_requests == 20


# ---------------------------------------------------------------------------
# 9. Dependency Injection & Backward Compatibility
# ---------------------------------------------------------------------------

def test_dependency_injection_and_compatibility() -> None:
    """Verify constructor dependency injection and backward compatibility with all Phases 9–13.8."""
    from brain.assistant import get_assistant_runtime
    from brain.assistant.conversation import get_conversation_runtime
    from brain.assistant.dialogue import get_dialogue_runtime
    from brain.assistant.memory import get_assistant_memory_runtime
    from brain.assistant.proactive import get_proactive_runtime
    from brain.assistant.reasoning import get_decision_runtime
    from brain.assistant.response import get_response_runtime
    from brain.assistant.voice import get_voice_runtime

    ast_rt = get_assistant_runtime()
    conv_rt = get_conversation_runtime()
    dial_rt = get_dialogue_runtime()
    dec_rt = get_decision_runtime()
    mem_rt = get_assistant_memory_runtime()
    resp_rt = get_response_runtime()
    voice_rt = get_voice_runtime()
    proactive_rt = get_proactive_runtime()

    assert ast_rt.is_initialized is True
    assert conv_rt.is_initialized is True
    assert dial_rt.is_initialized is True
    assert dec_rt.is_initialized is True
    assert mem_rt.is_initialized is True
    assert resp_rt.is_initialized is True
    assert voice_rt.is_initialized is True
    assert proactive_rt.is_initialized is True

    custom_reg = RuntimeRegistry()
    custom_pipeline = PipelineCoordinator()
    custom_coord = AssistantCoordinator()
    custom_health = HealthAggregator()

    provider = AssistantIntegrationProvider(
        registry=custom_reg,
        pipeline_coordinator=custom_pipeline,
        assistant_coordinator=custom_coord,
        health_aggregator=custom_health,
    )

    integration_rt = AssistantIntegrationRuntime(provider=provider)
    integration_rt.initialize()
    assert integration_rt.is_initialized is True
