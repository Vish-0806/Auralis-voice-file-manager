"""API Middleware Interfaces (Phase 15.3).

Defines Abstract Base Classes (ABCs) establishing design contracts for the Middleware
Registry, Pipeline Manager, Middleware Executor, Middleware Provider, and Middleware Runtime.
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple

from backend.application.api.middleware.models import (
    ApiMiddleware,
    MiddlewareCapabilities,
    MiddlewareContext,
    MiddlewareDiagnostics,
    MiddlewareHealth,
    MiddlewareResult,
    MiddlewareStage,
    MiddlewareStatistics,
)


class IMiddlewareRegistry(ABC):
    """Abstract interface for the API Middleware Registry."""

    @abstractmethod
    def register(self, middleware: ApiMiddleware) -> ApiMiddleware:
        """Register a new middleware component in the registry.

        Args:
            middleware: Immutable ApiMiddleware instance.

        Returns:
            ApiMiddleware: Registered middleware.

        Raises:
            DuplicateMiddlewareException: If middleware_id is already registered.
            MiddlewareRegistrationException: If registration fails.
        """
        raise NotImplementedError

    @abstractmethod
    def unregister(self, middleware_id: str) -> Optional[ApiMiddleware]:
        """Unregister a middleware component by ID.

        Args:
            middleware_id: Unique middleware identifier.

        Returns:
            Optional[ApiMiddleware]: Removed middleware if found, else None.
        """
        raise NotImplementedError

    @abstractmethod
    def enable(self, middleware_id: str) -> Optional[ApiMiddleware]:
        """Enable a registered middleware component.

        Args:
            middleware_id: Unique middleware identifier.

        Returns:
            Optional[ApiMiddleware]: Updated middleware if found, else None.
        """
        raise NotImplementedError

    @abstractmethod
    def disable(self, middleware_id: str) -> Optional[ApiMiddleware]:
        """Disable a registered middleware component.

        Args:
            middleware_id: Unique middleware identifier.

        Returns:
            Optional[ApiMiddleware]: Updated middleware if found, else None.
        """
        raise NotImplementedError

    @abstractmethod
    def contains(self, middleware_id: str) -> bool:
        """Check if a middleware ID is registered.

        Args:
            middleware_id: Unique middleware identifier.

        Returns:
            bool: True if present, False otherwise.
        """
        raise NotImplementedError

    @abstractmethod
    def lookup(self, middleware_id: str) -> Optional[ApiMiddleware]:
        """Look up a middleware by ID.

        Args:
            middleware_id: Unique middleware identifier.

        Returns:
            Optional[ApiMiddleware]: Middleware instance if found, else None.
        """
        raise NotImplementedError

    @abstractmethod
    def list_middlewares(
        self, stage: Optional[MiddlewareStage] = None
    ) -> Tuple[ApiMiddleware, ...]:
        """List registered middlewares, optionally filtered by stage and sorted by priority.

        Args:
            stage: Optional stage filter.

        Returns:
            Tuple[ApiMiddleware, ...]: Ordered tuple of matching middlewares.
        """
        raise NotImplementedError

    @abstractmethod
    def count(self) -> int:
        """Get total count of registered middlewares.

        Returns:
            int: Middleware count.
        """
        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        """Clear all registered middlewares from the registry."""
        raise NotImplementedError


class IPipelineManager(ABC):
    """Abstract interface for the Pipeline Manager."""

    @abstractmethod
    def build_before_pipeline(self) -> Tuple[ApiMiddleware, ...]:
        """Build priority-ordered pipeline for BEFORE_REQUEST stage.

        Returns:
            Tuple[ApiMiddleware, ...]: Pipeline sequence.
        """
        raise NotImplementedError

    @abstractmethod
    def build_around_pipeline(self) -> Tuple[ApiMiddleware, ...]:
        """Build priority-ordered pipeline for AROUND_REQUEST stage.

        Returns:
            Tuple[ApiMiddleware, ...]: Pipeline sequence.
        """
        raise NotImplementedError

    @abstractmethod
    def build_after_pipeline(self) -> Tuple[ApiMiddleware, ...]:
        """Build priority-ordered pipeline for AFTER_REQUEST stage.

        Returns:
            Tuple[ApiMiddleware, ...]: Pipeline sequence.
        """
        raise NotImplementedError

    @abstractmethod
    def build_error_pipeline(self) -> Tuple[ApiMiddleware, ...]:
        """Build priority-ordered pipeline for ERROR_HANDLER stage.

        Returns:
            Tuple[ApiMiddleware, ...]: Pipeline sequence.
        """
        raise NotImplementedError

    @abstractmethod
    def build_pipeline(self, stage: MiddlewareStage) -> Tuple[ApiMiddleware, ...]:
        """Build priority-ordered pipeline for a specific stage.

        Args:
            stage: Target MiddlewareStage.

        Returns:
            Tuple[ApiMiddleware, ...]: Pipeline sequence.
        """
        raise NotImplementedError


class IMiddlewareExecutor(ABC):
    """Abstract interface for the Middleware Executor engine."""

    @abstractmethod
    def execute_stage(
        self, stage: MiddlewareStage, context: MiddlewareContext
    ) -> MiddlewareResult:
        """Execute middleware pipeline for a given stage against context.

        Args:
            stage: Target MiddlewareStage.
            context: Immutable MiddlewareContext instance.

        Returns:
            MiddlewareResult: Result snapshot of the pipeline execution.

        Raises:
            MiddlewareExecutionException: If an execution error occurs.
        """
        raise NotImplementedError


class IMiddlewareProvider(ABC):
    """Abstract interface for the Middleware Provider."""

    @abstractmethod
    def initialize(self) -> MiddlewareHealth:
        """Initialize the middleware provider.

        Returns:
            MiddlewareHealth: Updated health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def shutdown(self) -> MiddlewareHealth:
        """Shutdown the middleware provider safely.

        Returns:
            MiddlewareHealth: Updated health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def restart(self) -> MiddlewareHealth:
        """Restart the middleware provider.

        Returns:
            MiddlewareHealth: Updated health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def health(self) -> MiddlewareHealth:
        """Get health evaluation snapshot.

        Returns:
            MiddlewareHealth: Health evaluation.
        """
        raise NotImplementedError

    @abstractmethod
    def statistics(self) -> MiddlewareStatistics:
        """Get aggregate statistics.

        Returns:
            MiddlewareStatistics: Statistics snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def capabilities(self) -> MiddlewareCapabilities:
        """Get declared capabilities.

        Returns:
            MiddlewareCapabilities: Capabilities snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def diagnostics(self) -> MiddlewareDiagnostics:
        """Get diagnostic telemetry snapshot.

        Returns:
            MiddlewareDiagnostics: Diagnostics snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def get_registry(self) -> IMiddlewareRegistry:
        """Get encapsulated middleware registry.

        Returns:
            IMiddlewareRegistry: Middleware registry.
        """
        raise NotImplementedError

    @abstractmethod
    def get_pipeline_manager(self) -> IPipelineManager:
        """Get encapsulated pipeline manager.

        Returns:
            IPipelineManager: Pipeline manager.
        """
        raise NotImplementedError

    @abstractmethod
    def get_executor(self) -> IMiddlewareExecutor:
        """Get encapsulated middleware executor.

        Returns:
            IMiddlewareExecutor: Middleware executor.
        """
        raise NotImplementedError


class IMiddlewareRuntime(ABC):
    """Abstract interface for the Middleware Runtime."""

    @abstractmethod
    def initialize(self) -> MiddlewareHealth:
        """Initialize the middleware runtime.

        Returns:
            MiddlewareHealth: Updated health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def shutdown(self) -> MiddlewareHealth:
        """Shutdown the middleware runtime safely.

        Returns:
            MiddlewareHealth: Updated health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def restart(self) -> MiddlewareHealth:
        """Restart the middleware runtime.

        Returns:
            MiddlewareHealth: Updated health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def health(self) -> MiddlewareHealth:
        """Get health evaluation snapshot.

        Returns:
            MiddlewareHealth: Health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def statistics(self) -> MiddlewareStatistics:
        """Get aggregate statistics.

        Returns:
            MiddlewareStatistics: Statistics snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def capabilities(self) -> MiddlewareCapabilities:
        """Get declared capabilities.

        Returns:
            MiddlewareCapabilities: Capabilities snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def diagnostics(self) -> MiddlewareDiagnostics:
        """Get diagnostic telemetry snapshot.

        Returns:
            MiddlewareDiagnostics: Diagnostics snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def get_provider(self) -> IMiddlewareProvider:
        """Get encapsulated middleware provider.

        Returns:
            IMiddlewareProvider: Middleware provider.
        """
        raise NotImplementedError
