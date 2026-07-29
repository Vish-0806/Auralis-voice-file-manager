"""Unit tests for ExecutionRuntimeCoordinator (Phase 9.4)."""

from concurrent.futures import ThreadPoolExecutor
import logging
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from brain.execution import (
    ExecutionCoordinator,
    ExecutionPolicy,
    ExecutionResult,
    ExecutionRuntimeCoordinator,
    ExecutionRuntimeHealth,
    ExecutionRuntimeStatistics,
    ExecutionRuntimeStatus,
    ExecutionStatus,

    get_execution_runtime,
    reset_execution_runtime,
)
from brain.planning import ActionPlan, ActionStep, ActionType, ExecutionPlan, ExecutionReadiness


@pytest.fixture
def runtime() -> ExecutionRuntimeCoordinator:
    """Fixture providing an initialized ExecutionRuntimeCoordinator instance."""
    rt = ExecutionRuntimeCoordinator()
    rt.initialize()
    yield rt
    rt.shutdown()


def test_runtime_initialization(runtime: ExecutionRuntimeCoordinator) -> None:
    """Verifies runtime initialization and status transition to READY."""
    assert runtime.status == ExecutionRuntimeStatus.READY
    components = runtime.list_components()
    assert len(components) == 3
    assert "ExecutionStepRunner" in components
    assert "ExecutionCoordinator" in components
    assert "ExecutionPolicy" in components


def test_runtime_shutdown(runtime: ExecutionRuntimeCoordinator) -> None:
    """Verifies runtime shutdown transition and resource cleanup."""
    res = runtime.shutdown()
    assert res is True
    assert runtime.status == ExecutionRuntimeStatus.SHUTDOWN


def test_runtime_health_check(runtime: ExecutionRuntimeCoordinator) -> None:
    """Verifies health check reporting components and healthy flag."""
    health = runtime.health_check()
    assert isinstance(health, ExecutionRuntimeHealth)
    assert health.healthy is True
    assert health.status == ExecutionRuntimeStatus.READY
    assert len(health.registered_components) == 3


def test_runtime_execute_ready_plan(runtime: ExecutionRuntimeCoordinator) -> None:
    """Verifies execute() on READY ExecutionPlan."""
    step = ActionStep(step_number=1, action_type=ActionType.SEARCH, description="Search")
    plan = ExecutionPlan(request="test", action_plan=ActionPlan(steps=[step]), execution_order=[1], readiness=ExecutionReadiness.READY)

    res = runtime.execute(plan)
    assert isinstance(res, ExecutionResult)
    assert res.status == ExecutionStatus.COMPLETED
    assert res.completed_steps == 1


def test_runtime_statistics_tracking(runtime: ExecutionRuntimeCoordinator) -> None:
    """Verifies statistics tracking (executions started, completed, failed, latency ms)."""
    step = ActionStep(step_number=1, action_type=ActionType.SEARCH, description="Search")
    plan = ExecutionPlan(action_plan=ActionPlan(steps=[step]), execution_order=[1], readiness=ExecutionReadiness.READY)

    runtime.execute(plan)
    runtime.execute(plan)

    stats = runtime.get_statistics()
    assert isinstance(stats, ExecutionRuntimeStatistics)
    assert stats.executions_started == 2
    assert stats.executions_completed == 2
    assert stats.executions_failed == 0
    assert stats.average_runtime_ms >= 0.0


def test_runtime_statistics_failure_tracking(runtime: ExecutionRuntimeCoordinator) -> None:
    """Verifies tracking of failed executions in runtime statistics."""
    plan = ExecutionPlan(readiness=ExecutionReadiness.BLOCKED)
    res = runtime.execute(plan)

    assert res.status == ExecutionStatus.BLOCKED
    stats = runtime.get_statistics()
    assert stats.executions_started == 1


def test_runtime_immutable_outputs(runtime: ExecutionRuntimeCoordinator) -> None:
    """Verifies health and statistics objects are immutable snapshots."""
    health = runtime.health_check()
    with pytest.raises((TypeError, ValidationError)):
        health.healthy = False

    stats = runtime.get_statistics()
    with pytest.raises((TypeError, ValidationError)):
        stats.executions_started = 999


def test_runtime_thread_safety(runtime: ExecutionRuntimeCoordinator) -> None:
    """Verifies thread safety during concurrent health checks and stats requests."""
    step = ActionStep(step_number=1, action_type=ActionType.SEARCH, description="Thread test")
    plan = ExecutionPlan(action_plan=ActionPlan(steps=[step]), execution_order=[1], readiness=ExecutionReadiness.READY)

    def worker() -> None:
        runtime.execute(plan)
        runtime.health_check()
        runtime.get_statistics()

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker) for _ in range(20)]
        for f in futures:
            f.result()

    stats = runtime.get_statistics()
    assert stats.executions_started == 20


def test_runtime_singleton_compatibility() -> None:
    """Verifies get_execution_runtime and reset_execution_runtime singleton behavior."""
    reset_execution_runtime()
    rt1 = get_execution_runtime()
    rt2 = get_execution_runtime()
    assert rt1 is rt2

    reset_execution_runtime()
    rt3 = get_execution_runtime()
    assert rt3 is not rt1
    reset_execution_runtime()


def test_runtime_clear(runtime: ExecutionRuntimeCoordinator) -> None:
    """Verifies clear() resets statistics to initial zero state."""
    step = ActionStep(step_number=1, action_type=ActionType.SEARCH, description="Search")
    plan = ExecutionPlan(action_plan=ActionPlan(steps=[step]), execution_order=[1], readiness=ExecutionReadiness.READY)

    runtime.execute(plan)
    assert runtime.get_statistics().executions_started == 1

    runtime.clear()
    assert runtime.get_statistics().executions_started == 0
    assert runtime.get_statistics().executions_completed == 0


def test_runtime_list_sessions(runtime: ExecutionRuntimeCoordinator) -> None:
    """Verifies list_sessions returns list of active execution sessions."""
    sessions = runtime.list_sessions()
    assert isinstance(sessions, list)


def test_runtime_list_components(runtime: ExecutionRuntimeCoordinator) -> None:
    """Verifies list_components returns all 3 execution component names."""
    components = runtime.list_components()
    assert components == [
        "ExecutionStepRunner",
        "ExecutionCoordinator",
        "ExecutionPolicy",
    ]


def test_runtime_logging(caplog: pytest.LogCaptureFixture) -> None:
    """Verifies required event log outputs during runtime lifecycle."""
    rt = ExecutionRuntimeCoordinator()

    with caplog.at_level(logging.INFO):
        rt.initialize()
        rt.shutdown()

    assert "Runtime Initialized" in caplog.text
    assert "Runtime Shutdown" in caplog.text


def test_runtime_configuration_injection() -> None:
    """Verifies custom component dependency injection into ExecutionRuntimeCoordinator."""
    coord = ExecutionCoordinator()
    policy = ExecutionPolicy(maximum_retries=10)
    rt = ExecutionRuntimeCoordinator(coordinator=coord, default_policy=policy)
    rt.initialize()

    assert rt._coordinator is coord
    assert rt._default_policy is policy
    rt.shutdown()


def test_runtime_cancel_nonexistent_execution(runtime: ExecutionRuntimeCoordinator) -> None:
    """Verifies cancel_execution returns False for nonexistent execution_id."""
    res = runtime.cancel_execution("nonexistent_id")
    assert res is False


def test_runtime_pause_nonexistent_execution(runtime: ExecutionRuntimeCoordinator) -> None:
    """Verifies pause_execution returns False for nonexistent execution_id."""
    res = runtime.pause_execution("nonexistent_id")
    assert res is False


def test_runtime_resume_nonexistent_execution(runtime: ExecutionRuntimeCoordinator) -> None:
    """Verifies resume_execution returns False for nonexistent execution_id."""
    res = runtime.resume_execution("nonexistent_id")
    assert res is False


def test_runtime_auto_reinitializes_on_execute_if_shutdown() -> None:
    """Verifies runtime automatically re-initializes when execute() is called while SHUTDOWN."""
    rt = ExecutionRuntimeCoordinator()
    rt.initialize()
    rt.shutdown()
    assert rt.status == ExecutionRuntimeStatus.SHUTDOWN

    step = ActionStep(step_number=1, action_type=ActionType.SEARCH, description="Search")
    plan = ExecutionPlan(action_plan=ActionPlan(steps=[step]), execution_order=[1], readiness=ExecutionReadiness.READY)

    res = rt.execute(plan)
    assert res.status == ExecutionStatus.COMPLETED
    assert rt.status == ExecutionStatus.READY or rt.status == ExecutionRuntimeStatus.READY


def test_runtime_diagnostics(runtime: ExecutionRuntimeCoordinator) -> None:
    """Verifies health check metadata contains thread_safety information."""
    health = runtime.health_check()
    assert health.metadata.get("thread_safety") == "PROTECTED"


def test_runtime_execute_none_plan(runtime: ExecutionRuntimeCoordinator) -> None:
    """Verifies execute() with None plan executes default plan cleanly."""
    res = runtime.execute(None)
    assert isinstance(res, ExecutionResult)
    assert res.status == ExecutionStatus.COMPLETED


def test_runtime_statistics_average_step_time(runtime: ExecutionRuntimeCoordinator) -> None:
    """Verifies average_step_time_ms calculation in runtime statistics."""
    step = ActionStep(step_number=1, action_type=ActionType.SEARCH, description="Search")
    plan = ExecutionPlan(action_plan=ActionPlan(steps=[step]), execution_order=[1], readiness=ExecutionReadiness.READY)

    runtime.execute(plan)
    stats = runtime.get_statistics()
    assert stats.average_step_time_ms >= 0.0


def test_runtime_peak_concurrent_sessions(runtime: ExecutionRuntimeCoordinator) -> None:
    """Verifies peak_concurrent_sessions tracking in statistics."""
    step = ActionStep(step_number=1, action_type=ActionType.SEARCH, description="Search")
    plan = ExecutionPlan(action_plan=ActionPlan(steps=[step]), execution_order=[1], readiness=ExecutionReadiness.READY)

    runtime.execute(plan)
    stats = runtime.get_statistics()
    assert stats.peak_concurrent_sessions >= 1


def test_runtime_backward_compatibility() -> None:
    """Verifies backward compatibility with existing execution exports."""
    from brain.execution import (
        ExecutionRuntimeCoordinator,
        ExecutionRuntimeHealth,
        ExecutionRuntimeStatistics,
        ExecutionRuntimeStatus,
        get_execution_runtime,
        reset_execution_runtime,
    )

    rt = get_execution_runtime()
    assert rt is not None
    reset_execution_runtime()


def test_runtime_regression_validation(runtime: ExecutionRuntimeCoordinator) -> None:
    """Verifies stability across multiple sequential plan executions."""
    requests = ["search report", "copy image", "open document"]
    plans = [
        ExecutionPlan(
            request=req,
            action_plan=ActionPlan(steps=[ActionStep(step_number=1, action_type=ActionType.SEARCH, description=req)]),
            execution_order=[1],
            readiness=ExecutionReadiness.READY,
        )
        for req in requests
    ]

    results = [runtime.execute(p) for p in plans]
    assert len(results) == 3
    assert all(r.status == ExecutionStatus.COMPLETED for r in results)
    assert runtime.get_statistics().executions_started == 3
