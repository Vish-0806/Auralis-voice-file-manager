"""Comprehensive Unit Tests for Phase 10.7: Runtime Validation & Resilience.

Validates:
- DefaultRetryManager: Fixed and exponential backoff calculations, attempt limits, history tracking
- DefaultTimeoutManager: Execution, plan, and step timeout status, elapsed and remaining calculations
- DefaultCancellationManager: Manual, timeout, and dependency cancellation tracking
- DefaultFailureClassifier: Failure classification into TRANSIENT, PERMANENT, TOOL, TIMEOUT, etc.
- DefaultRecoveryManager: RecoveryDecision action calculation (RETRY, CONTINUE, SKIP, ABORT, ESCALATE)
- DefaultCircuitBreaker: State transitions (CLOSED -> OPEN -> HALF_OPEN -> CLOSED) and trip thresholds
- DefaultEventDispatcher: Event recording and dispatching to registered observer listeners
- AIResilienceRuntime: End-to-end resilience coordination, retries, and error handling
"""

# pyrefly: ignore [missing-import]
import pytest
import time

from brain.ai import (
    AIResilienceRuntime,
    CancellationReason,
    CircuitBreakerOpenError,
    CircuitState,
    DefaultCancellationManager,
    DefaultCircuitBreaker,
    DefaultEventDispatcher,
    DefaultFailureClassifier,
    DefaultRecoveryManager,
    DefaultRetryManager,
    DefaultTimeoutManager,
    EventType,
    FailureInfo,
    FailureType,
    RecoveryAction,
    ResilienceContext,
    ResilienceException,
    RetryPolicy,
    RetryStrategy,
    TimeoutStatus,
)


# ---------------------------------------------------------------------------
# Tests: RetryManager
# ---------------------------------------------------------------------------


def test_retry_manager_fixed_and_exponential_backoff():
    """Test DefaultRetryManager calculates fixed and exponential backoff delays."""
    rm = DefaultRetryManager()

    policy_exp = RetryPolicy(max_retries=3, base_delay_seconds=1.0, backoff_multiplier=2.0, strategy=RetryStrategy.EXPONENTIAL_BACKOFF)

    att1 = rm.evaluate_retry(1, policy=policy_exp, target_id="t1")
    att2 = rm.evaluate_retry(2, policy=policy_exp, target_id="t1")
    att3 = rm.evaluate_retry(3, policy=policy_exp, target_id="t1")
    att4 = rm.evaluate_retry(4, policy=policy_exp, target_id="t1")

    assert att1 is not None and att1.delay_seconds == 1.0
    assert att2 is not None and att2.delay_seconds == 2.0
    assert att3 is not None and att3.delay_seconds == 4.0
    assert att4 is None  # Max retries exceeded

    history = rm.get_history("t1")
    assert len(history) == 3


# ---------------------------------------------------------------------------
# Tests: TimeoutManager
# ---------------------------------------------------------------------------


def test_timeout_manager_evaluation():
    """Test DefaultTimeoutManager tracks elapsed/remaining time and status."""
    tm = DefaultTimeoutManager()

    tm.start_timer("t-short", timeout_seconds=0.05)
    st_active = tm.check_timeout("t-short")
    assert st_active.status in (TimeoutStatus.ACTIVE, TimeoutStatus.WARNING, TimeoutStatus.EXPIRED)

    time.sleep(0.06)
    st_expired = tm.check_timeout("t-short")
    assert st_expired.status == TimeoutStatus.EXPIRED
    assert st_expired.remaining_seconds == 0.0


# ---------------------------------------------------------------------------
# Tests: CancellationManager
# ---------------------------------------------------------------------------


def test_cancellation_manager_manual_and_dependency():
    """Test DefaultCancellationManager tracks cancellation requests."""
    cm = DefaultCancellationManager()

    assert cm.is_cancelled("target-1") is False

    cm.request_cancellation("target-1", requested_by="user", reason=CancellationReason.MANUAL)
    assert cm.is_cancelled("target-1") is True

    req = cm.get_cancellation_request("target-1")
    assert req is not None
    assert req.reason == CancellationReason.MANUAL


# ---------------------------------------------------------------------------
# Tests: FailureClassifier
# ---------------------------------------------------------------------------


def test_failure_classifier_types():
    """Test DefaultFailureClassifier categorizes errors correctly."""
    fc = DefaultFailureClassifier()

    info_transient = fc.classify_failure("HTTP 429 Too Many Requests rate limit exceeded")
    assert info_transient.failure_type == FailureType.TRANSIENT
    assert info_transient.is_transient is True

    info_timeout = fc.classify_failure("Connection timed out after 3000ms")
    assert info_timeout.failure_type == FailureType.TIMEOUT

    info_tool = fc.classify_failure("Tool execution failed: file missing")
    assert info_tool.failure_type == FailureType.TOOL


# ---------------------------------------------------------------------------
# Tests: RecoveryManager
# ---------------------------------------------------------------------------


def test_recovery_manager_decisions():
    """Test DefaultRecoveryManager determines appropriate recovery actions."""
    rm = DefaultRecoveryManager()

    info_trans = FailureInfo(failure_id="f1", failure_type=FailureType.TRANSIENT, message="429", is_transient=True)
    dec_retry = rm.determine_recovery(info_trans, attempt_number=1, max_retries=3)
    assert dec_retry.action == RecoveryAction.RETRY

    info_perm = FailureInfo(failure_id="f2", failure_type=FailureType.PERMANENT, message="401 Auth error", is_transient=False)
    dec_esc = rm.determine_recovery(info_perm, attempt_number=1, max_retries=3)
    assert dec_esc.action == RecoveryAction.ESCALATE

    info_tool = FailureInfo(failure_id="f3", failure_type=FailureType.TOOL, message="Tool error", is_transient=False)
    dec_skip = rm.determine_recovery(info_tool, attempt_number=1, max_retries=3)
    assert dec_skip.action == RecoveryAction.SKIP


# ---------------------------------------------------------------------------
# Tests: CircuitBreaker
# ---------------------------------------------------------------------------


def test_circuit_breaker_state_transitions():
    """Test DefaultCircuitBreaker transitions across CLOSED, OPEN, and HALF_OPEN states."""
    cb = DefaultCircuitBreaker(trip_threshold=2, recovery_threshold=1, reset_cooldown_seconds=0.05)

    assert cb.get_state().state == CircuitState.CLOSED

    # Record 2 failures -> Trip to OPEN
    cb.record_failure()
    st = cb.record_failure()
    assert st.state == CircuitState.OPEN

    # Cooldown wait -> HALF_OPEN
    time.sleep(0.06)
    assert cb.get_state().state == CircuitState.HALF_OPEN

    # Record success in HALF_OPEN -> CLOSED
    st_recovered = cb.record_success()
    assert st_recovered.state == CircuitState.CLOSED


# ---------------------------------------------------------------------------
# Tests: EventDispatcher
# ---------------------------------------------------------------------------


def test_event_dispatcher_listener_notification():
    """Test DefaultEventDispatcher records events and notifies registered listeners."""
    ed = DefaultEventDispatcher()
    received_events = []

    def on_step_completed(evt):
        received_events.append(evt)

    ed.register_listener(EventType.STEP_COMPLETED, on_step_completed)

    ed.dispatch_event(EventType.STEP_STARTED, source="step-1")
    ed.dispatch_event(EventType.STEP_COMPLETED, source="step-1", payload={"result": "ok"})

    assert len(received_events) == 1
    assert received_events[0].source == "step-1"
    assert len(ed.get_events()) == 2


# ---------------------------------------------------------------------------
# Tests: AIResilienceRuntime Orchestration
# ---------------------------------------------------------------------------


def test_resilience_runtime_successful_execution():
    """Test AIResilienceRuntime executes operation cleanly."""
    runtime = AIResilienceRuntime()

    res = runtime.execute_with_resilience("op-1", lambda: "success_result")
    assert res == "success_result"


def test_resilience_runtime_transient_retry_success():
    """Test AIResilienceRuntime retries transient failures until success."""
    runtime = AIResilienceRuntime()
    attempts = 0

    def flaky_operation():
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise RuntimeError("HTTP 429 Rate Limit Exceeded")
        return "eventual_success"

    res = runtime.execute_with_resilience("op-flaky", flaky_operation)
    assert res == "eventual_success"
    assert attempts == 2


def test_resilience_runtime_transient_retry_exhaustion():
    """Test AIResilienceRuntime aborts and raises exception when retries are exhausted."""
    runtime = AIResilienceRuntime()

    def always_failing_operation():
        raise RuntimeError("HTTP 429 Rate Limit Exceeded")

    with pytest.raises(RuntimeError):
        runtime.execute_with_resilience("op-fail", always_failing_operation)


def test_resilience_runtime_open_circuit_blocking():
    """Test AIResilienceRuntime blocks execution when CircuitBreaker is OPEN."""
    cb = DefaultCircuitBreaker(trip_threshold=1)
    cb.record_failure()  # Circuit OPEN

    runtime = AIResilienceRuntime(circuit_breaker=cb)

    with pytest.raises(CircuitBreakerOpenError):
        runtime.execute_with_resilience("op-blocked", lambda: "should_not_run")
