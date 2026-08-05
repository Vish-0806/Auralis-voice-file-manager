"""API Response Coordinator Implementation (Phase 15.9).

Thread-safe response coordinator encapsulating gateway execution metrics and formatting
structured error responses without transport serialization logic.
"""

from datetime import datetime, timezone
import logging
from threading import RLock
from typing import Dict
import uuid

from backend.application.api.integration.interfaces import IResponseCoordinator
from backend.application.api.integration.models import (
    ApiIntegrationResponse,
    ApiResponseContext,
    PipelineStage,
)

logger = logging.getLogger(__name__)


class ResponseCoordinator(IResponseCoordinator):
    """Thread-safe response coordinator structuring outgoing integration responses."""

    def __init__(self) -> None:
        """Initialize ResponseCoordinator using Constructor Dependency Injection."""
        self._lock = RLock()
        self._total_responses_coordinated = 0

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
        with self._lock:
            context_id = f"resctx_{uuid.uuid4().hex[:8]}"
            context = ApiResponseContext(
                context_id=context_id,
                response=response,
                execution_time_ms=execution_time_ms,
                diagnostics={
                    "status_code": response.status_code,
                    "stage_reached": response.stage_reached.value,
                    "request_id": response.request_id,
                },
            )
            self._total_responses_coordinated += 1
            logger.info("Coordinated response for request ID '%s' (status: %d).", response.request_id, response.status_code)
            return context

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
        with self._lock:
            response_id = f"res_err_{uuid.uuid4().hex[:8]}"
            logger.warning("Formatting error response for request ID '%s' at stage '%s': %s", request_id, stage.value, error_message)
            return ApiIntegrationResponse(
                response_id=response_id,
                request_id=request_id,
                status_code=status_code,
                headers={"Content-Type": "application/json"},
                body={"error": error_message, "stage": stage.value},
                stage_reached=stage,
                completed_at=datetime.now(timezone.utc),
            )

    def get_coordinator_telemetry(self) -> Dict[str, int]:
        """Get internal response coordinator telemetry counters under lock."""
        with self._lock:
            return {
                "total_responses_coordinated": self._total_responses_coordinated,
            }
