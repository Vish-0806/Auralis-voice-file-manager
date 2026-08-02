"""Abstract Base Class interfaces for the Auralis Command Execution Orchestrator (Phase 12.3).

Defines canonical interfaces for coordinator, router, tracker, orchestrator, provider, and runtime.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from brain.execution.orchestrator.orchestrator_models import (
    ExecutionContext,
    ExecutionHealth,
    ExecutionRequest,
    ExecutionResult,
    ExecutionStage,
    ExecutionStageType,
    ExecutionStatistics,
    ExecutionSummary,
)


class IExecutionCoordinator(ABC):
    """Interface for evaluating execution requests, determining mode, and creating execution contexts."""

    @abstractmethod
    def prepare_execution(
        self,
        request_or_prompt: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExecutionContext:
        """Prepare an ExecutionContext from a prompt, IntentResolution, or ExecutionRequest."""
        pass


class IExecutionRouter(ABC):
    """Interface for routing execution stages toward sub-runtimes (Planning, Execution Engine, Security, OS)."""

    @abstractmethod
    def route_stage(
        self,
        stage_type: ExecutionStageType,
        context: ExecutionContext,
        payload: Optional[Dict[str, Any]] = None,
    ) -> ExecutionStage:
        """Route execution of a specific stage type to its appropriate subsystem runtime."""
        pass


class IExecutionTracker(ABC):
    """Interface for tracking execution progress, recording stages, timing, and statistics."""

    @abstractmethod
    def start_execution(self, context: ExecutionContext) -> str:
        """Record start of an execution context."""
        pass

    @abstractmethod
    def record_stage(self, execution_id: str, stage: ExecutionStage) -> None:
        """Record completed execution stage."""
        pass

    @abstractmethod
    def complete_execution(
        self,
        execution_id: str,
        result: ExecutionResult,
    ) -> ExecutionSummary:
        """Record completion of execution and generate ExecutionSummary."""
        pass

    @abstractmethod
    def get_statistics(self) -> ExecutionStatistics:
        """Return diagnostic statistics snapshot."""
        pass


class IExecutionOrchestrator(ABC):
    """Interface for master coordination across execution stages."""

    @abstractmethod
    def orchestrate(
        self,
        request_or_prompt: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """Coordinate multi-stage execution pipeline end-to-end."""
        pass


class IExecutionProvider(ABC):
    """Interface for the aggregate Command Execution Provider."""

    @abstractmethod
    def execute(
        self,
        request_or_prompt: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """Top-level entry point executing a request end-to-end."""
        pass

    @abstractmethod
    def health_check(self) -> ExecutionHealth:
        """Report overall health status of orchestrator components."""
        pass

    @abstractmethod
    def get_statistics(self) -> ExecutionStatistics:
        """Return snapshot of aggregated execution statistics."""
        pass


class IExecutionRuntime(ABC):
    """Interface for the thread-safe singleton lifecycle manager."""

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize orchestrator runtime lifecycle."""
        pass

    @abstractmethod
    def shutdown(self) -> bool:
        """Gracefully shut down orchestrator runtime lifecycle."""
        pass

    @abstractmethod
    def process_command(
        self,
        request_or_prompt: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """Process input command through the execution provider."""
        pass

    @abstractmethod
    def health_check(self) -> ExecutionHealth:
        """Fetch real-time health diagnostic status."""
        pass

    @abstractmethod
    def get_statistics(self) -> ExecutionStatistics:
        """Fetch snapshot of execution statistics."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Reset execution statistics and transient state."""
        pass
