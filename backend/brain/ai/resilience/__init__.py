"""Runtime Validation & Resilience package for Auralis (Phase 10.7).

Exports all resilience models, enums, exceptions, interfaces, managers, circuit breaker,
event dispatcher, and AIResilienceRuntime.
"""

from brain.ai.resilience.exceptions import (
    CircuitBreakerOpenError,
    ExecutionCancelledError,
    RecoveryExecutionError,
    ResilienceException,
    RetryLimitExceededError,
    TimeoutExceededError,
)
from brain.ai.resilience.resilience_models import (
    CancellationReason,
    CancellationRequest,
    CircuitBreakerState,
    CircuitState,
    EventType,
    FailureInfo,
    FailureType,
    RecoveryAction,
    RecoveryDecision,
    ResilienceContext,
    RetryAttempt,
    RetryPolicy,
    RetryStrategy,
    RuntimeEvent,
    TimeoutPolicy,
    TimeoutState,
    TimeoutStatus,
)
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
from brain.ai.resilience.retry_manager import DefaultRetryManager
from brain.ai.resilience.timeout_manager import DefaultTimeoutManager
from brain.ai.resilience.cancellation_manager import DefaultCancellationManager
from brain.ai.resilience.failure_classifier import DefaultFailureClassifier
from brain.ai.resilience.recovery_manager import DefaultRecoveryManager
from brain.ai.resilience.circuit_breaker import DefaultCircuitBreaker
from brain.ai.resilience.event_dispatcher import DefaultEventDispatcher
from brain.ai.resilience.resilience_runtime import AIResilienceRuntime

__all__ = [
    # Exceptions
    "ResilienceException",
    "RetryLimitExceededError",
    "TimeoutExceededError",
    "ExecutionCancelledError",
    "CircuitBreakerOpenError",
    "RecoveryExecutionError",
    # Enums & Models
    "FailureType",
    "RecoveryAction",
    "CircuitState",
    "EventType",
    "RetryStrategy",
    "TimeoutStatus",
    "CancellationReason",
    "RetryPolicy",
    "RetryAttempt",
    "TimeoutPolicy",
    "TimeoutState",
    "CancellationRequest",
    "FailureInfo",
    "RecoveryDecision",
    "CircuitBreakerState",
    "RuntimeEvent",
    "ResilienceContext",
    # Interfaces
    "RetryManagerInterface",
    "TimeoutManagerInterface",
    "CancellationManagerInterface",
    "FailureClassifierInterface",
    "RecoveryManagerInterface",
    "CircuitBreakerInterface",
    "EventDispatcherInterface",
    "ResilienceRuntimeInterface",
    # Implementations
    "DefaultRetryManager",
    "DefaultTimeoutManager",
    "DefaultCancellationManager",
    "DefaultFailureClassifier",
    "DefaultRecoveryManager",
    "DefaultCircuitBreaker",
    "DefaultEventDispatcher",
    "AIResilienceRuntime",
]
