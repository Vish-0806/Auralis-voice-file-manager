"""Runtime Validation & Resilience Exception Hierarchy for Auralis (Phase 10.7).

Defines exception types for retries, timeouts, cancellation, circuit breaker states,
and failure recovery.
"""

from brain.ai.exceptions import AIException


class ResilienceException(AIException):
    """Base exception for all resilience subsystem errors in Auralis."""

    pass


class RetryLimitExceededError(ResilienceException):
    """Raised when maximum retry attempt threshold is exceeded."""

    pass


class TimeoutExceededError(ResilienceException):
    """Raised when execution, plan, or step time limit is exceeded."""

    pass


class ExecutionCancelledError(ResilienceException):
    """Raised when an operation is cancelled manually, by timeout, or via dependency failure."""

    pass


class CircuitBreakerOpenError(ResilienceException):
    """Raised when an operation is attempted on an OPEN circuit breaker."""

    pass


class RecoveryExecutionError(ResilienceException):
    """Raised when recovery evaluation or execution fails."""

    pass
