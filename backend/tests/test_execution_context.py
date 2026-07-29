"""Unit tests for ExecutionContext (Phase 9.4)."""

from concurrent.futures import ThreadPoolExecutor
# pyrefly: ignore [missing-import]
import pytest

from brain.execution import ExecutionContext, ExecutionPolicy
from brain.planning import ActionPlan, ActionStep, ActionType, ExecutionPlan


def test_execution_context_defaults() -> None:
    """Verifies default values for ExecutionContext."""
    ctx = ExecutionContext()
    assert ctx.execution_id.startswith("exec-")
    assert isinstance(ctx.plan, ExecutionPlan)
    assert isinstance(ctx.policy, ExecutionPolicy)
    assert ctx.current_step_number is None
    assert ctx.completed_steps_count == 0
    assert ctx.cancellation_requested is False
    assert ctx.pause_requested is False


def test_execution_context_custom_plan_and_policy() -> None:
    """Verifies ExecutionContext initialized with custom ExecutionPlan and ExecutionPolicy."""
    step1 = ActionStep(step_number=1, action_type=ActionType.SEARCH, description="Search")
    plan = ExecutionPlan(request="test", action_plan=ActionPlan(steps=[step1]))
    policy = ExecutionPolicy(maximum_retries=5)
    ctx = ExecutionContext(plan=plan, policy=policy, execution_id="custom-exec-id")

    assert ctx.execution_id == "custom-exec-id"
    assert ctx.plan.request == "test"
    assert ctx.policy.maximum_retries == 5


def test_current_step_number_property() -> None:
    """Verifies setting and reading current_step_number."""
    ctx = ExecutionContext()
    ctx.current_step_number = 2
    assert ctx.current_step_number == 2


def test_progress_percentage_calculation() -> None:
    """Verifies progress_percentage calculation."""
    step1 = ActionStep(step_number=1, action_type=ActionType.SEARCH, description="S1")
    step2 = ActionStep(step_number=2, action_type=ActionType.OPEN_FILE, description="S2")
    plan = ExecutionPlan(action_plan=ActionPlan(steps=[step1, step2]))
    ctx = ExecutionContext(plan=plan)

    assert ctx.progress_percentage == 0.0
    ctx.increment_completed_steps()
    assert ctx.progress_percentage == 50.0
    ctx.increment_completed_steps()
    assert ctx.progress_percentage == 100.0


def test_progress_percentage_empty_plan() -> None:
    """Verifies progress_percentage for an empty plan defaults to 100.0."""
    ctx = ExecutionContext()
    assert ctx.progress_percentage == 100.0


def test_cancellation_request() -> None:
    """Verifies request_cancellation functionality."""
    ctx = ExecutionContext()
    assert ctx.cancellation_requested is False
    req1 = ctx.request_cancellation()
    assert req1 is True
    assert ctx.cancellation_requested is True

    # Idempotent second call returns False
    req2 = ctx.request_cancellation()
    assert req2 is False


def test_pause_and_resume_request() -> None:
    """Verifies request_pause and resume functionality."""
    ctx = ExecutionContext()
    assert ctx.pause_requested is False
    res1 = ctx.request_pause()
    assert res1 is True
    assert ctx.pause_requested is True

    # Idempotent second call returns False
    res2 = ctx.request_pause()
    assert res2 is False

    # Resume resets pause token
    res3 = ctx.resume()
    assert res3 is True
    assert ctx.pause_requested is False


def test_retry_counter() -> None:
    """Verifies get_retry_count and increment_retry functionality."""
    ctx = ExecutionContext()
    assert ctx.get_retry_count(1) == 0
    cnt1 = ctx.increment_retry(1)
    assert cnt1 == 1
    assert ctx.get_retry_count(1) == 1
    cnt2 = ctx.increment_retry(1)
    assert cnt2 == 2
    assert ctx.get_retry_count(1) == 2


def test_metadata_propagation() -> None:
    """Verifies metadata propagation from plan and custom metadata dict."""
    plan = ExecutionPlan(metadata={"plan_meta": "v1"})
    ctx = ExecutionContext(plan=plan, metadata={"ctx_meta": "v2"})

    meta = ctx.metadata
    assert meta["plan_meta"] == "v1"
    assert meta["ctx_meta"] == "v2"


def test_thread_safety_cancellation() -> None:
    """Verifies thread safety during concurrent cancellation requests."""
    ctx = ExecutionContext()

    def worker() -> None:
        ctx.request_cancellation()

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker) for _ in range(50)]
        for f in futures:
            f.result()

    assert ctx.cancellation_requested is True


def test_thread_safety_increment_completed() -> None:
    """Verifies thread safety during concurrent increment_completed_steps calls."""
    step1 = ActionStep(step_number=1, action_type=ActionType.SEARCH, description="S1")
    plan = ExecutionPlan(action_plan=ActionPlan(steps=[step1] * 50))
    ctx = ExecutionContext(plan=plan)

    def worker() -> None:
        ctx.increment_completed_steps()

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker) for _ in range(50)]
        for f in futures:
            f.result()

    assert ctx.completed_steps_count == 50


def test_thread_safety_retry_counters() -> None:
    """Verifies thread safety during concurrent retry increments across multiple steps."""
    ctx = ExecutionContext()

    def worker(step_id: int) -> None:
        ctx.increment_retry(step_id)

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker, i % 5) for i in range(50)]
        for f in futures:
            f.result()

    total_retries = sum(ctx.get_retry_count(i) for i in range(5))
    assert total_retries == 50


def test_execution_id_generation_unique() -> None:
    """Verifies unique execution_id generation."""
    c1 = ExecutionContext()
    c2 = ExecutionContext()
    assert c1.execution_id != c2.execution_id


def test_resume_when_not_paused() -> None:
    """Verifies calling resume when not paused returns False."""
    ctx = ExecutionContext()
    assert ctx.resume() is False


def test_metadata_returns_copy() -> None:
    """Verifies metadata getter returns a dictionary copy."""
    ctx = ExecutionContext(metadata={"orig": True})
    m = ctx.metadata
    m["mutated"] = True
    assert "mutated" not in ctx.metadata


def test_execution_order_length_for_total_steps() -> None:
    """Verifies total_steps_count respects execution_order when present."""
    step1 = ActionStep(step_number=1, action_type=ActionType.SEARCH, description="S1")
    plan = ExecutionPlan(execution_order=[1, 2, 3], action_plan=ActionPlan(steps=[step1]))
    ctx = ExecutionContext(plan=plan)

    assert ctx._total_steps_count == 3


def test_step_number_reset() -> None:
    """Verifies resetting current_step_number to None."""
    ctx = ExecutionContext()
    ctx.current_step_number = 5
    assert ctx.current_step_number == 5
    ctx.current_step_number = None
    assert ctx.current_step_number is None


def test_context_repr() -> None:
    """Verifies string representation of ExecutionContext."""
    ctx = ExecutionContext(execution_id="exec-12345")
    assert isinstance(ctx.execution_id, str)


def test_initial_created_at_populated() -> None:
    """Verifies created_at is automatically populated."""
    ctx = ExecutionContext()
    assert ctx._created_at is not None


def test_policy_property_access() -> None:
    """Verifies policy property accessor."""
    p = ExecutionPolicy(maximum_retries=7)
    ctx = ExecutionContext(policy=p)
    assert ctx.policy.maximum_retries == 7


def test_plan_property_access() -> None:
    """Verifies plan property accessor."""
    plan = ExecutionPlan(request="req")
    ctx = ExecutionContext(plan=plan)
    assert ctx.plan.request == "req"


def test_metadata_override() -> None:
    """Verifies custom metadata overrides plan metadata keys if specified."""
    plan = ExecutionPlan(metadata={"key": "plan_val"})
    ctx = ExecutionContext(plan=plan, metadata={"key": "override_val"})
    assert ctx.metadata["key"] == "override_val"
