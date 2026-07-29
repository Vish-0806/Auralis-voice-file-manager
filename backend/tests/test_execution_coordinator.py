"""Unit tests for ExecutionCoordinator (Phase 9.4)."""

# pyrefly: ignore [missing-import]
import pytest

from brain.execution import (
    ExecutionCoordinator,
    ExecutionPolicy,
    ExecutionResult,
    ExecutionStatus,
    ExecutionStepResult,
    ExecutionStepRunner,
)
from brain.planning import (
    ActionPlan,
    ActionStep,
    ActionType,
    DependencyResolutionResult,
    DependencyStatus,
    ExecutionPlan,
    ExecutionReadiness,
    PlanValidationResult,
    RiskAnalysisResult,
    RiskLevel,
)


@pytest.fixture
def coordinator() -> ExecutionCoordinator:
    """Fixture providing an ExecutionCoordinator instance."""
    return ExecutionCoordinator()


def test_execute_plan_ready(coordinator: ExecutionCoordinator) -> None:
    """Verifies execution of valid READY ExecutionPlan."""
    step1 = ActionStep(step_number=1, action_type=ActionType.SEARCH, description="Search")
    plan = ExecutionPlan(
        request="search data",
        action_plan=ActionPlan(steps=[step1]),
        execution_order=[1],
        readiness=ExecutionReadiness.READY,
    )

    res = coordinator.execute_plan(plan)
    assert isinstance(res, ExecutionResult)
    assert res.status == ExecutionStatus.COMPLETED
    assert res.completed_steps == 1
    assert len(res.step_results) == 1


def test_execute_plan_ready_with_warnings(coordinator: ExecutionCoordinator) -> None:
    """Verifies execution of READY_WITH_WARNINGS ExecutionPlan."""
    step1 = ActionStep(step_number=1, action_type=ActionType.COPY_FILES, description="Copy")
    plan = ExecutionPlan(
        request="copy data",
        action_plan=ActionPlan(steps=[step1]),
        execution_order=[1],
        readiness=ExecutionReadiness.READY_WITH_WARNINGS,
        risk_result=RiskAnalysisResult(overall_risk=RiskLevel.MEDIUM, acceptable=True),
    )

    res = coordinator.execute_plan(plan)
    assert res.status == ExecutionStatus.COMPLETED


def test_execute_plan_blocked_rejection(coordinator: ExecutionCoordinator) -> None:
    """Verifies rejection of BLOCKED ExecutionPlan."""
    plan = ExecutionPlan(
        request="delete critical system files",
        readiness=ExecutionReadiness.BLOCKED,
        risk_result=RiskAnalysisResult(overall_risk=RiskLevel.CRITICAL, acceptable=False),
    )

    res = coordinator.execute_plan(plan)
    assert res.status == ExecutionStatus.BLOCKED
    assert "readiness is BLOCKED" in res.metadata.get("reason", "")


def test_execute_plan_not_ready_rejection(coordinator: ExecutionCoordinator) -> None:
    """Verifies rejection of NOT_READY ExecutionPlan."""
    plan = ExecutionPlan(
        request="invalid request",
        readiness=ExecutionReadiness.NOT_READY,
        validation_result=PlanValidationResult(valid=False),
    )

    res = coordinator.execute_plan(plan)
    assert res.status == ExecutionStatus.BLOCKED
    assert "readiness is NOT_READY" in res.metadata.get("reason", "")


def test_strict_execution_order_enforcement(coordinator: ExecutionCoordinator) -> None:
    """Verifies strict execution_order sequence enforcement."""
    step1 = ActionStep(step_number=1, action_type=ActionType.SEARCH, description="First")
    step2 = ActionStep(step_number=2, action_type=ActionType.MOVE_FILES, description="Second")
    plan = ExecutionPlan(
        request="ordered test",
        action_plan=ActionPlan(steps=[step1, step2]),
        execution_order=[2, 1],  # Reverse execution order
        readiness=ExecutionReadiness.READY,
    )

    res = coordinator.execute_plan(plan)
    assert res.status == ExecutionStatus.COMPLETED
    assert [sr.step_number for sr in res.step_results] == [2, 1]


def test_continue_on_error_false_stops_pipeline(coordinator: ExecutionCoordinator) -> None:
    """Verifies pipeline stops on first step failure when continue_on_error is False."""
    step1 = ActionStep(step_number=1, action_type=ActionType.SEARCH, description="S1")
    step2 = ActionStep(step_number=2, action_type=ActionType.SEARCH, description="S2")
    plan = ExecutionPlan(
        request="fail test",
        action_plan=ActionPlan(steps=[step1, step2]),
        execution_order=[1, 2],
        readiness=ExecutionReadiness.READY,
    )

    policy = ExecutionPolicy(maximum_retries=0, continue_on_error=False, rollback_enabled=False)

    def failing_runner(step: ActionStep, ctx: float) -> ExecutionStepResult:
        if step.step_number == 1:
            return ExecutionStepResult(step_id="step-1", step_number=1, status=ExecutionStatus.FAILED, error="Step 1 fail")
        return ExecutionStepResult(step_id="step-2", step_number=2, status=ExecutionStatus.COMPLETED)

    coordinator._step_runner.execute_step = failing_runner  # type: ignore

    res = coordinator.execute_plan(plan, policy=policy)
    assert res.status == ExecutionStatus.FAILED
    assert res.completed_steps == 0
    assert res.failed_steps == 1
    assert len(res.step_results) == 1  # Step 2 was never run


def test_continue_on_error_true_continues_pipeline(coordinator: ExecutionCoordinator) -> None:
    """Verifies pipeline continues after step failure when continue_on_error is True."""
    step1 = ActionStep(step_number=1, action_type=ActionType.SEARCH, description="S1")
    step2 = ActionStep(step_number=2, action_type=ActionType.SEARCH, description="S2")
    plan = ExecutionPlan(
        request="continue on error test",
        action_plan=ActionPlan(steps=[step1, step2]),
        execution_order=[1, 2],
        readiness=ExecutionReadiness.READY,
    )

    policy = ExecutionPolicy(maximum_retries=0, continue_on_error=True, rollback_enabled=False)

    def partial_failing_runner(step: ActionStep, ctx: float) -> ExecutionStepResult:
        if step.step_number == 1:
            return ExecutionStepResult(step_id="step-1", step_number=1, status=ExecutionStatus.FAILED, error="Step 1 fail")
        return ExecutionStepResult(step_id="step-2", step_number=2, status=ExecutionStatus.COMPLETED)

    coordinator._step_runner.execute_step = partial_failing_runner  # type: ignore

    res = coordinator.execute_plan(plan, policy=policy)
    assert res.status == ExecutionStatus.COMPLETED
    assert res.completed_steps == 1
    assert res.failed_steps == 1
    assert len(res.step_results) == 2


def test_rollback_triggered_on_failure(coordinator: ExecutionCoordinator) -> None:
    """Verifies rollback steps are recorded when rollback_enabled is True and step fails."""
    step1 = ActionStep(step_number=1, action_type=ActionType.MOVE_FILES, description="S1")
    plan = ExecutionPlan(
        request="rollback test",
        action_plan=ActionPlan(steps=[step1]),
        execution_order=[1],
        readiness=ExecutionReadiness.READY,
    )

    policy = ExecutionPolicy(maximum_retries=0, rollback_enabled=True, continue_on_error=False)

    def failing_runner(step: ActionStep, ctx: float) -> ExecutionStepResult:
        return ExecutionStepResult(step_id="step-1", step_number=1, status=ExecutionStatus.FAILED, error="Failed move")

    coordinator._step_runner.execute_step = failing_runner  # type: ignore

    res = coordinator.execute_plan(plan, policy=policy)
    assert res.status == ExecutionStatus.FAILED
    assert any(sr.status == ExecutionStatus.ROLLING_BACK for sr in res.step_results)


def test_cancellation_during_plan_execution(coordinator: ExecutionCoordinator) -> None:
    """Verifies cancellation token aborts plan execution between steps."""
    step1 = ActionStep(step_number=1, action_type=ActionType.SEARCH, description="S1")
    step2 = ActionStep(step_number=2, action_type=ActionType.SEARCH, description="S2")
    plan = ExecutionPlan(
        request="cancel mid-exec",
        action_plan=ActionPlan(steps=[step1, step2]),
        execution_order=[1, 2],
        readiness=ExecutionReadiness.READY,
    )

    def cancelling_step_runner(step: ActionStep, ctx: float) -> ExecutionStepResult:
        if step.step_number == 1:
            ctx.request_cancellation()  # type: ignore
        return ExecutionStepResult(step_id=f"step-{step.step_number}", step_number=step.step_number, status=ExecutionStatus.COMPLETED)

    coordinator._step_runner.execute_step = cancelling_step_runner  # type: ignore

    res = coordinator.execute_plan(plan)
    assert res.status == ExecutionStatus.CANCELLED


def test_custom_default_policy_injection() -> None:
    """Verifies initializing ExecutionCoordinator with custom default policy."""
    policy = ExecutionPolicy(maximum_retries=10)
    coord = ExecutionCoordinator(default_policy=policy)
    step1 = ActionStep(step_number=1, action_type=ActionType.SEARCH, description="S1")
    plan = ExecutionPlan(action_plan=ActionPlan(steps=[step1]), execution_order=[1], readiness=ExecutionReadiness.READY)

    res = coord.execute_plan(plan)
    assert res.status == ExecutionStatus.COMPLETED


def test_execute_empty_plan(coordinator: ExecutionCoordinator) -> None:
    """Verifies executing an empty plan completes successfully with zero step results."""
    plan = ExecutionPlan(readiness=ExecutionReadiness.READY)
    res = coordinator.execute_plan(plan)

    assert res.status == ExecutionStatus.COMPLETED
    assert res.completed_steps == 0
    assert len(res.step_results) == 0


def test_missing_step_number_in_map(coordinator: ExecutionCoordinator) -> None:
    """Verifies handling when execution_order contains a step number missing from action_plan.steps."""
    step1 = ActionStep(step_number=1, action_type=ActionType.SEARCH, description="S1")
    plan = ExecutionPlan(
        action_plan=ActionPlan(steps=[step1]),
        execution_order=[1, 999],  # 999 does not exist
        readiness=ExecutionReadiness.READY,
    )

    res = coordinator.execute_plan(plan)
    assert res.status == ExecutionStatus.COMPLETED
    assert res.completed_steps == 1
    assert len(res.step_results) == 1


def test_coordinator_thread_safety() -> None:
    """Verifies thread safety under concurrent plan execution calls."""
    coord = ExecutionCoordinator()
    step = ActionStep(step_number=1, action_type=ActionType.SEARCH, description="Concurrent step")
    plan = ExecutionPlan(action_plan=ActionPlan(steps=[step]), execution_order=[1], readiness=ExecutionReadiness.READY)

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(coord.execute_plan, plan) for _ in range(20)]
        results = [f.result() for f in futures]

    assert len(results) == 20
    assert all(r.status == ExecutionStatus.COMPLETED for r in results)


def test_coordinator_execution_time_positive(coordinator: ExecutionCoordinator) -> None:
    """Verifies ExecutionResult execution_time is positive."""
    step = ActionStep(step_number=1, action_type=ActionType.SEARCH, description="S1")
    plan = ExecutionPlan(action_plan=ActionPlan(steps=[step]), execution_order=[1], readiness=ExecutionReadiness.READY)

    res = coordinator.execute_plan(plan)
    assert res.execution_time >= 0.0


def test_coordinator_metadata_propagation(coordinator: ExecutionCoordinator) -> None:
    """Verifies plan metadata is propagated into final ExecutionResult."""
    plan = ExecutionPlan(
        readiness=ExecutionReadiness.READY,
        metadata={"session_tag": "t100"},
    )
    res = coordinator.execute_plan(plan)
    assert res.metadata.get("session_tag") == "t100"


def test_custom_step_runner_injection() -> None:
    """Verifies initializing ExecutionCoordinator with custom ExecutionStepRunner."""
    custom_runner = ExecutionStepRunner()
    coord = ExecutionCoordinator(step_runner=custom_runner)
    assert coord._step_runner is custom_runner


def test_coordinator_multiple_steps_sequential(coordinator: ExecutionCoordinator) -> None:
    """Verifies multi-step plan execution."""
    s1 = ActionStep(step_number=1, action_type=ActionType.CREATE_FOLDER, description="Create")
    s2 = ActionStep(step_number=2, action_type=ActionType.SEARCH, description="Search")
    s3 = ActionStep(step_number=3, action_type=ActionType.MOVE_FILES, description="Move")
    plan = ExecutionPlan(
        action_plan=ActionPlan(steps=[s1, s2, s3]),
        execution_order=[1, 2, 3],
        readiness=ExecutionReadiness.READY,
    )

    res = coordinator.execute_plan(plan)
    assert res.completed_steps == 3
    assert res.status == ExecutionStatus.COMPLETED


def test_coordinator_policy_override(coordinator: ExecutionCoordinator) -> None:
    """Verifies passing explicit policy override to execute_plan."""
    plan = ExecutionPlan(readiness=ExecutionReadiness.READY)
    override_policy = ExecutionPolicy(maximum_retries=10)

    res = coordinator.execute_plan(plan, policy=override_policy)
    assert res.status == ExecutionStatus.COMPLETED


def test_coordinator_rollback_disabled(coordinator: ExecutionCoordinator) -> None:
    """Verifies rollback step is skipped when rollback_enabled is False."""
    step1 = ActionStep(step_number=1, action_type=ActionType.MOVE_FILES, description="S1")
    plan = ExecutionPlan(
        action_plan=ActionPlan(steps=[step1]),
        execution_order=[1],
        readiness=ExecutionReadiness.READY,
    )

    policy = ExecutionPolicy(maximum_retries=0, rollback_enabled=False, continue_on_error=False)

    def failing_runner(step: ActionStep, ctx: float) -> ExecutionStepResult:
        return ExecutionStepResult(step_id="step-1", step_number=1, status=ExecutionStatus.FAILED, error="Failed move")

    coordinator._step_runner.execute_step = failing_runner  # type: ignore

    res = coordinator.execute_plan(plan, policy=policy)
    assert res.status == ExecutionStatus.FAILED
    assert not any(sr.status == ExecutionStatus.ROLLING_BACK for sr in res.step_results)


def test_coordinator_single_step_failure(coordinator: ExecutionCoordinator) -> None:
    """Verifies single step failure counts as failed_steps == 1."""
    step1 = ActionStep(step_number=1, action_type=ActionType.SEARCH, description="S1")
    plan = ExecutionPlan(
        action_plan=ActionPlan(steps=[step1]),
        execution_order=[1],
        readiness=ExecutionReadiness.READY,
    )

    def failing_runner(step: ActionStep, ctx: float) -> ExecutionStepResult:
        return ExecutionStepResult(step_id="step-1", step_number=1, status=ExecutionStatus.FAILED, error="Failed")

    coordinator._step_runner.execute_step = failing_runner  # type: ignore

    res = coordinator.execute_plan(plan, policy=ExecutionPolicy(maximum_retries=0, rollback_enabled=False))
    assert res.failed_steps == 1
    assert res.completed_steps == 0


def test_coordinator_defaults_execution_order_if_empty(coordinator: ExecutionCoordinator) -> None:
    """Verifies defaulting to step numbers from action_plan.steps if execution_order is empty."""
    s1 = ActionStep(step_number=5, action_type=ActionType.SEARCH, description="S5")
    plan = ExecutionPlan(
        action_plan=ActionPlan(steps=[s1]),
        execution_order=[],  # empty execution order
        readiness=ExecutionReadiness.READY,
    )

    res = coordinator.execute_plan(plan)
    assert res.completed_steps == 1
    assert res.step_results[0].step_number == 5


def test_coordinator_execution_result_timestamps_populated(coordinator: ExecutionCoordinator) -> None:
    """Verifies started_at and finished_at are populated on ExecutionResult."""
    plan = ExecutionPlan(readiness=ExecutionReadiness.READY)
    res = coordinator.execute_plan(plan)
    assert res.started_at is not None
    assert res.finished_at is not None


def test_coordinator_rejection_logs_warning(caplog: pytest.LogCaptureFixture, coordinator: ExecutionCoordinator) -> None:
    """Verifies rejection of BLOCKED plan logs warning message."""
    import logging
    plan = ExecutionPlan(readiness=ExecutionReadiness.BLOCKED)

    with caplog.at_level(logging.WARNING):
        coordinator.execute_plan(plan)

    assert "Execution rejected due to plan readiness" in caplog.text


def test_coordinator_rollback_logs_info(caplog: pytest.LogCaptureFixture, coordinator: ExecutionCoordinator) -> None:
    """Verifies rollback logging message outputs."""
    import logging
    step1 = ActionStep(step_number=1, action_type=ActionType.MOVE_FILES, description="S1")
    plan = ExecutionPlan(action_plan=ActionPlan(steps=[step1]), execution_order=[1], readiness=ExecutionReadiness.READY)

    def failing_runner(step: ActionStep, ctx: float) -> ExecutionStepResult:
        return ExecutionStepResult(step_id="step-1", step_number=1, status=ExecutionStatus.FAILED)

    coordinator._step_runner.execute_step = failing_runner  # type: ignore

    with caplog.at_level(logging.INFO):
        coordinator.execute_plan(plan, policy=ExecutionPolicy(maximum_retries=0, rollback_enabled=True))

    assert "Rollback Started" in caplog.text
    assert "Rollback Completed" in caplog.text
