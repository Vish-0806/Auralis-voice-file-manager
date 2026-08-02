"""Unit test suite for Phase 12.3 — Command Execution Orchestrator.

Covers:
- Execution models, enums, defaults, and immutability
- Subsystem exceptions hierarchy
- ExecutionCoordinator mode and priority evaluation
- ExecutionRouter stage routing to mocked subsystem runtimes
- ExecutionTracker stage progression, duration tracking, and statistics
- ExecutionOrchestrator multi-stage execution pipeline (success and failure cases)
- ExecutionProvider aggregation, diagnostics, and health reporting
- ExecutionRuntime singleton lifecycle, initialization, shutdown, and thread safety under concurrency
- Mock integrations for Intent Resolution, Planning, Security, Execution Engine, and OS runtimes
"""

from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from brain.execution.orchestrator import (
    ExecutionCoordinator,
    ExecutionContext,
    ExecutionHealth,
    ExecutionMode,
    ExecutionOrchestrator,
    ExecutionOrchestratorException,
    ExecutionPreparationError,
    ExecutionPriority,
    ExecutionProvider,

    ExecutionRequest,
    ExecutionResult,
    ExecutionRouter,
    ExecutionRuntime,
    ExecutionStage,
    ExecutionStageType,
    ExecutionState,
    ExecutionStatistics,
    ExecutionTracker,
    OrchestrationStatus,
    OrchestratorRuntimeStatus,
    get_orchestrator_runtime,
    reset_orchestrator_runtime,
)


@pytest.fixture(autouse=True)
def cleanup_runtime() -> None:
    """Fixture resetting global runtime before and after each test."""
    reset_orchestrator_runtime()
    yield
    reset_orchestrator_runtime()


def test_orchestrator_models_defaults_and_immutability() -> None:
    """Verifies orchestrator model default values and Pydantic v2 immutability."""
    req = ExecutionRequest(
        raw_prompt="Open Chrome and search report",
        mode=ExecutionMode.DIRECT,
        priority=ExecutionPriority.NORMAL,
    )
    assert req.raw_prompt == "Open Chrome and search report"
    assert req.mode == ExecutionMode.DIRECT

    with pytest.raises((TypeError, ValidationError)):
        req.raw_prompt = "Modified prompt"  # type: ignore

    stage = ExecutionStage(
        stage_type=ExecutionStageType.INTENT_RESOLUTION,
        status=OrchestrationStatus.SUCCESS,
        duration_ms=12.5,
    )
    assert stage.stage_type == ExecutionStageType.INTENT_RESOLUTION

    with pytest.raises((TypeError, ValidationError)):
        stage.status = OrchestrationStatus.FAILED  # type: ignore


def test_orchestrator_exceptions_hierarchy() -> None:
    """Verifies exception inheritance hierarchy."""
    exc = ExecutionPreparationError("Preparation failed")
    assert isinstance(exc, ExecutionOrchestratorException)


def test_execution_coordinator_preparation() -> None:
    """Verifies coordinator mode determination and priority assignment."""
    coordinator = ExecutionCoordinator()

    # Direct mode
    ctx1 = coordinator.prepare_execution("Open Spotify app")
    assert ctx1.request.mode == ExecutionMode.DIRECT
    assert ctx1.request.priority == ExecutionPriority.NORMAL

    # Planned mode
    ctx2 = coordinator.prepare_execution("Build a workflow sequence for file cleanup")
    assert ctx2.request.mode == ExecutionMode.PLANNED
    assert ctx2.request.priority == ExecutionPriority.HIGH

    # Critical mode
    ctx3 = coordinator.prepare_execution("Shutdown system power")
    assert ctx3.request.mode == ExecutionMode.CRITICAL
    assert ctx3.request.priority == ExecutionPriority.CRITICAL

    # Invalid input
    with pytest.raises(ExecutionPreparationError):
        coordinator.prepare_execution(None)


def test_execution_router_with_mock_runtimes() -> None:
    """Verifies stage routing across mocked subsystem runtimes."""
    mock_intent_runtime = MagicMock()
    mock_intent_runtime.process_intent.return_value = {"intent": "OPEN_APP"}

    mock_planning_runtime = MagicMock()
    mock_planning_runtime.create_plan.return_value = {"steps": ["step1"]}

    mock_security_runtime = MagicMock()
    mock_security_runtime.evaluate.return_value = {"allowed": True}

    mock_os_runtime = MagicMock()
    mock_os_runtime.execute_command.return_value = {"status": "SUCCESS"}

    router = ExecutionRouter(
        intent_runtime=mock_intent_runtime,
        planning_runtime=mock_planning_runtime,
        security_runtime=mock_security_runtime,
        os_runtime=mock_os_runtime,
    )

    coordinator = ExecutionCoordinator()
    ctx = coordinator.prepare_execution("Build workflow for PDF search")

    # Route Intent Resolution
    stage1 = router.route_stage(ExecutionStageType.INTENT_RESOLUTION, ctx)
    assert stage1.status == OrchestrationStatus.SUCCESS
    assert "resolution" in stage1.output

    # Route Planning
    stage2 = router.route_stage(ExecutionStageType.PLANNING, ctx)
    assert stage2.status == OrchestrationStatus.SUCCESS

    # Route Security
    stage3 = router.route_stage(ExecutionStageType.SECURITY_REVIEW, ctx)
    assert stage3.status == OrchestrationStatus.SUCCESS

    # Route OS Execution
    stage4 = router.route_stage(ExecutionStageType.OS_EXECUTION, ctx)
    assert stage4.status == OrchestrationStatus.SUCCESS


def test_execution_tracker_recording_and_statistics() -> None:
    """Verifies tracker recording of stages, completion summaries, and statistics."""
    tracker = ExecutionTracker()
    coordinator = ExecutionCoordinator()
    ctx = coordinator.prepare_execution("Test command")

    exec_id = tracker.start_execution(ctx)
    assert tracker.get_statistics().active_orchestrations == 1

    stage = ExecutionStage(
        stage_type=ExecutionStageType.INTENT_RESOLUTION,
        status=OrchestrationStatus.SUCCESS,
        duration_ms=5.0,
    )
    tracker.record_stage(exec_id, stage)

    result = ExecutionResult(
        execution_id=exec_id,
        status=OrchestrationStatus.SUCCESS,
        state=ExecutionState.COMPLETED,
        stages=[stage],
        execution_time_ms=15.0,
    )

    summary = tracker.complete_execution(exec_id, result)
    assert summary.status == OrchestrationStatus.SUCCESS
    assert summary.completed_stages == 1

    stats = tracker.get_statistics()
    assert isinstance(stats, ExecutionStatistics)
    assert stats.total_orchestrations == 1
    assert stats.successful_count == 1
    assert stats.active_orchestrations == 0


def test_execution_orchestrator_pipeline_success() -> None:
    """Verifies multi-stage orchestration pipeline success flow."""
    orchestrator = ExecutionOrchestrator()

    res = orchestrator.orchestrate("Search for report.pdf")
    assert isinstance(res, ExecutionResult)
    assert res.status == OrchestrationStatus.SUCCESS
    assert res.state == ExecutionState.COMPLETED
    assert len(res.stages) == 4  # INTENT_RESOLUTION, SECURITY_REVIEW, OS_EXECUTION, RESPONSE_SYNTHESIS
    assert res.execution_time_ms >= 0.0


def test_execution_orchestrator_pipeline_failure_handling() -> None:
    """Verifies orchestration pipeline failure handling when a stage fails."""
    mock_os_runtime = MagicMock()
    mock_os_runtime.execute_command.side_effect = RuntimeError("OS execution binary missing")

    router = ExecutionRouter(os_runtime=mock_os_runtime)
    orchestrator = ExecutionOrchestrator(router=router)

    res = orchestrator.orchestrate("Run missing command")
    assert res.status == OrchestrationStatus.FAILED
    assert res.state == ExecutionState.FAILED
    assert "OS execution binary missing" in res.error


def test_execution_provider_and_health_check() -> None:
    """Verifies ExecutionProvider end-to-end processing, health check, and clear methods."""
    provider = ExecutionProvider()

    res = provider.execute("Open Calculator")
    assert res.status == OrchestrationStatus.SUCCESS

    health = provider.health_check()
    assert isinstance(health, ExecutionHealth)
    assert health.healthy is True
    assert len(health.components) == 4

    stats = provider.get_statistics()
    assert stats.total_orchestrations == 1

    provider.clear()
    assert provider.get_statistics().total_orchestrations == 0


def test_execution_runtime_lifecycle_and_singleton() -> None:
    """Verifies ExecutionRuntime initialization, shutdown, processing, and singleton accessors."""
    rt = get_orchestrator_runtime()
    assert rt.status == OrchestratorRuntimeStatus.READY

    rt2 = get_orchestrator_runtime()
    assert rt is rt2

    res = rt.process_command("Find document.docx")
    assert res.status == OrchestrationStatus.SUCCESS

    health = rt.health_check()
    assert health.healthy is True

    stats = rt.get_statistics()
    assert stats.total_orchestrations == 1

    rt.clear()
    assert rt.get_statistics().total_orchestrations == 0

    assert rt.shutdown() is True
    assert rt.status == OrchestratorRuntimeStatus.SHUTDOWN


def test_execution_runtime_thread_safety() -> None:
    """Verifies thread-safe orchestration across concurrent worker threads."""
    rt = get_orchestrator_runtime()
    prompts = [
        "Open Chrome",
        "Create folder Backup",
        "Mute audio",
        "Search files",
        "Take screenshot",
    ] * 4

    def worker(cmd: str) -> OrchestrationStatus:
        res = rt.process_command(cmd)
        return res.status

    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(worker, prompts))

    assert len(results) == 20
    assert all(status == OrchestrationStatus.SUCCESS for status in results)

    stats = rt.get_statistics()
    assert stats.total_orchestrations == 20
    assert stats.successful_count == 20
