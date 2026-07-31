"""AIResilienceRuntime high-level service coordinating runtime resilience (Phase 10.7).

Coordinates:
RetryManager → FailureClassifier → RecoveryManager → CircuitBreaker → EventDispatcher
Uses dependency injection throughout without provider, planner, or filesystem logic.
"""

import logging
from typing import Any, Callable, Optional

from brain.ai.resilience.exceptions import CircuitBreakerOpenError, ResilienceException
from brain.ai.resilience.interfaces import (
    CancellationManagerInterface,
    CircuitBreakerInterface,
    EventDispatcherInterface,
    FailureClassifierInterface,
    RecoveryManagerInterface,
    ResilienceRuntimeInterface,
    RetryManagerInterface,
    TimeoutManagerInterface,
)
from brain.ai.resilience.cancellation_manager import DefaultCancellationManager
from brain.ai.resilience.circuit_breaker import DefaultCircuitBreaker
from brain.ai.resilience.event_dispatcher import DefaultEventDispatcher
from brain.ai.resilience.failure_classifier import DefaultFailureClassifier
from brain.ai.resilience.recovery_manager import DefaultRecoveryManager
from brain.ai.resilience.retry_manager import DefaultRetryManager
from brain.ai.resilience.timeout_manager import DefaultTimeoutManager
from brain.ai.resilience.resilience_models import (
    CircuitState,
    EventType,
    FailureInfo,
    RecoveryAction,
    RecoveryDecision,
    ResilienceContext,
)

logger = logging.getLogger(__name__)


class AIResilienceRuntime(ResilienceRuntimeInterface):
    """High-level Runtime Validation & Resilience service."""

    def __init__(
        self,
        retry_manager: Optional[RetryManagerInterface] = None,
        timeout_manager: Optional[TimeoutManagerInterface] = None,
        cancellation_manager: Optional[CancellationManagerInterface] = None,
        failure_classifier: Optional[FailureClassifierInterface] = None,
        recovery_manager: Optional[RecoveryManagerInterface] = None,
        circuit_breaker: Optional[CircuitBreakerInterface] = None,
        event_dispatcher: Optional[EventDispatcherInterface] = None,
    ) -> None:
        self.retry_manager = retry_manager or DefaultRetryManager()
        self.timeout_manager = timeout_manager or DefaultTimeoutManager()
        self.cancellation_manager = cancellation_manager or DefaultCancellationManager()
        self.failure_classifier = failure_classifier or DefaultFailureClassifier()
        self.recovery_manager = recovery_manager or DefaultRecoveryManager()
        self.circuit_breaker = circuit_breaker or DefaultCircuitBreaker()
        self.event_dispatcher = event_dispatcher or DefaultEventDispatcher()

    def execute_with_resilience(
        self,
        target_id: str,
        operation: Callable[[], Any],
        context: Optional[ResilienceContext] = None,
    ) -> Any:
        """Execute an operation wrapped with circuit breaker, timeout, failure classification, and retry management.

        Args:
            target_id: Target operation identifier.
            operation: Callable function to execute.
            context: Optional ResilienceContext configuration.

        Returns:
            Return value of operation function.

        Raises:
            CircuitBreakerOpenError: If circuit breaker is OPEN.
            ResilienceException / Original Exception: If recovery fails or decision is ABORT/ESCALATE.
        """
        # 1. Check Circuit Breaker
        cb_state = self.circuit_breaker.get_state()
        if cb_state.state == CircuitState.OPEN:
            self.event_dispatcher.dispatch_event(
                EventType.CIRCUIT_OPENED,
                source=target_id,
                payload={"circuit_id": cb_state.circuit_id},
            )
            raise CircuitBreakerOpenError(
                f"Operation '{target_id}' blocked by OPEN circuit breaker '{cb_state.circuit_id}'."
            )

        # 2. Check Cancellation
        if self.cancellation_manager.is_cancelled(target_id):
            self.event_dispatcher.dispatch_event(
                EventType.CANCELLATION_REQUESTED,
                source=target_id,
                payload={"target_id": target_id},
            )
            cancel_req = self.cancellation_manager.get_cancellation_request(target_id)
            reason_msg = cancel_req.reason.value if cancel_req else "Operation cancelled"
            raise ResilienceException(f"Operation '{target_id}' was cancelled: {reason_msg}")

        # 3. Start Timeout Tracking
        timeout_policy = context.timeout_policy if context else None
        timeout_limit = timeout_policy.step_timeout_seconds if timeout_policy else 30.0
        self.timeout_manager.start_timer(target_id, timeout_limit)

        self.event_dispatcher.dispatch_event(EventType.STEP_STARTED, source=target_id)

        attempt = 1
        max_retries = context.retry_policy.max_retries if context else 3

        while True:
            try:
                result = operation()
                self.circuit_breaker.record_success()
                self.event_dispatcher.dispatch_event(
                    EventType.STEP_COMPLETED,
                    source=target_id,
                    payload={"attempt": attempt},
                )
                return result

            except Exception as exc:
                self.circuit_breaker.record_failure()

                # 4. Classify Failure
                failure_info: FailureInfo = self.failure_classifier.classify_failure(
                    exc, metadata={"target_id": target_id, "attempt": attempt}
                )

                # 5. Determine Recovery Decision
                decision: RecoveryDecision = self.recovery_manager.determine_recovery(
                    failure_info, attempt_number=attempt, max_retries=max_retries
                )

                self.event_dispatcher.dispatch_event(
                    EventType.STEP_FAILED,
                    source=target_id,
                    payload={
                        "attempt": attempt,
                        "failure_type": failure_info.failure_type.value,
                        "action": decision.action.value,
                    },
                )

                if decision.action == RecoveryAction.RETRY and attempt <= max_retries:
                    attempt_info = self.retry_manager.evaluate_retry(
                        attempt_number=attempt,
                        policy=context.retry_policy if context else None,
                        reason=failure_info.message,
                        target_id=target_id,
                    )
                    self.event_dispatcher.dispatch_event(
                        EventType.RETRY_SCHEDULED,
                        source=target_id,
                        payload={
                            "attempt": attempt,
                            "delay_seconds": attempt_info.delay_seconds if attempt_info else 0.0,
                        },
                    )
                    attempt += 1
                    continue

                if decision.action in (RecoveryAction.SKIP, RecoveryAction.CONTINUE):
                    logger.warning(f"Operation '{target_id}' failed but recovery action is '{decision.action.value}'. Returning None.")
                    return None

                # ABORT or ESCALATE -> Raise original exception
                raise
