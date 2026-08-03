"""Abstract Interfaces for the Decision & Reasoning Coordinator Subsystem (Phase 13.4).

Defines Python ABC interfaces for decision coordination, policy evaluation,
candidate scoring, provider aggregation, and runtime orchestration.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from brain.assistant.reasoning.models import (
    DecisionCandidate,
    DecisionContext,
    DecisionHealth,
    DecisionPolicy,
    DecisionRequest,
    DecisionResult,
    DecisionStatistics,
)


class IDecisionCoordinator(ABC):
    """Abstract interface for coordinating high-level decision routing."""

    @abstractmethod
    def evaluate_request(
        self,
        request: DecisionRequest,
        policy: Optional[DecisionPolicy] = None,
    ) -> DecisionResult:
        """Evaluate a decision request and produce a deterministic DecisionResult."""
        pass


class IDecisionPolicyManager(ABC):
    """Abstract interface for applying deterministic routing policies and rules."""

    @abstractmethod
    def evaluate_policy(
        self,
        request: DecisionRequest,
        policy: Optional[DecisionPolicy] = None,
    ) -> List[DecisionCandidate]:
        """Generate candidate routing options based on deterministic policy rules."""
        pass


class IDecisionEvaluator(ABC):
    """Abstract interface for scoring candidate actions and resolving conflicts."""

    @abstractmethod
    def evaluate_candidates(
        self,
        candidates: List[DecisionCandidate],
        context: DecisionContext,
    ) -> DecisionCandidate:
        """Score candidate options, resolve conflicts, and return the winning candidate."""
        pass


class IDecisionProvider(ABC):
    """Abstract interface aggregating decision coordinator, policy manager, and evaluator."""

    @property
    @abstractmethod
    def coordinator(self) -> IDecisionCoordinator:
        """Get the decision coordinator."""
        pass

    @property
    @abstractmethod
    def policy_manager(self) -> IDecisionPolicyManager:
        """Get the policy manager."""
        pass

    @property
    @abstractmethod
    def evaluator(self) -> IDecisionEvaluator:
        """Get the decision evaluator."""
        pass

    @abstractmethod
    def get_health(self) -> DecisionHealth:
        """Get diagnostic health report."""
        pass

    @abstractmethod
    def get_statistics(self) -> DecisionStatistics:
        """Get aggregated decision performance statistics."""
        pass

    @abstractmethod
    def initialize(self) -> None:
        """Initialize provider resources."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown provider resources."""
        pass

    @property
    @abstractmethod
    def is_initialized(self) -> bool:
        """Check if provider is initialized."""
        pass


class IDecisionRuntime(ABC):
    """Abstract interface for top-level Decision Runtime orchestration."""

    @abstractmethod
    def initialize(self) -> None:
        """Initialize decision runtime."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown decision runtime."""
        pass

    @abstractmethod
    def get_health(self) -> DecisionHealth:
        """Get overall health status."""
        pass

    @abstractmethod
    def get_statistics(self) -> DecisionStatistics:
        """Get decision execution statistics."""
        pass

    @property
    @abstractmethod
    def is_initialized(self) -> bool:
        """Check if runtime is initialized."""
        pass
