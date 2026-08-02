"""Abstract Base Class interfaces for the Auralis Workflow Execution Engine (Phase 12.4).

Defines canonical interfaces for builder, validator, scheduler, executor, provider, and runtime.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from brain.execution.workflow.workflow_models import (
    WorkflowContext,
    WorkflowExecution,
    WorkflowHealth,
    WorkflowRequest,
    WorkflowResult,
    WorkflowStatistics,
    WorkflowStep,
)


class IWorkflowBuilder(ABC):
    """Interface for building workflow graphs, step dependencies, and execution requests."""

    @abstractmethod
    def build_workflow(
        self,
        name: str,
        steps: List[WorkflowStep],
        context: Optional[Dict[str, Any]] = None,
    ) -> WorkflowRequest:
        """Construct a structured WorkflowRequest without execution logic."""
        pass


class IWorkflowValidator(ABC):
    """Interface for validating workflow graph integrity, cycle detection, and dependency correctness."""

    @abstractmethod
    def validate_workflow(self, request: WorkflowRequest) -> List[str]:
        """Validate workflow for duplicate IDs, cycles, missing steps, or empty graph."""
        pass


class IWorkflowScheduler(ABC):
    """Interface for topological sorting and scheduling workflow step execution order."""

    @abstractmethod
    def schedule(self, request: WorkflowRequest) -> WorkflowExecution:
        """Produce an executable WorkflowExecution schedule ordered by dependencies and priority."""
        pass


class IWorkflowExecutor(ABC):
    """Interface for executing scheduled workflow steps."""

    @abstractmethod
    def execute(
        self,
        execution: WorkflowExecution,
        request: WorkflowRequest,
        cancellation_token: Optional[Dict[str, bool]] = None,
    ) -> WorkflowResult:
        """Execute a scheduled workflow graph end-to-end."""
        pass


class IWorkflowProvider(ABC):
    """Interface for the aggregate Workflow Provider."""

    @abstractmethod
    def execute_workflow(
        self,
        request_or_steps: Any,
        context: Optional[Dict[str, Any]] = None,
        cancellation_token: Optional[Dict[str, bool]] = None,
    ) -> WorkflowResult:
        """Top-level entry point executing a workflow graph end-to-end."""
        pass

    @abstractmethod
    def health_check(self) -> WorkflowHealth:
        """Report overall health of workflow engine components."""
        pass

    @abstractmethod
    def get_statistics(self) -> WorkflowStatistics:
        """Return snapshot of aggregated workflow execution statistics."""
        pass


class IWorkflowRuntime(ABC):
    """Interface for the thread-safe singleton lifecycle manager."""

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize workflow runtime lifecycle."""
        pass

    @abstractmethod
    def shutdown(self) -> bool:
        """Gracefully shut down workflow runtime lifecycle."""
        pass

    @abstractmethod
    def process_workflow(
        self,
        request_or_steps: Any,
        context: Optional[Dict[str, Any]] = None,
        cancellation_token: Optional[Dict[str, bool]] = None,
    ) -> WorkflowResult:
        """Process workflow request through the provider."""
        pass

    @abstractmethod
    def health_check(self) -> WorkflowHealth:
        """Fetch real-time health diagnostic status."""
        pass

    @abstractmethod
    def get_statistics(self) -> WorkflowStatistics:
        """Fetch snapshot of workflow execution statistics."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Reset workflow execution statistics and transient state."""
        pass
