"""Unit tests for ExecutionSession (Phase 9.4)."""

import time
# pyrefly: ignore [missing-import]
import pytest

from brain.execution import (
    ExecutionContext,
    ExecutionPolicy,
    ExecutionResult,
    ExecutionSession,
    ExecutionStatus,
    ExecutionStepResult,
)


@pytest.fixture
def context() -> ExecutionContext:
    """Fixture providing a fresh ExecutionContext instance."""
    return ExecutionContext()


@pytest.fixture
def session(context: ExecutionContext) -> ExecutionSession:
    """Fixture providing a fresh ExecutionSession instance."""
    return ExecutionSession(context)


def test_session_initialization(session: ExecutionSession, context: ExecutionContext) -> None:
    """Verifies default values for ExecutionSession."""
    assert session.execution_id == context.execution_id
    assert session.context is context
    assert session.status == ExecutionStatus.PENDING


def test_session_start(session: ExecutionSession) -> None:
    """Verifies start transitions status from PENDING to RUNNING."""
    started = session.start()
    assert started is True
    assert session.status == ExecutionStatus.RUNNING

    # Idempotent second start returns False
    assert session.start() is False


def test_session_pause_and_resume(session: ExecutionSession) -> None:
    """Verifies pause and resume status transitions."""
    session.start()
    assert session.pause() is True
    assert session.status == ExecutionStatus.PAUSED

    assert session.resume() is True
    assert session.status == ExecutionStatus.RUNNING


def test_session_pause_when_not_running(session: ExecutionSession) -> None:
    """Verifies pause fails when status is not RUNNING."""
    assert session.pause() is False


def test_session_resume_when_not_paused(session: ExecutionSession) -> None:
    """Verifies resume fails when status is not PAUSED."""
    session.start()
    assert session.resume() is False


def test_session_cancel(session: ExecutionSession) -> None:
    """Verifies cancel transitions status to CANCELLED."""
    session.start()
    assert session.cancel() is True
    assert session.status == ExecutionStatus.CANCELLED

    # Subsequent cancel calls return False
    assert session.cancel() is False


def test_session_cancel_when_completed(session: ExecutionSession) -> None:
    """Verifies cancel fails if session is already completed."""
    session.start()
    session.complete(final_status=ExecutionStatus.COMPLETED)
    assert session.cancel() is False


def test_session_record_step_result_completed(session: ExecutionSession) -> None:
    """Verifies recording completed step execution results."""
    sr = ExecutionStepResult(step_id="s1", status=ExecutionStatus.COMPLETED)
    session.record_step_result(sr)

    res = session.complete()
    assert res.completed_steps == 1
    assert res.failed_steps == 0
    assert res.cancelled_steps == 0
    assert len(res.step_results) == 1


def test_session_record_step_result_failed(session: ExecutionSession) -> None:
    """Verifies recording failed step execution results."""
    sr = ExecutionStepResult(step_id="s1", status=ExecutionStatus.FAILED, error="Error")
    session.record_step_result(sr)

    res = session.complete()
    assert res.completed_steps == 0
    assert res.failed_steps == 1
    assert res.status == ExecutionStatus.FAILED


def test_session_record_step_result_cancelled(session: ExecutionSession) -> None:
    """Verifies recording cancelled step execution results."""
    sr = ExecutionStepResult(step_id="s1", status=ExecutionStatus.CANCELLED)
    session.record_step_result(sr)

    res = session.complete()
    assert res.cancelled_steps == 1


def test_session_complete_with_explicit_status(session: ExecutionSession) -> None:
    """Verifies completing session with explicit status override."""
    session.start()
    res = session.complete(final_status=ExecutionStatus.ROLLING_BACK)

    assert res.status == ExecutionStatus.ROLLING_BACK
    assert isinstance(res, ExecutionResult)


def test_session_complete_timing_metrics(session: ExecutionSession) -> None:
    """Verifies calculation of execution_time during complete."""
    session.start()
    time.sleep(0.01)
    res = session.complete()

    assert res.execution_time >= 5.0
    assert res.started_at is not None
    assert res.finished_at is not None


def test_session_complete_when_cancellation_requested(session: ExecutionSession) -> None:
    """Verifies complete auto-detects cancellation token."""
    session.start()
    session.context.request_cancellation()
    res = session.complete()

    assert res.status == ExecutionStatus.CANCELLED


def test_session_continue_on_error_policy() -> None:
    """Verifies session status calculation when policy.continue_on_error is True."""
    ctx = ExecutionContext(policy=ExecutionPolicy(continue_on_error=True))
    sess = ExecutionSession(ctx)
    sess.start()

    sr = ExecutionStepResult(step_id="s1", status=ExecutionStatus.FAILED)
    sess.record_step_result(sr)

    res = sess.complete()
    assert res.status == ExecutionStatus.COMPLETED
    assert res.failed_steps == 1


def test_session_multiple_step_results(session: ExecutionSession) -> None:
    """Verifies session recording multiple mixed step results."""
    session.start()
    session.record_step_result(ExecutionStepResult(step_id="s1", status=ExecutionStatus.COMPLETED))
    session.record_step_result(ExecutionStepResult(step_id="s2", status=ExecutionStatus.COMPLETED))
    session.record_step_result(ExecutionStepResult(step_id="s3", status=ExecutionStatus.CANCELLED))

    res = session.complete()
    assert res.completed_steps == 2
    assert res.cancelled_steps == 1
    assert len(res.step_results) == 3


def test_session_execution_id_property(session: ExecutionSession, context: ExecutionContext) -> None:
    """Verifies execution_id property accessor."""
    assert session.execution_id == context.execution_id


def test_session_context_property(session: ExecutionSession, context: ExecutionContext) -> None:
    """Verifies context property accessor."""
    assert session.context is context


def test_session_start_when_already_completed(session: ExecutionSession) -> None:
    """Verifies start fails if session is already completed."""
    session.start()
    session.complete()
    assert session.start() is False


def test_session_start_when_cancelled(session: ExecutionSession) -> None:
    """Verifies start fails if session is cancelled."""
    session.cancel()
    assert session.start() is False


def test_session_complete_metadata_propagation() -> None:
    """Verifies metadata propagation into ExecutionResult."""
    ctx = ExecutionContext(metadata={"key": "value"})
    sess = ExecutionSession(ctx)
    res = sess.complete()

    assert res.metadata["key"] == "value"


def test_session_multiple_completes(session: ExecutionSession) -> None:
    """Verifies multiple complete calls return consistent ExecutionResult."""
    session.start()
    res1 = session.complete()
    res2 = session.complete()

    assert res1.execution_id == res2.execution_id
    assert res1.status == res2.status


def test_session_pause_and_cancel(session: ExecutionSession) -> None:
    """Verifies cancelling a paused session."""
    session.start()
    session.pause()
    assert session.cancel() is True
    assert session.status == ExecutionStatus.CANCELLED
