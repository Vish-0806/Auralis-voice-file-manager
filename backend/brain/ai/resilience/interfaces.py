"""Abstract interfaces for Runtime Validation & Resilience (Phase 10.7).

Defines ABCs for:
- RetryManagerInterface
- TimeoutManagerInterface
- CancellationManagerInterface
- FailureClassifierInterface
- RecoveryManagerInterface
- CircuitBreakerInterface
- EventDispatcherInterface
- ResilienceRuntimeInterface
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional

from brain.ai.resilience.resilience_models import (
    CancellationReason,
    CancellationRequest,
    CircuitBreakerState,
    EventType,
    FailureInfo,
    RecoveryDecision,
    ResilienceContext,
    RetryAttempt,
    RetryPolicy,
    RuntimeEvent,
    TimeoutState,
)


class RetryManagerInterface(ABC):
    """Abstract interface for evaluating retry eligibility and delay calculations."""

    @abstractmethod
    def evaluate_retry(
        self,
        attempt_number: int,
        policy: Optional[RetryPolicy] = None,
        reason: str = "",
        target_id: str = "default",
    ) -> Optional[RetryAttempt]:
        """Calculate next retry attempt or return None if retries exhausted."""
        pass

    @abstractmethod
    def get_history(self, target_id: str = "default") -> List[RetryAttempt]:
        """Retrieve recorded retry history for a target."""
        pass


class TimeoutManagerInterface(ABC):
    """Abstract interface for execution, plan, and step timeout state evaluation."""

    @abstractmethod
    def start_timer(self, target_id: str, timeout_seconds: float) -> TimeoutState:
        """Start tracking a target timeout."""
        pass

    @abstractmethod
    def check_timeout(self, target_id: str) -> TimeoutState:
        """Check current elapsed and remaining time for a target."""
        pass

    @abstractmethod
    def stop_timer(self, target_id: str) -> None:
        """Stop tracking a target timer."""
        pass


class CancellationManagerInterface(ABC):
    """Abstract interface for tracking cancellation requests."""

    @abstractmethod
    def request_cancellation(
        self,
        target_id: str,
        requested_by: str,
        reason: CancellationReason,
        details: Optional[Dict[str, Any]] = None,
    ) -> CancellationRequest:
        """Issue a cancellation request for a target."""
        pass

    @abstractmethod
    def is_cancelled(self, target_id: str) -> bool:
        """Check if target is cancelled."""
        pass

    @abstractmethod
    def get_cancellation_request(self, target_id: str) -> Optional[CancellationRequest]:
        """Retrieve CancellationRequest details for a target."""
        pass


class FailureClassifierInterface(ABC):
    """Abstract interface for classifying runtime exceptions into FailureInfo models."""

    @abstractmethod
    def classify_failure(
        self,
        exception_or_message: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> FailureInfo:
        """Classify failure into FailureInfo model."""
        pass


class RecoveryManagerInterface(ABC):
    """Abstract interface for determining RecoveryDecision actions."""

    @abstractmethod
    def determine_recovery(
        self,
        failure_info: FailureInfo,
        attempt_number: int = 1,
        max_retries: int = 3,
    ) -> RecoveryDecision:
        """Determine recovery action (RETRY, CONTINUE, SKIP, ABORT, ESCALATE)."""
        pass


class CircuitBreakerInterface(ABC):
    """Abstract interface for CircuitBreaker state management."""

    @abstractmethod
    def record_success(self) -> CircuitBreakerState:
        """Record successful operation."""
        pass

    @abstractmethod
    def record_failure(self) -> CircuitBreakerState:
        """Record failed operation and check trip threshold."""
        pass

    @abstractmethod
    def get_state(self) -> CircuitBreakerState:
        """Retrieve current circuit breaker state."""
        pass


class EventDispatcherInterface(ABC):
    """Abstract interface for recording runtime events and notifying listeners."""

    @abstractmethod
    def dispatch_event(
        self,
        event_type: EventType,
        source: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> RuntimeEvent:
        """Record and dispatch a structured RuntimeEvent."""
        pass

    @abstractmethod
    def register_listener(
        self,
        event_type: EventType,
        listener: Callable[[RuntimeEvent], None],
    ) -> None:
        """Register observer callback for an EventType."""
        pass

    @abstractmethod
    def get_events(self, event_type: Optional[EventType] = None) -> List[RuntimeEvent]:
        """Retrieve recorded events list."""
        pass


class ResilienceRuntimeInterface(ABC):
    """Abstract interface for high-level AIResilienceRuntime service."""

    @abstractmethod
    def execute_with_resilience(
        self,
        target_id: str,
        operation: Callable[[], Any],
        context: Optional[ResilienceContext] = None,
    ) -> Any:
        """Coordinate resilience pipeline around an operation function."""
        pass
