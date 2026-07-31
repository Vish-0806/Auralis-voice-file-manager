"""DefaultCircuitBreaker implementation for state machine resilience (Phase 10.7).

Tracks failure and success counts across CLOSED, OPEN, and HALF_OPEN states and manages
trip thresholds and recovery cooldowns.
"""

import time
import logging
from datetime import datetime, timezone
from typing import Optional

from brain.ai.resilience.interfaces import CircuitBreakerInterface
from brain.ai.resilience.resilience_models import CircuitBreakerState, CircuitState

logger = logging.getLogger(__name__)


class DefaultCircuitBreaker(CircuitBreakerInterface):
    """Deterministic state machine implementing circuit breaker pattern."""

    def __init__(
        self,
        circuit_id: str = "default-circuit",
        trip_threshold: int = 3,
        recovery_threshold: int = 2,
        reset_cooldown_seconds: float = 10.0,
    ) -> None:
        self.circuit_id = circuit_id
        self.trip_threshold = trip_threshold
        self.recovery_threshold = recovery_threshold
        self.reset_cooldown_seconds = reset_cooldown_seconds

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_timestamp: Optional[float] = None
        self._last_state_change = datetime.now(timezone.utc)

    def record_success(self) -> CircuitBreakerState:
        """Record successful operation."""
        self._evaluate_cooldown()

        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.recovery_threshold:
                self._transition_to(CircuitState.CLOSED)
        elif self._state == CircuitState.CLOSED:
            self._failure_count = 0
            self._success_count += 1

        return self.get_state()

    def record_failure(self) -> CircuitBreakerState:
        """Record failed operation and evaluate trip threshold."""
        self._evaluate_cooldown()
        self._last_failure_timestamp = time.perf_counter()

        if self._state == CircuitState.CLOSED:
            self._failure_count += 1
            if self._failure_count >= self.trip_threshold:
                self._transition_to(CircuitState.OPEN)
        elif self._state == CircuitState.HALF_OPEN:
            self._transition_to(CircuitState.OPEN)

        return self.get_state()

    def get_state(self) -> CircuitBreakerState:
        """Retrieve current circuit breaker state snapshot."""
        self._evaluate_cooldown()
        return CircuitBreakerState(
            circuit_id=self.circuit_id,
            state=self._state,
            failure_count=self._failure_count,
            success_count=self._success_count,
            last_failure_timestamp=self._last_failure_timestamp,
            last_state_change=self._last_state_change,
        )

    def _evaluate_cooldown(self) -> None:
        """Check if reset cooldown has elapsed to transition OPEN -> HALF_OPEN."""
        if self._state == CircuitState.OPEN and self._last_failure_timestamp is not None:
            elapsed = time.perf_counter() - self._last_failure_timestamp
            if elapsed >= self.reset_cooldown_seconds:
                self._transition_to(CircuitState.HALF_OPEN)

    def _transition_to(self, new_state: CircuitState) -> None:
        """Internal helper to transition states and reset counters."""
        logger.info(f"Circuit '{self.circuit_id}' state transition: {self._state.value} -> {new_state.value}")
        self._state = new_state
        self._last_state_change = datetime.now(timezone.utc)

        if new_state == CircuitState.CLOSED:
            self._failure_count = 0
            self._success_count = 0
        elif new_state == CircuitState.OPEN:
            self._success_count = 0
        elif new_state == CircuitState.HALF_OPEN:
            self._success_count = 0
