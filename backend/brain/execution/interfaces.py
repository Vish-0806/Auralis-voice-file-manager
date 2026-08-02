"""Abstract Base Class interfaces for the Auralis Brain Execution Engine Subsystem (Phase 12.1).

Defines canonical interfaces for coordinator, request analyzer, decision engine,
execution pipeline, and execution runtime.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict

from brain.execution.execution_models import (
    ExecutionDecision,
    ExecutionHealth,
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatistics,
)


class IExecutionCoordinator(ABC):
    """Interface for top-level execution coordination."""

    @abstractmethod
    def execute_request(self, request: ExecutionRequest) -> ExecutionResult:
        """Process and execute an ExecutionRequest through the complete execution subsystem."""
        pass

    @abstractmethod
    def health_check(self) -> ExecutionHealth:
        """Report overall health of the coordinator and sub-components."""
        pass

    @abstractmethod
    def get_statistics(self) -> ExecutionStatistics:
        """Return aggregated runtime execution statistics."""
        pass


class IRequestAnalyzer(ABC):
    """Interface for validating, normalizing, categorizing, and analyzing incoming requests."""

    @abstractmethod
    def validate_request(self, request: Any) -> ExecutionRequest:
        """Validate and construct an ExecutionRequest from raw input."""
        pass

    @abstractmethod
    def analyze(self, request: Any) -> ExecutionRequest:
        """Perform deterministic analysis, metadata extraction, and complexity estimation."""
        pass

    @abstractmethod
    def identify_category(self, request: ExecutionRequest) -> str:
        """Determine request functional category."""
        pass

    @abstractmethod
    def extract_metadata(self, request: ExecutionRequest) -> Dict[str, Any]:
        """Extract parameters, paths, and metadata from the request."""
        pass

    @abstractmethod
    def estimate_complexity(self, request: ExecutionRequest) -> str:
        """Estimate execution complexity rating for the request."""
        pass


class IDecisionEngine(ABC):
    """Interface for evaluating analyzed requests and formulating execution decisions."""

    @abstractmethod
    def evaluate(self, request: ExecutionRequest) -> ExecutionDecision:
        """Formulate an ExecutionDecision for an analyzed request without taking action."""
        pass


class IExecutionPipeline(ABC):
    """Interface for orchestrating the multi-stage runtime execution pipeline."""

    @abstractmethod
    def execute(self, request: ExecutionRequest, decision: ExecutionDecision) -> ExecutionResult:
        """Orchestrate runtime steps through sub-runtimes according to the decision."""
        pass


class IExecutionRuntime(ABC):
    """Interface for the thread-safe singleton lifecycle manager."""

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the runtime lifecycle and underlying components."""
        pass

    @abstractmethod
    def shutdown(self) -> bool:
        """Gracefully shut down the runtime lifecycle."""
        pass

    @abstractmethod
    def process_request(self, request: Any) -> ExecutionResult:
        """Process an incoming request end-to-end."""
        pass

    @abstractmethod
    def health_check(self) -> ExecutionHealth:
        """Check runtime health state."""
        pass

    @abstractmethod
    def get_statistics(self) -> ExecutionStatistics:
        """Fetch runtime statistics snapshot."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Reset runtime statistics and clear transient execution sessions."""
        pass
