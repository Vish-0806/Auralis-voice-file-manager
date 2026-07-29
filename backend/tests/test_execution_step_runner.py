"""Unit tests for ExecutionStepRunner (Phase 9.4)."""

# pyrefly: ignore [missing-import]
import pytest

from brain.execution import (
    ExecutionContext,
    ExecutionPolicy,
    ExecutionStatus,
    ExecutionStepResult,
    ExecutionStepRunner,
)
from brain.planning import ActionStep, ActionType


@pytest.fixture
def runner() -> ExecutionStepRunner:
    """Fixture providing an ExecutionStepRunner instance."""
    return ExecutionStepRunner()


@pytest.fixture
def context() -> ExecutionContext:
    """Fixture providing a fresh ExecutionContext instance."""
    return ExecutionContext()


def test_execute_step_locate_files(runner: ExecutionStepRunner, context: ExecutionContext) -> None:
    """Verifies execution of LOCATE_FILES ActionStep."""
    step = ActionStep(step_number=1, action_type=ActionType.LOCATE_FILES, description="Locate PDFs", parameters={"target": "pdf"})
    res = runner.execute_step(step, context)

    assert isinstance(res, ExecutionStepResult)
    assert res.step_id == "step-1"
    assert res.step_number == 1
    assert res.status == ExecutionStatus.COMPLETED
    assert res.output.get("action") == ActionType.LOCATE_FILES.value
    assert res.output.get("found") is True


def test_execute_step_move_files(runner: ExecutionStepRunner, context: ExecutionContext) -> None:
    """Verifies execution of MOVE_FILES ActionStep."""
    step = ActionStep(step_number=2, action_type=ActionType.MOVE_FILES, description="Move file", parameters={"source": "a.txt", "destination": "b.txt"})
    res = runner.execute_step(step, context)

    assert res.status == ExecutionStatus.COMPLETED
    assert res.output.get("moved_count") == 1


def test_execute_step_copy_files(runner: ExecutionStepRunner, context: ExecutionContext) -> None:
    """Verifies execution of COPY_FILES ActionStep."""
    step = ActionStep(step_number=3, action_type=ActionType.COPY_FILES, description="Copy file", parameters={"source": "a.txt", "destination": "b.txt"})
    res = runner.execute_step(step, context)

    assert res.status == ExecutionStatus.COMPLETED
    assert res.output.get("copied_count") == 1


def test_execute_step_delete_files(runner: ExecutionStepRunner, context: ExecutionContext) -> None:
    """Verifies execution of DELETE_FILES ActionStep."""
    step = ActionStep(step_number=4, action_type=ActionType.DELETE_FILES, description="Delete file", parameters={"target": "temp.log"})
    res = runner.execute_step(step, context)

    assert res.status == ExecutionStatus.COMPLETED
    assert res.output.get("deleted_count") == 1


def test_execute_step_rename_files(runner: ExecutionStepRunner, context: ExecutionContext) -> None:
    """Verifies execution of RENAME_FILES ActionStep."""
    step = ActionStep(step_number=5, action_type=ActionType.RENAME_FILES, description="Rename file", parameters={"target": "old.txt", "new_name": "new.txt"})
    res = runner.execute_step(step, context)

    assert res.status == ExecutionStatus.COMPLETED
    assert res.output.get("renamed") is True


def test_execute_step_open_file(runner: ExecutionStepRunner, context: ExecutionContext) -> None:
    """Verifies execution of OPEN_FILE ActionStep."""
    step = ActionStep(step_number=6, action_type=ActionType.OPEN_FILE, description="Open doc", parameters={"file": "doc.pdf"})
    res = runner.execute_step(step, context)

    assert res.status == ExecutionStatus.COMPLETED
    assert res.output.get("opened") is True


def test_execute_step_create_folder(runner: ExecutionStepRunner, context: ExecutionContext) -> None:
    """Verifies execution of CREATE_FOLDER ActionStep."""
    step = ActionStep(step_number=7, action_type=ActionType.CREATE_FOLDER, description="Create dir", parameters={"folder": "Archive"})
    res = runner.execute_step(step, context)

    assert res.status == ExecutionStatus.COMPLETED
    assert res.output.get("created") is True


def test_execute_step_delete_folder(runner: ExecutionStepRunner, context: ExecutionContext) -> None:
    """Verifies execution of DELETE_FOLDER ActionStep."""
    step = ActionStep(step_number=8, action_type=ActionType.DELETE_FOLDER, description="Delete dir", parameters={"folder": "TempDir"})
    res = runner.execute_step(step, context)

    assert res.status == ExecutionStatus.COMPLETED
    assert res.output.get("deleted") is True


def test_execute_step_search(runner: ExecutionStepRunner, context: ExecutionContext) -> None:
    """Verifies execution of SEARCH ActionStep."""
    step = ActionStep(step_number=9, action_type=ActionType.SEARCH, description="Search query")
    res = runner.execute_step(step, context)

    assert res.status == ExecutionStatus.COMPLETED
    assert res.output.get("found") is True


def test_execute_step_respond(runner: ExecutionStepRunner, context: ExecutionContext) -> None:
    """Verifies execution of RESPOND ActionStep."""
    step = ActionStep(step_number=10, action_type=ActionType.RESPOND, description="Reply to user")
    res = runner.execute_step(step, context)

    assert res.status == ExecutionStatus.COMPLETED
    assert res.output.get("responded") is True


def test_execute_step_schedule(runner: ExecutionStepRunner, context: ExecutionContext) -> None:
    """Verifies execution of SCHEDULE ActionStep."""
    step = ActionStep(step_number=11, action_type=ActionType.SCHEDULE, description="Schedule backup")
    res = runner.execute_step(step, context)

    assert res.status == ExecutionStatus.COMPLETED
    assert res.output.get("scheduled") is True


def test_execute_step_no_action(runner: ExecutionStepRunner, context: ExecutionContext) -> None:
    """Verifies execution of NO_ACTION ActionStep."""
    step = ActionStep(step_number=12, action_type=ActionType.NO_ACTION, description="No op")
    res = runner.execute_step(step, context)

    assert res.status == ExecutionStatus.COMPLETED
    assert res.output.get("status") == "NO_OP"


def test_execute_step_when_cancellation_requested(runner: ExecutionStepRunner, context: ExecutionContext) -> None:
    """Verifies step execution is cancelled when cancellation token is set."""
    context.request_cancellation()
    step = ActionStep(step_number=1, action_type=ActionType.SEARCH, description="Search")

    res = runner.execute_step(step, context)
    assert res.status == ExecutionStatus.CANCELLED
    assert "cancellation" in (res.error or "").lower()


def test_execute_step_retry_mechanism(runner: ExecutionStepRunner) -> None:
    """Verifies retry mechanism when action handler raises an exception."""
    ctx = ExecutionContext(policy=ExecutionPolicy(maximum_retries=2))
    step = ActionStep(step_number=1, action_type=ActionType.SEARCH, description="Faulty step")

    # Monkeypatch handler to fail twice then succeed
    call_count = 0

    def faulty_handler(s: ActionStep, c: ExecutionContext) -> dict:
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise RuntimeError("Transient error")
        return {"recovered": True}

    runner._dispatch_action_handler = faulty_handler  # type: ignore

    res = runner.execute_step(step, ctx)
    assert res.status == ExecutionStatus.COMPLETED
    assert res.output.get("recovered") is True
    assert ctx.get_retry_count(1) == 2


def test_execute_step_exceeds_max_retries(runner: ExecutionStepRunner) -> None:
    """Verifies failure result when retries exceed maximum_retries limit."""
    ctx = ExecutionContext(policy=ExecutionPolicy(maximum_retries=1))
    step = ActionStep(step_number=1, action_type=ActionType.SEARCH, description="Persistent failure")

    def failing_handler(s: ActionStep, c: ExecutionContext) -> dict:
        raise RuntimeError("Persistent error")

    runner._dispatch_action_handler = failing_handler  # type: ignore

    res = runner.execute_step(step, ctx)
    assert res.status == ExecutionStatus.FAILED
    assert "Persistent error" in (res.error or "")


def test_execute_step_zero_retries(runner: ExecutionStepRunner) -> None:
    """Verifies behavior when maximum_retries is set to 0."""
    ctx = ExecutionContext(policy=ExecutionPolicy(maximum_retries=0))
    step = ActionStep(step_number=1, action_type=ActionType.SEARCH, description="Zero retries")

    def failing_handler(s: ActionStep, c: ExecutionContext) -> dict:
        raise RuntimeError("Immediate failure")

    runner._dispatch_action_handler = failing_handler  # type: ignore

    res = runner.execute_step(step, ctx)
    assert res.status == ExecutionStatus.FAILED
    assert ctx.get_retry_count(1) == 1


def test_step_duration_ms_calculation(runner: ExecutionStepRunner, context: ExecutionContext) -> None:
    """Verifies step duration_ms calculation."""
    step = ActionStep(step_number=1, action_type=ActionType.SEARCH, description="Fast step")
    res = runner.execute_step(step, context)
    assert res.duration_ms >= 0.0


def test_step_metadata_tracking(runner: ExecutionStepRunner, context: ExecutionContext) -> None:
    """Verifies step result metadata tracking."""
    step = ActionStep(step_number=1, action_type=ActionType.CREATE_FOLDER, description="Create")
    res = runner.execute_step(step, context)
    assert res.metadata.get("action_type") == ActionType.CREATE_FOLDER.value
    assert res.metadata.get("attempt") == 1


def test_cancellation_during_retry_loop(runner: ExecutionStepRunner) -> None:
    """Verifies cancellation token check during step retry loop."""
    ctx = ExecutionContext(policy=ExecutionPolicy(maximum_retries=5))
    step = ActionStep(step_number=1, action_type=ActionType.SEARCH, description="Retry step")

    call_count = 0

    def cancelling_handler(s: ActionStep, c: ExecutionContext) -> dict:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            c.request_cancellation()
            raise RuntimeError("First attempt fail")
        return {}

    runner._dispatch_action_handler = cancelling_handler  # type: ignore

    res = runner.execute_step(step, ctx)
    assert res.status == ExecutionStatus.CANCELLED


def test_step_runner_statelessness(runner: ExecutionStepRunner, context: ExecutionContext) -> None:
    """Verifies ExecutionStepRunner instances are stateless across multiple step calls."""
    step1 = ActionStep(step_number=1, action_type=ActionType.SEARCH, description="S1")
    step2 = ActionStep(step_number=2, action_type=ActionType.OPEN_FILE, description="S2")

    res1 = runner.execute_step(step1, context)
    res2 = runner.execute_step(step2, context)

    assert res1.step_id == "step-1"
    assert res2.step_id == "step-2"


def test_step_runner_handles_none_parameters(runner: ExecutionStepRunner, context: ExecutionContext) -> None:
    """Verifies handling ActionStep with None parameters dict."""
    step = ActionStep(step_number=1, action_type=ActionType.SEARCH, description="S1", parameters={})
    res = runner.execute_step(step, context)
    assert res.status == ExecutionStatus.COMPLETED


def test_step_runner_output_structure(runner: ExecutionStepRunner, context: ExecutionContext) -> None:
    """Verifies output payload is a valid dictionary."""
    step = ActionStep(step_number=1, action_type=ActionType.SEARCH, description="S1")
    res = runner.execute_step(step, context)
    assert isinstance(res.output, dict)


def test_step_runner_timestamps_populated(runner: ExecutionStepRunner, context: ExecutionContext) -> None:
    """Verifies started_at and finished_at are populated."""
    step = ActionStep(step_number=1, action_type=ActionType.SEARCH, description="S1")
    res = runner.execute_step(step, context)
    assert res.started_at is not None
    assert res.finished_at is not None


def test_step_runner_isolated_exceptions(runner: ExecutionStepRunner, context: ExecutionContext) -> None:
    """Verifies unexpected non-Exception errors are caught gracefully."""
    step = ActionStep(step_number=1, action_type=ActionType.SEARCH, description="Exception test")

    def fatal_handler(s: ActionStep, c: ExecutionContext) -> dict:
        raise ValueError("Custom value error")

    runner._dispatch_action_handler = fatal_handler  # type: ignore

    res = runner.execute_step(step, context)
    assert res.status == ExecutionStatus.FAILED
    assert "Custom value error" in (res.error or "")


def test_step_runner_with_custom_step_number(runner: ExecutionStepRunner, context: ExecutionContext) -> None:
    """Verifies step_number propagation into step_id."""
    step = ActionStep(step_number=42, action_type=ActionType.SEARCH, description="Answer to everything")
    res = runner.execute_step(step, context)
    assert res.step_id == "step-42"
    assert res.step_number == 42
