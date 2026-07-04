"""Core interface contracts for Auralis.

This module defines the abstract boundaries for the assistant, planner,
dispatcher, and capability layers. It also retains the legacy interfaces used
by the current codebase so the package remains import-compatible during the
contract migration.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .models import AssistantRequest, AssistantResponse, ExecutionPlan, ExecutionResult, SessionContext


class IAssistant(ABC):
    """Defines the assistant orchestration contract."""

    @abstractmethod
    def process_request(
        self,
        request: AssistantRequest,
        context: SessionContext | None = None,
    ) -> AssistantResponse:
        """Processes a request and returns a structured response."""


class IPlanner(ABC):
    """Defines the contract for turning requests into execution plans."""

    @abstractmethod
    def create_plan(
        self,
        request: AssistantRequest,
        context: SessionContext | None = None,
    ) -> ExecutionPlan:
        """Builds an execution plan from the request and session context."""

    @abstractmethod
    def validate_plan(self, plan: ExecutionPlan) -> bool:
        """Validates that a plan is structurally ready for dispatch."""


class IDispatcher(ABC):
    """Defines the contract for executing a validated plan."""

    @abstractmethod
    def dispatch(
        self,
        plan: ExecutionPlan,
        context: SessionContext | None = None,
    ) -> ExecutionResult:
        """Executes a plan and returns an execution result."""


class ICapability(ABC):
    """Defines the contract for an executable capability."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the stable capability name."""

    @abstractmethod
    def execute(self, action: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Executes a capability action with the provided arguments."""


class IOSAdapter(ABC):
    """Legacy contract for OS abstraction adapters."""

    @abstractmethod
    def execute_shell(self, command: str) -> str:
        """Executes a shell command and returns stdout."""

    @abstractmethod
    def resolve_path(self, path: str) -> str:
        """Resolves a path into an absolute system path."""


class IMemoryEngine(ABC):
    """Legacy contract for memory storage integrations."""

    @abstractmethod
    def retrieve_context(self, query: str, limit: int) -> list[dict[str, Any]]:
        """Retrieves semantically similar context items."""

    @abstractmethod
    def save_context(self, item: dict[str, Any]) -> None:
        """Stores a context item."""


class IAgentBrain(ABC):
    """Legacy contract for reasoning and intent parsing."""

    @abstractmethod
    def reason(self, request: str, context: dict[str, Any]) -> dict[str, Any]:
        """Returns a structured reasoning payload for the request."""


__all__ = [
    "IAssistant",
    "IPlanner",
    "IDispatcher",
    "ICapability",
    "IOSAdapter",
    "IMemoryEngine",
    "IAgentBrain",
]
