"""Unit tests for PlanningRuntimeCoordinator (Phase 9.3.6)."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import logging
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from brain.planning import (
    ActionPlanner,
    DependencyResolver,
    ExecutionPlan,
    ExecutionPlanBuilder,
    ExecutionReadiness,
    PlanValidator,
    PlanningRuntimeCoordinator,
    PlanningRuntimeHealth,
    PlanningRuntimeStats,
    PlanningRuntimeStatus,
    RiskAnalyzer,
    RiskLevel,
    get_planning_runtime,
    reset_planning_runtime,
)
from brain.reasoning import (
    GoalExtractionResult,
    GoalType,
    ReasoningContext,
    ReasoningContextBuilder,
)


@pytest.fixture
def runtime() -> PlanningRuntimeCoordinator:
    """Fixture providing an initialized PlanningRuntimeCoordinator instance."""
    rt = PlanningRuntimeCoordinator()
    rt.initialize()
    yield rt
    rt.shutdown()


def test_initialization(runtime: PlanningRuntimeCoordinator) -> None:
    """Verifies runtime initialization and status transition to READY."""
    assert runtime.status == PlanningRuntimeStatus.READY
    components = runtime.list_components()
    assert len(components) == 5
    assert "ActionPlanner" in components
    assert "ExecutionPlanBuilder" in components


def test_shutdown(runtime: PlanningRuntimeCoordinator) -> None:
    """Verifies runtime shutdown transition and resource cleanup."""
    res = runtime.shutdown()
    assert res is True
    assert runtime.status == PlanningRuntimeStatus.SHUTDOWN


def test_health_checks(runtime: PlanningRuntimeCoordinator) -> None:
    """Verifies health check reporting components and healthy flag."""
    health = runtime.health_check()
    assert isinstance(health, PlanningRuntimeHealth)
    assert health.healthy is True
    assert health.status == PlanningRuntimeStatus.READY
    assert len(health.components) == 5


def test_runtime_status_transitions(runtime: PlanningRuntimeCoordinator) -> None:
    """Verifies lifecycle status transitions."""
    assert runtime.status == PlanningRuntimeStatus.READY
    runtime.shutdown()
    assert runtime.status == PlanningRuntimeStatus.SHUTDOWN
    runtime.initialize()
    assert runtime.status == PlanningRuntimeStatus.READY


def test_planning_request_processing(runtime: PlanningRuntimeCoordinator) -> None:
    """Verifies end-to-end 5-stage planning pipeline processing for a ReasoningContext."""
    rcb = ReasoningContextBuilder()
    ctx = rcb.build_context("search report.pdf", goal_result=GoalExtractionResult(goal_type=GoalType.SEARCH_FILES))

    exec_plan = runtime.process_reasoning_context(ctx)

    assert isinstance(exec_plan, ExecutionPlan)
    assert exec_plan.request == "search report.pdf"
    assert exec_plan.readiness == ExecutionReadiness.READY


def test_statistics_updates(runtime: PlanningRuntimeCoordinator) -> None:
    """Verifies stats tracking (plans processed, plans built, average latency ms)."""
    rcb = ReasoningContextBuilder()
    ctx = rcb.build_context("locate data", goal_result=GoalExtractionResult(goal_type=GoalType.SEARCH_FILES))

    runtime.process_reasoning_context(ctx)
    runtime.process_reasoning_context(ctx)

    stats = runtime.get_statistics()
    assert isinstance(stats, PlanningRuntimeStats)
    assert stats.plans_processed == 2
    assert stats.plans_built == 2
    assert stats.average_runtime_ms >= 0.0
    assert stats.last_request_timestamp is not None


def test_immutable_outputs(runtime: PlanningRuntimeCoordinator) -> None:
    """Verifies health and stats objects are immutable snapshots."""
    health = runtime.health_check()
    with pytest.raises((TypeError, ValidationError)):
        health.healthy = False

    stats = runtime.get_statistics()
    with pytest.raises((TypeError, ValidationError)):
        stats.plans_processed = 999


def test_thread_safety(runtime: PlanningRuntimeCoordinator) -> None:
    """Verifies thread safety during concurrent health checks and stats requests."""
    rcb = ReasoningContextBuilder()
    ctx = rcb.build_context("test task")

    def worker() -> None:
        runtime.process_reasoning_context(ctx)
        runtime.health_check()
        runtime.get_statistics()

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker) for _ in range(30)]
        for f in futures:
            f.result()

    stats = runtime.get_statistics()
    assert stats.plans_processed == 30


def test_concurrent_processing(runtime: PlanningRuntimeCoordinator) -> None:
    """Verifies thread-safe concurrent plan creation."""
    rcb = ReasoningContextBuilder()
    ctx = rcb.build_context("search logs", goal_result=GoalExtractionResult(goal_type=GoalType.SEARCH_FILES))

    with ThreadPoolExecutor(max_workers=5) as executor:
        plans = list(executor.map(lambda _: runtime.process_reasoning_context(ctx), range(10)))

    assert len(plans) == 10
    assert all(p.readiness == ExecutionReadiness.READY for p in plans)


def test_singleton_compatibility() -> None:
    """Verifies get_planning_runtime and reset_planning_runtime singleton behavior."""
    reset_planning_runtime()
    rt1 = get_planning_runtime()
    rt2 = get_planning_runtime()
    assert rt1 is rt2

    reset_planning_runtime()
    rt3 = get_planning_runtime()
    assert rt3 is not rt1
    reset_planning_runtime()


def test_invalid_requests(runtime: PlanningRuntimeCoordinator) -> None:
    """Verifies non-ReasoningContext input maps cleanly without raising uncaught exceptions."""
    exec_plan = runtime.process_reasoning_context("invalid_string_context")  # type: ignore
    assert isinstance(exec_plan, ExecutionPlan)


def test_empty_reasoning_contexts(runtime: PlanningRuntimeCoordinator) -> None:
    """Verifies empty ReasoningContext processing."""
    rcb = ReasoningContextBuilder()
    ctx = rcb.build_context("")

    exec_plan = runtime.process_reasoning_context(ctx)
    assert isinstance(exec_plan, ExecutionPlan)


def test_configuration_injection() -> None:
    """Verifies custom component dependency injection into PlanningRuntimeCoordinator."""
    ap = ActionPlanner()
    pv = PlanValidator()
    dr = DependencyResolver()
    ra = RiskAnalyzer()
    epb = ExecutionPlanBuilder()

    coordinator = PlanningRuntimeCoordinator(
        action_planner=ap,
        plan_validator=pv,
        dependency_resolver=dr,
        risk_analyzer=ra,
        execution_plan_builder=epb,
    )
    coordinator.initialize()

    assert coordinator.action_planner is ap
    assert coordinator.execution_plan_builder is epb
    coordinator.shutdown()


def test_component_availability(runtime: PlanningRuntimeCoordinator) -> None:
    """Verifies list_components returns all 5 planning component names."""
    components = runtime.list_components()
    assert components == [
        "ActionPlanner",
        "PlanValidator",
        "DependencyResolver",
        "RiskAnalyzer",
        "ExecutionPlanBuilder",
    ]


def test_diagnostics(runtime: PlanningRuntimeCoordinator) -> None:
    """Verifies health check metadata contains thread_safety information."""
    health = runtime.health_check()
    assert health.metadata.get("thread_safety") == "PROTECTED"


def test_clear(runtime: PlanningRuntimeCoordinator) -> None:
    """Verifies clear() resets statistics to initial state."""
    rcb = ReasoningContextBuilder()
    ctx = rcb.build_context("temp request")
    runtime.process_reasoning_context(ctx)

    assert runtime.get_statistics().plans_processed == 1
    runtime.clear()
    assert runtime.get_statistics().plans_processed == 0


def test_logging(caplog: pytest.LogCaptureFixture) -> None:
    """Verifies required event log outputs."""
    rcb = ReasoningContextBuilder()
    ctx = rcb.build_context("log test")
    rt = PlanningRuntimeCoordinator()

    with caplog.at_level(logging.INFO):
        rt.initialize()
        rt.process_reasoning_context(ctx)
        rt.health_check()
        rt.clear()
        rt.shutdown()

    assert "Runtime Initialized" in caplog.text
    assert "Planning Request Processed" in caplog.text
    assert "Health Check" in caplog.text
    assert "Runtime Cleared" in caplog.text
    assert "Runtime Shutdown" in caplog.text


def test_integration_with_action_planner(runtime: PlanningRuntimeCoordinator) -> None:
    """Verifies pipeline stage 1: ActionPlanner step generation."""
    rcb = ReasoningContextBuilder()
    ctx = rcb.build_context("locate file.txt", goal_result=GoalExtractionResult(goal_type=GoalType.SEARCH_FILES))

    exec_plan = runtime.process_reasoning_context(ctx)
    assert len(exec_plan.action_plan.steps) >= 1


def test_integration_with_plan_validator(runtime: PlanningRuntimeCoordinator) -> None:
    """Verifies pipeline stage 2: PlanValidator validation result attachment."""
    rcb = ReasoningContextBuilder()
    ctx = rcb.build_context("search files")

    exec_plan = runtime.process_reasoning_context(ctx)
    assert exec_plan.validation_result.valid is True


def test_integration_with_dependency_resolver(runtime: PlanningRuntimeCoordinator) -> None:
    """Verifies pipeline stage 3: DependencyResolver execution_order calculation."""
    rcb = ReasoningContextBuilder()
    ctx = rcb.build_context("move document.pdf to Archive", goal_result=GoalExtractionResult(goal_type=GoalType.MOVE_FILES))

    exec_plan = runtime.process_reasoning_context(ctx)
    assert len(exec_plan.execution_order) == 3


def test_integration_with_risk_analyzer(runtime: PlanningRuntimeCoordinator) -> None:
    """Verifies pipeline stage 4: RiskAnalyzer risk classification."""
    rcb = ReasoningContextBuilder()
    ctx = rcb.build_context("delete temp folder", goal_result=GoalExtractionResult(goal_type=GoalType.DELETE_FOLDER))

    exec_plan = runtime.process_reasoning_context(ctx)
    assert exec_plan.risk_result.overall_risk == RiskLevel.CRITICAL
    assert exec_plan.readiness == ExecutionReadiness.BLOCKED


def test_integration_with_execution_plan_builder(runtime: PlanningRuntimeCoordinator) -> None:
    """Verifies pipeline stage 5: ExecutionPlanBuilder final snapshot construction."""
    rcb = ReasoningContextBuilder()
    ctx = rcb.build_context("create new directory", goal_result=GoalExtractionResult(goal_type=GoalType.CREATE_FOLDER))

    exec_plan = runtime.process_reasoning_context(ctx)
    assert exec_plan.current_stage == ExecutionPlanBuilder().build_execution_plan().current_stage


def test_backward_compatibility() -> None:
    """Verifies backward compatibility with existing planning exports."""
    from brain.planning import (
        PlanningRuntimeCoordinator,
        PlanningRuntimeHealth,
        PlanningRuntimeStats,
        PlanningRuntimeStatus,
        get_planning_runtime,
        reset_planning_runtime,
    )

    rt = get_planning_runtime()
    assert rt is not None
    reset_planning_runtime()


def test_regression_validation(runtime: PlanningRuntimeCoordinator) -> None:
    """Verifies multi-request pipeline stability."""
    rcb = ReasoningContextBuilder()
    requests = ["search report", "copy image.png", "open document.docx"]

    plans = [runtime.process_reasoning_context(rcb.build_context(req)) for req in requests]
    assert len(plans) == 3
    assert runtime.get_statistics().plans_processed == 3
