"""API Integration Gateway Interfaces (Phase 15.9).

Defines Abstract Base Classes (ABCs) establishing design contracts for the API Gateway,
Request Coordinator, Response Coordinator, Integration Provider, and Integration Runtime.
"""

from abc import ABC, abstractmethod
from typing import Tuple

from backend.application.api.integration.models import (
    ApiIntegrationRequest,
    ApiIntegrationResponse,
    ApiPipelineStage,
    ApiRequestContext,
    ApiResponseContext,
    IntegrationCapabilities,
    IntegrationDiagnostics,
    IntegrationHealth,
    IntegrationStatistics,
    PipelineStage,
)


class IApiGateway(ABC):
    """Abstract interface for the API Gateway."""

    @abstractmethod
    def process_request(
        self, request: ApiIntegrationRequest
    ) -> ApiIntegrationResponse:
        """Process an incoming integration request through the gateway pipeline.

        Args:
            request: Immutable ApiIntegrationRequest instance.

        Returns:
            ApiIntegrationResponse: Resulting integration response model.
        """
        raise NotImplementedError

    @abstractmethod
    def list_pipeline_stages(self) -> Tuple[ApiPipelineStage, ...]:
        """List all configured pipeline stages in order.

        Returns:
            Tuple[ApiPipelineStage, ...]: Tuple of configured pipeline stages.
        """
        raise NotImplementedError

    @abstractmethod
    def get_gateway_statistics(self) -> IntegrationStatistics:
        """Get aggregate gateway execution statistics.

        Returns:
            IntegrationStatistics: Statistics model snapshot.
        """
        raise NotImplementedError


class IRequestCoordinator(ABC):
    """Abstract interface for the Request Coordinator."""

    @abstractmethod
    def coordinate_request(
        self, request: ApiIntegrationRequest
    ) -> ApiRequestContext:
        """Prepare and validate an immutable request context for gateway execution.

        Args:
            request: Immutable ApiIntegrationRequest instance.

        Returns:
            ApiRequestContext: Prepared request context model.

        Raises:
            RequestCoordinationException: If request metadata is invalid.
        """
        raise NotImplementedError

    @abstractmethod
    def validate_request_metadata(self, request: ApiIntegrationRequest) -> bool:
        """Validate metadata completeness of an incoming request.

        Args:
            request: Target request model.

        Returns:
            bool: True if metadata is valid, else False.
        """
        raise NotImplementedError


class IResponseCoordinator(ABC):
    """Abstract interface for the Response Coordinator."""

    @abstractmethod
    def coordinate_response(
        self, response: ApiIntegrationResponse, execution_time_ms: float = 0.0
    ) -> ApiResponseContext:
        """Encapsulate an integration response into an ApiResponseContext model.

        Args:
            response: Target ApiIntegrationResponse instance.
            execution_time_ms: Processing duration in milliseconds.

        Returns:
            ApiResponseContext: Prepared response context model.
        """
        raise NotImplementedError

    @abstractmethod
    def format_error_response(
        self,
        request_id: str,
        error_message: str,
        status_code: int = 500,
        stage: PipelineStage = PipelineStage.ROUTING,
    ) -> ApiIntegrationResponse:
        """Format an immutable error response model.

        Args:
            request_id: Associated request ID.
            error_message: Human-readable error description.
            status_code: HTTP status code (default 500).
            stage: PipelineStage where failure occurred.

        Returns:
            ApiIntegrationResponse: Formatted error response.
        """
        raise NotImplementedError


class IIntegrationProvider(ABC):
    """Abstract interface for the Integration Provider."""

    @abstractmethod
    def initialize(self) -> IntegrationHealth:
        """Initialize the integration provider.

        Returns:
            IntegrationHealth: Health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def shutdown(self) -> IntegrationHealth:
        """Shutdown the integration provider safely.

        Returns:
            IntegrationHealth: Health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def restart(self) -> IntegrationHealth:
        """Restart the integration provider.

        Returns:
            IntegrationHealth: Health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def health(self) -> IntegrationHealth:
        """Get health evaluation snapshot.

        Returns:
            IntegrationHealth: Health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def statistics(self) -> IntegrationStatistics:
        """Get aggregate statistics.

        Returns:
            IntegrationStatistics: Statistics snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def capabilities(self) -> IntegrationCapabilities:
        """Get declared capabilities.

        Returns:
            IntegrationCapabilities: Capabilities snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def diagnostics(self) -> IntegrationDiagnostics:
        """Get diagnostic telemetry.

        Returns:
            IntegrationDiagnostics: Diagnostics snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def get_api_gateway(self) -> IApiGateway:
        """Get encapsulated API gateway.

        Returns:
            IApiGateway: API gateway.
        """
        raise NotImplementedError

    @abstractmethod
    def get_request_coordinator(self) -> IRequestCoordinator:
        """Get encapsulated request coordinator.

        Returns:
            IRequestCoordinator: Request coordinator.
        """
        raise NotImplementedError

    @abstractmethod
    def get_response_coordinator(self) -> IResponseCoordinator:
        """Get encapsulated response coordinator.

        Returns:
            IResponseCoordinator: Response coordinator.
        """
        raise NotImplementedError


class IIntegrationRuntime(ABC):
    """Abstract interface for the Integration Runtime."""

    @abstractmethod
    def initialize(self) -> IntegrationHealth:
        """Initialize the integration runtime.

        Returns:
            IntegrationHealth: Health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def shutdown(self) -> IntegrationHealth:
        """Shutdown the integration runtime safely.

        Returns:
            IntegrationHealth: Health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def restart(self) -> IntegrationHealth:
        """Restart the integration runtime.

        Returns:
            IntegrationHealth: Health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def health(self) -> IntegrationHealth:
        """Get health evaluation snapshot.

        Returns:
            IntegrationHealth: Health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def statistics(self) -> IntegrationStatistics:
        """Get aggregate statistics.

        Returns:
            IntegrationStatistics: Statistics snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def capabilities(self) -> IntegrationCapabilities:
        """Get declared capabilities.

        Returns:
            IntegrationCapabilities: Capabilities snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def diagnostics(self) -> IntegrationDiagnostics:
        """Get diagnostic telemetry.

        Returns:
            IntegrationDiagnostics: Diagnostics snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def get_provider(self) -> IIntegrationProvider:
        """Get encapsulated integration provider.

        Returns:
            IIntegrationProvider: Integration provider.
        """
        raise NotImplementedError
